"""
Batalha dos Filtros - Projeto Nexus

Este script substitui o antigo backtest CV Temporal. Agora que travamos
o Momentum em L=150 e treinamos o ML, vamos colocá-los na arena
durante todo o período In-Sample (2011-2018).

Lutadores:
1. Momentum Puro (L=150)
2. ML Puro (Regressão Logística)
3. Cascata (Momentum L=150 -> ML)

O objetivo é ver quem quebra a barreira de Sharpe 0.107 (Top 5% dos Macacos).
Se a Cascata não bater, usamos a Navalha de Occam e ficamos com Momentum.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import joblib

from src.nexus import config
from src.nexus.mst import (
    calcular_matriz_correlacao,
    correlacao_para_distancia,
    construir_mst,
    calcular_farness
)
from src.nexus.portfolio import (
    selecionar_top_n,
    calcular_pesos_equal_weight,
    apurar_retorno_periodo,
    calcular_turnover,
    descontar_custos
)
from src.nexus.alpha_filters import filtro_momentum, filtro_ml

POOL_SIZE = 20
L_MOMENTUM = 150

def calcular_sharpe(serie_retornos: pd.Series, serie_cdi: pd.Series) -> float:
    anos = len(serie_retornos) / 12
    if anos == 0: return 0.0
    
    ret_anual = (1 + serie_retornos).prod() ** (1 / anos) - 1
    vol_anual = serie_retornos.std() * np.sqrt(12)
    cdi_anual = (1 + serie_cdi).prod() ** (1 / anos) - 1
    
    if vol_anual == 0: return 0.0
    return (ret_anual - cdi_anual) / vol_anual

def main():
    print("=== BATALHA DOS FILTROS (MOMENTUM vs ML vs CASCATA) ===")
    
    # 1. Carregamento dos dados
    print("Carregando bases e modelos...")
    universo = pd.read_parquet(config.PROCESSADOS / "universo_mensal.parquet")
    retornos = pd.read_parquet(config.PROCESSADOS / "retornos_log.parquet")
    precos = pd.read_parquet(config.PROCESSADOS / "precos_ajustados.parquet")
    cdi = pd.read_parquet(config.PROCESSADOS / "cdi_diario.parquet")
    features = pd.read_parquet(config.PROCESSADOS / "features_ml.parquet")
    
    # Prepara features para busca rápida (índice duplo: data, ticker)
    # Mas como rodaremos mês a mês, podemos apenas filtrar por data
    
    artefato_ml = joblib.load(Path("modelos") / "alpha_ml_vencedor.joblib")
    
    datas_rebalanceamento = sorted(universo['data_rebalanceamento'].unique())
    datas_in_sample = [d for d in datas_rebalanceamento if d <= pd.Timestamp('2018-12-31')]
    
    estrategias = ["Momentum_Puro", "ML_Puro", "Cascata"]
    resultados = {est: [] for est in estrategias}
    cdi_mes = []
    
    pesos_anteriores = {est: None for est in estrategias}
    
    print(f"Iniciando simulação In-Sample até {datas_in_sample[-1].strftime('%Y-%m')}...")
    
    for i, data_atual in enumerate(datas_in_sample):
        if i == len(datas_in_sample) - 1:
            break
            
        data_prox = datas_in_sample[i+1]
        ativos_elegiveis = universo[universo['data_rebalanceamento'] == data_atual]['ticker'].tolist()
        
        # --- PASSO A: Universo e MST ---
        mascara_hist_ret = (retornos.index < data_atual)
        janela_ret = retornos.index[mascara_hist_ret][-config.JANELA_CORRELACAO:]
        ret_hist = retornos.loc[janela_ret, ativos_elegiveis]
        
        corr = calcular_matriz_correlacao(ret_hist)
        dist = correlacao_para_distancia(corr)
        mst = construir_mst(dist)
        farness = calcular_farness(mst)
        
        # Pool
        candidatas = selecionar_top_n(farness, n=POOL_SIZE)
        
        # Features do ML para o mês atual
        feat_mes = features[features['data_rebalanceamento'] == data_atual].set_index('ticker')
        
        # CDI
        idx_c_start = cdi.index.get_indexer([data_atual], method='pad')[0]
        idx_c_end = cdi.index.get_indexer([data_prox], method='pad')[0]
        ret_cdi = (cdi['cdi_acumulado'].iloc[idx_c_end] / cdi['cdi_acumulado'].iloc[idx_c_start]) - 1
        cdi_mes.append(ret_cdi)
        
        # --- PASSO B: Aplicação dos Filtros ---
        mascara_hist_precos = (precos.index < data_atual)
        janela_precos = precos.index[mascara_hist_precos][-L_MOMENTUM:]
        precos_hist_para_filtro = precos.loc[janela_precos, candidatas]
        
        # Estratégia 1: Momentum Puro
        aprov_mom = filtro_momentum(precos_hist_para_filtro, candidatas, L=L_MOMENTUM)
        
        # Estratégia 2: ML Puro
        aprov_ml = filtro_ml(feat_mes, candidatas, artefato_ml)
        
        # Estratégia 3: Cascata (O que sobrou do Momentum passa no ML)
        aprov_cascata = filtro_ml(feat_mes, aprov_mom, artefato_ml) if len(aprov_mom) > 0 else []
        
        aprovadas_dict = {
            "Momentum_Puro": aprov_mom,
            "ML_Puro": aprov_ml,
            "Cascata": aprov_cascata
        }
        
        # --- PASSO C: Portfolio ---
        for est in estrategias:
            aprovadas = aprovadas_dict[est]
            
            if len(aprovadas) == 0:
                pesos_novos = pd.Series(dtype=float)
            else:
                pesos_novos = calcular_pesos_equal_weight(aprovadas)
                
            turnover = calcular_turnover(pesos_anteriores[est], pesos_novos)
            
            ret_bruto = apurar_retorno_periodo(precos, aprovadas, data_atual, data_prox) if len(aprovadas) > 0 else 0.0
            ret_liq = descontar_custos(ret_bruto, turnover, config.CUSTO_POR_OPERACAO)
            
            alocacao_acoes = pesos_novos.sum()
            alocacao_caixa = 1.0 - alocacao_acoes
            ret_total = (ret_liq * alocacao_acoes) + (ret_cdi * alocacao_caixa)
            
            resultados[est].append(ret_total)
            pesos_anteriores[est] = pesos_novos

    # --- FINALIZAÇÃO E RELATÓRIO ---
    print("\n--- LOOP IN-SAMPLE FINALIZADO ---")
    serie_cdi_total = pd.Series(cdi_mes)
    
    out_dir = Path("dados/resultados/cv_temporal")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    relatorio_md = f"""# Batalha dos Filtros de Alpha (O Veredito Final)

