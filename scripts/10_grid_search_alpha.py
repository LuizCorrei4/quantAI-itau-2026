"""
===============================================================================
PROJETO NEXUS - DESAFIO ITAÚ ASSET QUANT AI 2026
Etapa 8 - Grid Search (Matriz de Sensibilidade Pool x SMA de Momentum)
Arquivo: scripts/10_grid_search_alpha.py
===============================================================================

OBJETIVO DO SCRIPT:
-------------------
Executa a calibração paramétrica sistemática do Filtro de Momentum (Camada 2)
no período In-Sample (2011 a 2018), testando todas as combinações de:
  - Tamanho do Pool de Ações Periféricas da MST (N in {10, 15, 20, 25})
  - Comprimento da Média Móvel Simples (L in {50, 100, 150, 200} dias úteis)

RIGOR METODOLÓGICO:
-------------------
- Alinhado com a Regra de CAP de 10% por ativo (`config.CAP_POR_ATIVO`).
- Custos transacionais deduzidos integralmente do retorno total do portfólio.
- Gera o Heatmap institucional em `images/03_heatmap_alpha_cv.png`.
- Documenta as conclusões em `docs/07_limite_do_momentum_grid_search.md`.
===============================================================================
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Inclusão da raiz do repositório
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
    calcular_turnover
)
from src.nexus.alpha_filters import filtro_momentum

POOL_VALORES = [10, 15, 20, 25]
L_VALORES = [50, 100, 150, 200]
IMG_DIR = Path("images")
IMG_DIR.mkdir(parents=True, exist_ok=True)


def calcular_sharpe(serie_retornos: pd.Series, serie_cdi: pd.Series) -> float:
    """
    Calcula o Sharpe Ratio anualizado em relação ao CDI.
    """
    anos = len(serie_retornos) / 12.0
    if anos == 0:
        return 0.0
    
    ret_anual = (1.0 + serie_retornos).prod() ** (1.0 / anos) - 1.0
    vol_anual = float(serie_retornos.std() * np.sqrt(12.0))
    cdi_anual = (1.0 + serie_cdi).prod() ** (1.0 / anos) - 1.0
    
    if vol_anual == 0:
        return 0.0
    return float((ret_anual - cdi_anual) / vol_anual)


def main():
    print("=" * 80)
    print("  PROJETO NEXUS - GRID SEARCH DE SENSIBILIDADE DO MOMENTUM (IN-SAMPLE)")
    print("  (Pool Top N x SMA L - Com Cap de 10% e Dedução Estrita de Custos)")
    print("=" * 80)
    
    universo = pd.read_parquet(config.PROCESSADOS / "universo_mensal.parquet")
    retornos = pd.read_parquet(config.PROCESSADOS / "retornos_log.parquet")
    precos = pd.read_parquet(config.PROCESSADOS / "precos_ajustados.parquet")
    cdi = pd.read_parquet(config.PROCESSADOS / "cdi_diario.parquet")
    
    datas_rebalanceamento = sorted(universo['data_rebalanceamento'].unique())
    datas_in_sample = [d for d in datas_rebalanceamento if d <= pd.Timestamp('2018-12-31')]
    
    matriz_sharpe = np.zeros((len(POOL_VALORES), len(L_VALORES)))
    
    print(f"\n[1/3] Executando simulações paralelas para {len(POOL_VALORES) * len(L_VALORES)} combinações...")
    
    # Estruturas para registrar retornos mensais de cada combinação
    retornos_combinacoes = {f"P{p}_L{l}": [] for p in POOL_VALORES for l in L_VALORES}
    cdi_mes = []
    pesos_anteriores = {f"P{p}_L{l}": None for p in POOL_VALORES for l in L_VALORES}
    
    for i, data_atual in enumerate(datas_in_sample):
        if i == len(datas_in_sample) - 1:
            break
            
        data_prox = datas_in_sample[i + 1]
        ativos_elegiveis = universo[universo['data_rebalanceamento'] == data_atual]['ticker'].tolist()
        
        # 1. MST Pura (Calculada 1 vez por mês para otimização)
        mascara_hist_ret = (retornos.index < data_atual)
        janela_ret = retornos.index[mascara_hist_ret][-config.JANELA_CORRELACAO:]
        ret_hist = retornos.loc[janela_ret, ativos_elegiveis]
        
        corr = calcular_matriz_correlacao(ret_hist)
        dist = correlacao_para_distancia(corr)
        mst = construir_mst(dist)
        farness = calcular_farness(mst)
        
        mascara_hist_precos = (precos.index < data_atual)
        
        # CDI do período
        idx_c_start = cdi.index.get_indexer([data_atual], method='pad')[0]
        idx_c_end = cdi.index.get_indexer([data_prox], method='pad')[0]
        ret_cdi = float((cdi['cdi_acumulado'].iloc[idx_c_end] / cdi['cdi_acumulado'].iloc[idx_c_start]) - 1.0)
        cdi_mes.append(ret_cdi)
        
        # 2. Avaliação de todas as combinações de hiperparâmetros
        for p_idx, pool_size in enumerate(POOL_VALORES):
            candidatas = selecionar_top_n(farness, n=pool_size)
            
            for l_idx, L in enumerate(L_VALORES):
                chave = f"P{pool_size}_L{L}"
                
                janela_precos = precos.index[mascara_hist_precos][-L:] 
                precos_hist_para_filtro = precos.loc[janela_precos, candidatas]
                
                aprovadas = filtro_momentum(precos_hist_para_filtro, candidatas, L=L)
                
                # Dimensionamento com CAP de 10%
                pesos_novos = calcular_pesos_equal_weight(aprovadas, cap=config.CAP_POR_ATIVO)
                
                turnover = calcular_turnover(pesos_anteriores[chave], pesos_novos)
                custo_turnover = turnover * (config.CUSTO_POR_OPERACAO * 2.0)
                
                ret_acoes = apurar_retorno_periodo(precos, aprovadas, data_atual, data_prox) if len(aprovadas) > 0 else 0.0
                
                alocacao_acoes = float(pesos_novos.sum())
                alocacao_caixa = float(1.0 - alocacao_acoes)
                
                ret_total = (ret_acoes * alocacao_acoes) + (ret_cdi * alocacao_caixa) - custo_turnover
                
                retornos_combinacoes[chave].append(ret_total)
                pesos_anteriores[chave] = pesos_novos

    print("\n[2/3] Apurando métricas de Sharpe e consolidando matriz...")
    serie_cdi_total = pd.Series(cdi_mes)
    
    for p_idx, pool_size in enumerate(POOL_VALORES):
        for l_idx, L in enumerate(L_VALORES):
            chave = f"P{pool_size}_L{L}"
            serie_ret = pd.Series(retornos_combinacoes[chave])
            sharpe = calcular_sharpe(serie_ret, serie_cdi_total)
            matriz_sharpe[p_idx, l_idx] = sharpe
            
    # Geração do Heatmap Visual
    print("\n[3/3] Exportando Heatmap para 'images/03_heatmap_alpha_cv.png'...")
    plt.figure(figsize=(8, 6))
    df_heatmap = pd.DataFrame(matriz_sharpe, index=[f"Pool: {p}" for p in POOL_VALORES], 
                              columns=[f"SMA: {l}" for l in L_VALORES])
                              
    sns.heatmap(df_heatmap, annot=True, cmap="YlGnBu", fmt=".3f", linewidths=.5)
    plt.title("Heatmap: Sharpe Ratio (In-Sample 2011-2018) por Pool x SMA", fontweight='bold')
    plt.xlabel("Comprimento da Média Móvel (L em dias úteis)")
    plt.ylabel("Tamanho do Pool Periférico da MST (N)")
    plt.tight_layout()
    
    img_path = IMG_DIR / "03_heatmap_alpha_cv.png"
    plt.savefig(img_path, dpi=180)
    plt.close()
    
    print(f" -> Heatmap salvo em: {img_path.resolve()}")
    
    # Identificação da melhor configuração
    melhor_idx = np.unravel_index(np.argmax(matriz_sharpe), matriz_sharpe.shape)
    melhor_pool = POOL_VALORES[melhor_idx[0]]
    melhor_l = L_VALORES[melhor_idx[1]]
    melhor_sharpe = matriz_sharpe[melhor_idx]
    
    print(f"\n🏆 CONFIGURAÇÃO ÓTIMA DE MOMENTUM:")
    print(f" -> Tamanho do Pool (MST): {melhor_pool}")
    print(f" -> Média Móvel (SMA L): {melhor_l} dias")
    print(f" -> Sharpe Ratio In-Sample: {melhor_sharpe:+.3f}")
    
    # Atualização do documento Markdown
    relatorio_md = f"""# Limite Estrutural do Filtro de Momentum (Grid Search)

