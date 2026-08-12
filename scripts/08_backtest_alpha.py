"""
Backtest com Filtros de Alpha e Validação Cruzada Temporal (CV Temporal)

Este orquestrador (criado a partir do 07_backtest.py) foca em:
Injetar a convicção direcional (Momentum) sobre as ações descorrelacionadas (MST)
e medir o impacto usando Validação Cruzada Temporal dentro do período In-Sample.

O objetivo principal aqui NÃO é achar o melhor Sharpe para o período inteiro,
mas sim encontrar a configuração (o valor de L) que seja mais ESTÁVEL entre
os 3 folds temporais, provando que o resultado não é overfitting.
"""

import sys
from pathlib import Path

# Garante que os módulos internos do src/nexus possam ser importados 
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
from src.nexus.alpha_filters import filtro_momentum

# --- Configurações do Experimento (Missão 2) ---
POOL_SIZE = 20 # Expandimos o universo periférico (era Top 10 no MVP, agora 20 candidatas)
L_VALORES = [50, 100, 150, 200] # Testaremos esses 4 comprimentos de média móvel

# Definição rigorosa dos Folds (períodos de validação em que vamos medir o Sharpe)
FOLDS = {
    'Fold_1': {'inicio': '2015-01-01', 'fim': '2016-12-31'},
    'Fold_2': {'inicio': '2016-01-01', 'fim': '2017-12-31'},
    'Fold_3': {'inicio': '2017-01-01', 'fim': '2018-12-31'},
}

def classificar_fold(data: pd.Timestamp) -> str:
    """Retorna a qual fold a data pertence, ou None se estiver fora."""
    # Como as datas são sobrepostas, uma mesma data pode pertencer a múltiplos folds.
    # Mas para simplificar o log e o agrupamento depois, faremos o agrupamento a posteriori
    # usando pandas nas datas salvas.
    pass