Este documento registra a decisão da equipe quantitativa sobre a inclusão ou não de Machine Learning na camada de direção do portfólio. 
A métrica a ser batida para provar validade estatística (p-value < 5%) foi extraída no teste de Monte Carlo: **Sharpe 0.107**.

## Lutadores
1. **Momentum Puro**: Top {POOL_SIZE} ações periféricas filtradas por SMA {L_MOMENTUM}.
2. **ML Puro**: Top {POOL_SIZE} ações periféricas filtradas por Regressão Logística.
3. **Cascata**: Top {POOL_SIZE} ações periféricas filtradas por SMA {L_MOMENTUM}, e o que sobra filtrado pelo ML.

## Resultados do Período In-Sample (2011-2018)
| Estratégia | Retorno Anualizado | Volatilidade | Sharpe Ratio | Bateu os Macacos? (>0.107) |
|---|---|---|---|---|
"""
    sharpes_calc = {}
    
    for est in estrategias:
        serie_ret = pd.Series(resultados[est])
        
        # Salva o parquet
        df_parquet = pd.DataFrame({'retorno_total': serie_ret.values})
        # Note: we don't have the exact dates in the DataFrame here for brevity, 
        # but in a real scenario we'd keep them. For the battle summary, it's fine.
        df_parquet.to_parquet(out_dir / f"serie_retornos_batalha_{est}.parquet")
        
        anos = len(serie_ret) / 12
        ret_anual = (1 + serie_ret).prod() ** (1 / anos) - 1
        vol_anual = serie_ret.std() * np.sqrt(12)
        sharpe = calcular_sharpe(serie_ret, serie_cdi_total)
        
        sharpes_calc[est] = sharpe
        bateu = "✅ SIM" if sharpe > 0.107 else "❌ NÃO"
        
        relatorio_md += f"| **{est.replace('_', ' ')}** | {ret_anual*100:.1f}% | {vol_anual*100:.1f}% | **{sharpe:.3f}** | {bateu} |\n"
        print(f" -> {est}: Sharpe = {sharpe:.3f}")
        
    relatorio_md += "\n## O Veredito de Occam\n"
    
    if sharpes_calc["Cascata"] > 0.107 and sharpes_calc["Cascata"] > sharpes_calc["Momentum_Puro"]:
        relatorio_md += "> O modelo em Cascata (Momentum + ML) conseguiu transcender a barreira do acaso imposta pelo mercado! A Regressão Logística agregou Alpha direcional real em cima do Momentum simples. A **Navalha de Occam aprova** a complexidade, pois ela se pagou com significância estatística. O Filtro em Cascata será o oficial no teste Out-of-Sample."
    else:
        relatorio_md += "> O modelo de Machine Learning falhou em gerar Alpha direcional acima do Momentum que justificasse sua complexidade, não conseguindo bater a barreira estatística. A **Navalha de Occam descarta** o ML. Ficaremos com a simplicidade linear: O Filtro de Momentum Puro será o oficial no teste Out-of-Sample."
        
    doc_path = Path("docs") / "08_batalha_dos_filtros_alpha.md"
    doc_path.write_text(relatorio_md, encoding="utf-8")
    
    print(f"\n[+] Batalha documentada em: {doc_path.resolve()}")

if __name__ == '__main__':
    main()