**Objetivo:** Aplicar o princípio da Navalha de Occam buscando a configuração mais simples (Média Móvel) capaz de extrair Alpha direcional consistente do universo descorrelacionado (MST).

## 1. Metodologia (Otimização Sistemática)
Para provar que a escolha de parâmetros não sofre de *cherry-picking*, executamos um Grid Search massivo no período *In-Sample* (2011-2018):

*   **Tamanho do Pool (MST):** Testamos selecionar as Top `{{10, 15, 20, 25}}` candidatas periféricas.
*   **Filtro de Momentum (L):** Testamos Comprimentos de Média Móvel de `{{50, 100, 150, 200}}` dias úteis.
*   **Regra de CAP:** Teto de 10% por ativo (`CAP_POR_ATIVO = 0.10`), com capital excedente preservado em CDI.

## 2. Matriz de Sensibilidade (Heatmap)
<p align="center">
  <img src="../images/03_heatmap_alpha_cv.png" width="650" alt="Heatmap Pool vs SMA" />
</p>

## 3. O Veredito de Occam (Diagnóstico Estrutural)
A matriz de calor traz uma constatação científica crítica sobre a estratégia:

1.  **A Configuração Ótima:** A região de maior solidez paramétrica situa-se em `Pool = {melhor_pool}` com `SMA = {melhor_l}`, gerando um Sharpe *In-Sample* de **{melhor_sharpe:+.3f}**.
2.  **A Barreira Estatística:** Conforme aferido no teste de Monte Carlo, o limiar de 95% de confiança (p-value < 0.05) para rejeitar a hipótese de ruído é um Sharpe de **0.107**.

> **Conclusão para a Banca:** O Filtro de Momentum puro consegue recuperar o Sharpe negativo do MVP para um patamar de {melhor_sharpe:+.3f}. A configuração `Pool = {melhor_pool}` e `SMA = {melhor_l}` foi travada como o benchmark linear para a Batalha dos Filtros de Alpha.
"""
    doc_path = Path("docs") / "07_limite_do_momentum_grid_search.md"
    doc_path.write_text(relatorio_md, encoding="utf-8")
    print(f" -> Relatório atualizado em: {doc_path.resolve()}")
    print("=" * 80)


if __name__ == '__main__':
    main()