def main():
    print("=== BACKTEST COM VALIDAÇÃO CRUZADA TEMPORAL (MOMENTUM) ===")
    
    # 1. Carregamento dos dados
    print("Carregando bases de dados...")
    universo = pd.read_parquet(config.PROCESSADOS / "universo_mensal.parquet")
    retornos = pd.read_parquet(config.PROCESSADOS / "retornos_log.parquet")
    precos = pd.read_parquet(config.PROCESSADOS / "precos_ajustados.parquet")
    cdi = pd.read_parquet(config.PROCESSADOS / "cdi_diario.parquet")
    
    datas_rebalanceamento = sorted(universo['data_rebalanceamento'].unique())
    
    # Limitamos o loop para ir apenas até Dez/2018 (Fim do In-Sample)
    datas_in_sample = [d for d in datas_rebalanceamento if d <= pd.Timestamp('2018-12-31')]
    
    # Estruturas para guardar os resultados de CADA variante de L
    # Ex: resultados['L_50'] = [{'data': X, 'retorno_liq': Y}, ...]
    resultados_por_variante = {f"L_{L}": [] for L in L_VALORES}
    
    # Controlamos os pesos_anteriores de forma isolada para calcular turnover corretamente
    pesos_anteriores_variante = {f"L_{L}": None for L in L_VALORES}
    
    print(f"Iniciando loop In-Sample (até {datas_in_sample[-1].strftime('%Y-%m')})...")
    
    for i, data_atual in enumerate(datas_in_sample):
        # Como precisamos avaliar o retorno do mês, paramos 1 mês antes do fim da lista
        if i == len(datas_in_sample) - 1:
            break
            
        data_prox = datas_in_sample[i+1]
        
        # --- PASSO A: O Filtro de Universo (MST e Farness) ---
        ativos_elegiveis = universo[universo['data_rebalanceamento'] == data_atual]['ticker'].tolist()
        
        # Janela para correlação (Trailing 63 dias)
        mascara_hist_ret = (retornos.index < data_atual)
        janela_ret = retornos.index[mascara_hist_ret][-config.JANELA_CORRELACAO:]
        ret_hist = retornos.loc[janela_ret, ativos_elegiveis]
        
        # Constrói o Grafo e acha as ações periféricas (Farness)
        corr = calcular_matriz_correlacao(ret_hist)
        dist = correlacao_para_distancia(corr)
        mst = construir_mst(dist)
        farness = calcular_farness(mst)
        
        # Pega as Top N candidatas da MST (O "Pool" descorrelacionado)
        candidatas = selecionar_top_n(farness, n=POOL_SIZE)
        
        # --- PASSO B: O Filtro de Alpha (Momentum) ---
        # A Média Móvel exige os preços do passado, no máximo até T-1.
        mascara_hist_precos = (precos.index < data_atual)
        
        # Para cada valor de L que queremos testar...
        for L in L_VALORES:
            variante = f"L_{L}"
            
            # Pegamos um histórico de preços que tenha pelo menos L dias antes de T
            janela_precos = precos.index[mascara_hist_precos][-L:] 
            precos_hist_para_filtro = precos.loc[janela_precos, candidatas]
            
            # Aplicamos o nosso módulo que acabamos de criar!
            aprovadas = filtro_momentum(precos_hist_para_filtro, candidatas, L=L)
            
            # --- PASSO C: O Portfolio Mensal ---
            # Se ninguém passar no Momentum, todo o dinheiro vai pro CDI.
            if len(aprovadas) == 0:
                pesos_novos = pd.Series(dtype=float) # Vazio = 100% CDI
            else:
                pesos_novos = calcular_pesos_equal_weight(aprovadas)
            
            turnover = calcular_turnover(pesos_anteriores_variante[variante], pesos_novos)
            
            # Calculamos o Retorno Bruto apenas das ações
            if len(aprovadas) > 0:
                ret_bruto = apurar_retorno_periodo(precos, aprovadas, data_atual, data_prox)
            else:
                ret_bruto = 0.0 # Sem ações na carteira
                
            ret_liq = descontar_custos(ret_bruto, turnover, config.CUSTO_POR_OPERACAO)
            
            # CDI correspondente no período
            idx_c_start = cdi.index.get_indexer([data_atual], method='pad')[0]
            idx_c_end = cdi.index.get_indexer([data_prox], method='pad')[0]
            ret_cdi = (cdi['cdi_acumulado'].iloc[idx_c_end] / cdi['cdi_acumulado'].iloc[idx_c_start]) - 1
            
            # Efeito Caixa: a grana que NÃO está nas ações aprovadas, rende CDI.
            alocacao_acoes = pesos_novos.sum() # Será 1.0 se houver aprovadas, 0.0 se não houver
            alocacao_caixa = 1.0 - alocacao_acoes
            
            retorno_carteira_total = (ret_liq * alocacao_acoes) + (ret_cdi * alocacao_caixa)
            
            # Salva o resultado mensal para esta variante
            resultados_por_variante[variante].append({
                'data_rebalanceamento': data_atual,
                'retorno_carteira_total': retorno_carteira_total,
                'retorno_cdi': ret_cdi,
                'qtd_aprovadas': len(aprovadas)
            })
            
            pesos_anteriores_variante[variante] = pesos_novos
            
    print("\n--- LOOP IN-SAMPLE FINALIZADO ---")
    
    # 2. Consolidação e Apuração do Sharpe nos Folds de Validação (O Teste de Fogo)
    print("Avaliando o Sharpe nas Validações Cruzadas Temporais...")
    
    # Prepara o diretório de saída conforme Missão 3 (Armazenamento Semântico)
    out_dir = Path("dados/resultados/cv_temporal")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    docs_dir = Path("docs")
    relatorio_md = f"# Calibração CV Temporal - Momentum (Pool = {POOL_SIZE})\n\n"
    relatorio_md += "Este teste aplica o Filtro de Momentum em diferentes tamanhos de Média Móvel (L) e mede a **estabilidade** do Sharpe Ratio em 3 períodos distintos.\n\n"
    relatorio_md += "| Variante | Sharpe (Fold 1: 15-16) | Sharpe (Fold 2: 16-17) | Sharpe (Fold 3: 17-18) | Sharpe In-Sample Total |\n"
    relatorio_md += "|---|---|---|---|---|\n"
    
    for L in L_VALORES:
        variante = f"L_{L}"
        df_res = pd.DataFrame(resultados_por_variante[variante]).set_index('data_rebalanceamento')
        
        # Salva a série cronológica completa do In-Sample em Parquet para a arquitetura
        df_res.to_parquet(out_dir / f"serie_retornos_momentum_{variante}_Pool{POOL_SIZE}.parquet")
        
        # Helpers de cálculo
        sharpes_folds = []
        for nome_fold, dict_datas in FOLDS.items():
            # Filtra a série pelo período do Fold (Ex: 2015-01-01 a 2016-12-31)
            mascara_fold = (df_res.index >= dict_datas['inicio']) & (df_res.index <= dict_datas['fim'])
            df_fold = df_res[mascara_fold]
            
            # Anualização baseada em 12 meses
            anos_fold = len(df_fold) / 12
            if anos_fold == 0:
                sharpes_folds.append(0.0)
                continue
                
            ret_anual = (1 + df_fold['retorno_carteira_total']).prod() ** (1 / anos_fold) - 1
            vol_anual = df_fold['retorno_carteira_total'].std() * np.sqrt(12)
            
            cdi_anual = (1 + df_fold['retorno_cdi']).prod() ** (1 / anos_fold) - 1
            
            sharpe = (ret_anual - cdi_anual) / vol_anual if vol_anual > 0 else 0
            sharpes_folds.append(sharpe)
            
        # Calcula Sharpe In-Sample Total (2011-2018)
        anos_total = len(df_res) / 12
        ret_anual_total = (1 + df_res['retorno_carteira_total']).prod() ** (1 / anos_total) - 1
        vol_anual_total = df_res['retorno_carteira_total'].std() * np.sqrt(12)
        cdi_anual_total = (1 + df_res['retorno_cdi']).prod() ** (1 / anos_total) - 1
        sharpe_total = (ret_anual_total - cdi_anual_total) / vol_anual_total if vol_anual_total > 0 else 0
        
        # Adiciona a linha na tabela Markdown
        relatorio_md += f"| **L = {L}** | {sharpes_folds[0]:.2f} | {sharpes_folds[1]:.2f} | {sharpes_folds[2]:.2f} | **{sharpe_total:.2f}** |\n"
    
    # 3. Salva a Tabela de Decisão em docs/
    doc_path = docs_dir / "05_calibracao_momentum_cv.md"
    doc_path.write_text(relatorio_md, encoding="utf-8")
    
    print(f"\n[+] Relatório de Calibração salvo em: {doc_path.resolve()}")
    print("Execute `cat docs/05_calibracao_momentum_cv.md` para ver qual L é o mais ESTÁVEL!")

if __name__ == '__main__':
    main()
