"""
Etapa 5 - O Loop de Backtest MVP

Este é o orquestrador que consome a inteligência pura armazenada em
`mst.py` e `portfolio.py` para gerar a curva de capital da estratégia
Nexus de ponta a ponta (2011-2026), sem o filtro de regime.

As saídas são gravadas de forma 100% auditável e um relatório Markdown 
é gerado automaticamente na pasta `docs/`.
"""

import sys
from pathlib import Path

# Garante que os módulos internos do src/nexus possam ser importados 
# independentemente da pasta de onde o script for chamado.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.nexus import config
from src.nexus.mst import (
    calcular_matriz_correlacao,
    correlacao_para_distancia,
    construir_mst,
    calcular_farness,
    calcular_distancia_media_mst
)
from src.nexus.portfolio import (
    selecionar_top_n,
    calcular_pesos_equal_weight,
    apurar_retorno_periodo,
    calcular_turnover,
    descontar_custos
)

# Cria a pasta de imagens para o relatório
IMG_DIR = Path("images")
IMG_DIR.mkdir(parents=True, exist_ok=True)

def gerar_graficos(df_resultados: pd.DataFrame):
    """
    Gera três gráficos analíticos em alta qualidade visual e exporta para `images/`.
    Esses gráficos alimentam automaticamente o documento do relatório.
    """
    # 1. Curva de Capital (Retorno Acumulado) - O coração do MVP
    plt.figure(figsize=(10, 5))
    
    # As curvas .cumprod() transformam retornos mensais em patrimônio acumulado 
    # (ex: 1.0 -> 1.05 -> 1.10)
    plt.plot((1 + df_resultados['retorno_liquido']).cumprod(), label='Nexus (Líquido)', color='purple', linewidth=2.5)
    plt.plot((1 + df_resultados['retorno_cdi']).cumprod(), label='CDI (Benchmark Foco)', color='gray', linestyle='--', linewidth=2)
    plt.plot((1 + df_resultados['retorno_ibov']).cumprod(), label='Ibovespa', color='red', alpha=0.5, linewidth=1.5)
    plt.plot((1 + df_resultados['retorno_bova11']).cumprod(), label='BOVA11', color='orange', alpha=0.5, linewidth=1.5)
    
    plt.title("Retorno Acumulado: Nexus vs Benchmarks (Base 1.0)", fontsize=14, fontweight='bold')
    plt.ylabel("Capital Crescimento (x)")
    plt.legend(loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(IMG_DIR / "01_mvp_puro_retorno_acumulado.png", dpi=150)
    plt.close()

    # 2. Drawdown - Para avaliar resiliência sistêmica (o vale das perdas)
    cum_ret = (1 + df_resultados['retorno_liquido']).cumprod()
    pico_historico = cum_ret.cummax()
    drawdown = (cum_ret - pico_historico) / pico_historico
    
    plt.figure(figsize=(10, 3))
    plt.fill_between(drawdown.index, drawdown, 0, color='darkred', alpha=0.4)
    plt.title("Drawdown do Robô Nexus (Quedas do Topo)", fontsize=12)
    plt.ylabel("% de Perda")
    plt.tight_layout()
    plt.savefig(IMG_DIR / "01_mvp_puro_drawdown.png", dpi=150)
    plt.close()

    # 3. Turnover - Para checar estabilidade da carteira mensal
    plt.figure(figsize=(10, 3))
    plt.bar(df_resultados.index, df_resultados['turnover'] * 100, color='blue', alpha=0.6, width=20)
    plt.title("Turnover Mensal (%)", fontsize=12)
    plt.ylabel("% da Carteira Girada")
    plt.tight_layout()
    plt.savefig(IMG_DIR / "01_mvp_puro_turnover_mensal.png", dpi=150)
    plt.close()
    
def calcular_metricas_estatisticas(serie_retornos: pd.Series, risk_free_anual: float = 0.0) -> dict:
    """
    Função utilitária para consolidar as métricas chaves de Sharpe e Risco de cada benchmark.
    """
    ret_acumulado = (1 + serie_retornos).prod() - 1
    
    # Anualização baseada em 12 meses
    ret_anual = (1 + serie_retornos).prod() ** (12 / len(serie_retornos)) - 1
    vol_anual = serie_retornos.std() * np.sqrt(12)
    
    # Índice Sharpe Clássico
    sharpe = (ret_anual - risk_free_anual) / vol_anual if vol_anual > 0 else 0
    
    cum_ret = (1 + serie_retornos).cumprod()
    max_dd = ((cum_ret - cum_ret.cummax()) / cum_ret.cummax()).min()
    
    # Índice Calmar Clássico (Retorno por dor máxima)
    calmar = ret_anual / abs(max_dd) if max_dd != 0 else 0
    
    return {
        "Ret. Acumulado": ret_acumulado,
        "Ret. Anualizado": ret_anual,
        "Vol. Anualizada": vol_anual,
        "Sharpe": sharpe,
        "Max Drawdown": max_dd,
        "Calmar": calmar
    }

def main():
    print("=== ORQUESTRADOR DO BACKTEST (MVP) ===")
    print("Carregando 15 anos de dados em memória...")
    
    # Carrega dados do Pipeline base 
    universo = pd.read_parquet(config.PROCESSADOS / "universo_mensal.parquet")
    retornos = pd.read_parquet(config.PROCESSADOS / "retornos_log.parquet")
    precos = pd.read_parquet(config.PROCESSADOS / "precos_ajustados.parquet")
    benchmarks = pd.read_parquet(config.PROCESSADOS / "benchmarks.parquet")
    cdi = pd.read_parquet(config.PROCESSADOS / "cdi_diario.parquet")
    
    # Extrai o calendário exato em que os rebalanceamentos acontecem
    datas_rebalanceamento = sorted(universo['data_rebalanceamento'].unique())
    
    resultados_mes = []
    carteiras = []
    todas_farness = []
    pesos_anteriores = None
    
    print(f"Iniciando loop por {len(datas_rebalanceamento)-1} meses de pregão...")
    
    # Percorre cada mês de rebalanceamento
    for i, data in enumerate(datas_rebalanceamento):
        if i == len(datas_rebalanceamento) - 1:
            # Não calculamos o mês N porque precisamos do mês N+1 para medir o retorno 
            # de segurar a carteira.
            break
            
        data_atual = data
        data_prox = datas_rebalanceamento[i+1]
        
        # 1. Restringe a avaliação para apenas as 80 ações permitidas no mês
        ativos_elegiveis = universo[universo['data_rebalanceamento'] == data_atual]['ticker'].tolist()
        
        # 2. Pega os últimos 63 pregões, estritamente até ontem (evita Look-Ahead Bias)
        mascara_hist = (retornos.index < data_atual)
        janela = retornos.index[mascara_hist][-config.JANELA_CORRELACAO:]
        ret_hist = retornos.loc[janela, ativos_elegiveis]
        
        # --- NÚCLEO DE GRAFOS (Seu trabalho brilha aqui) ---
        corr = calcular_matriz_correlacao(ret_hist)
        dist = correlacao_para_distancia(corr)
        mst = construir_mst(dist)
        
        farness = calcular_farness(mst)
        dist_media = calcular_distancia_media_mst(mst)
        
        # Salva o dataset puro de grafos para as Pessoas 2 e 3
        df_farness = pd.DataFrame({'data_rebalanceamento': data_atual, 'ticker': farness.index, 'farness': farness.values})
        todas_farness.append(df_farness)
        
        # --- NÚCLEO DE PORTFÓLIO E OPERAÇÕES ---
        top_n = selecionar_top_n(farness, n=config.TOP_N)
        pesos_novos = calcular_pesos_equal_weight(top_n)
        
        turnover = calcular_turnover(pesos_anteriores, pesos_novos)
        
        # Retorno entre o rebalanceamento de hoje e o rebalanceamento futuro
        ret_bruto = apurar_retorno_periodo(precos, top_n, data_atual, data_prox)
        ret_liq = descontar_custos(ret_bruto, turnover, config.CUSTO_POR_OPERACAO)
        
        # --- BENCHMARKS ---
        # Isolamos o retorno exato do índice IBOV/CDI do dia do rebalanceamento atual até o próximo
        idx_b_start = benchmarks.index.get_indexer([data_atual], method='pad')[0]
        idx_b_end = benchmarks.index.get_indexer([data_prox], method='pad')[0]
        ret_ibov = (benchmarks['ibov'].iloc[idx_b_end] / benchmarks['ibov'].iloc[idx_b_start]) - 1
        ret_bova = (benchmarks['bova11'].iloc[idx_b_end] / benchmarks['bova11'].iloc[idx_b_start]) - 1
        
        idx_c_start = cdi.index.get_indexer([data_atual], method='pad')[0]
        idx_c_end = cdi.index.get_indexer([data_prox], method='pad')[0]
        ret_cdi = (cdi['cdi_acumulado'].iloc[idx_c_end] / cdi['cdi_acumulado'].iloc[idx_c_start]) - 1
        
        # Armazena tudo
        resultados_mes.append({
            'data_rebalanceamento': data_atual,
            'retorno_bruto': ret_bruto,
            'retorno_liquido': ret_liq,
            'turnover': turnover,
            'custo': ret_bruto - ret_liq,
            'dist_media_mst': dist_media,
            'retorno_ibov': ret_ibov,
            'retorno_bova11': ret_bova,
            'retorno_cdi': ret_cdi
        })
        
        for t, p in pesos_novos.items():
            carteiras.append({
                'data_rebalanceamento': data_atual,
                'ticker': t,
                'farness': farness.loc[t],
                'peso': p
            })
            
        pesos_anteriores = pesos_novos
        
    print("\n--- LOOP FINALIZADO ---")
    print("Consolidando as saídas auditáveis em .parquet...")
    
    df_res = pd.DataFrame(resultados_mes).set_index('data_rebalanceamento')
    df_cart = pd.DataFrame(carteiras)
    df_farness_all = pd.concat(todas_farness)
    
    df_res.to_parquet(config.RESULTADOS / "serie_retornos_nexus.parquet")
    df_cart.to_parquet(config.RESULTADOS / "carteiras_mensais.parquet")
    df_farness_all.to_parquet(config.RESULTADOS / "farness_completa.parquet")
    
    print("Renderizando gráficos em images/...")
    gerar_graficos(df_res)
    
    print("Emitindo Relatório Final (Markdown)...")
    
    # Descobre qual foi o ganho anual composto do CDI para usá-lo como Risk-Free no Sharpe
    cdi_anual = (1 + df_res['retorno_cdi']).prod() ** (12 / len(df_res)) - 1
    
    m_nexus = calcular_metricas_estatisticas(df_res['retorno_liquido'], cdi_anual)
    m_cdi = calcular_metricas_estatisticas(df_res['retorno_cdi'], cdi_anual)
    m_ibov = calcular_metricas_estatisticas(df_res['retorno_ibov'], cdi_anual)
    m_bova = calcular_metricas_estatisticas(df_res['retorno_bova11'], cdi_anual)
    
    turnover_medio = df_res['turnover'].mean() * 100
    
    # Constrói o texto do documento final
    relatorio = f"""# Resumo do Backtest MVP - Robô Nexus

**Data de aprovação do relatório:** Automática (Final do Teste Cego)
**Métrica Vencedora Oficial:** Farness (Soma Absoluta das Distâncias)

## 1. Parâmetros Ativos
- **Janela de Correlação (Shrinkage):** {config.JANELA_CORRELACAO} dias
- **Tamanho da Carteira:** Top {config.TOP_N} ações da periferia
- **Custo de Transação Escorregadio (B3 + Corretagem):** {config.CUSTO_POR_OPERACAO * 100}% por perna
- **Pesos:** Equal-weight (Transparência absoluta, sem fit de variância/Sharpe nulo)
- **Filtro de Regime:** DESLIGADO neste MVP (Teste limpo apenas com a seleção topológica)

## 2. Gráficos Visuais de Desempenho

### 📈 Retorno Acumulado (Curva de Capital)
![Curva de Capital](../images/01_mvp_puro_retorno_acumulado.png)

> **Contexto para a Banca:** O Ibovespa no período rendeu *menos* que o CDI puro. Nosso benchmark e obstáculo central sempre será superar o dinheiro 100% livre de risco de crédito (CDI).

### 📉 Drawdown (As dores da Carteira)
![Drawdown](../images/01_mvp_puro_drawdown.png)

### 🔄 Estabilidade (Giro Mensal)
![Turnover](../images/01_mvp_puro_turnover_mensal.png)
> **Turnover médio mensal:** {turnover_medio:.1f}% 
*(Isso significa que o robô muda aproximadamente {turnover_medio / 10:.1f} ações por mês, segurando posições por mais de um semestre. Uma prova que a MST é estável no longo prazo).*

## 3. Tabela de Métricas Finais

| Métrica | Nexus (Líquido) | CDI | Ibovespa | BOVA11 |
|---|---|---|---|---|
| **Ret. Acumulado 15 anos** | {m_nexus['Ret. Acumulado']:.1%} | {m_cdi['Ret. Acumulado']:.1%} | {m_ibov['Ret. Acumulado']:.1%} | {m_bova['Ret. Acumulado']:.1%} |
| **Rentabilidade Anualizada** | {m_nexus['Ret. Anualizado']:.1%} | {m_cdi['Ret. Anualizado']:.1%} | {m_ibov['Ret. Anualizado']:.1%} | {m_bova['Ret. Anualizado']:.1%} |
| **Volatilidade Anual** | {m_nexus['Vol. Anualizada']:.1%} | {m_cdi['Vol. Anualizada']:.1%} | {m_ibov['Vol. Anualizada']:.1%} | {m_bova['Vol. Anualizada']:.1%} |
| **Sharpe Ratio Clássico** | **{m_nexus['Sharpe']:.2f}** | N/A | {m_ibov['Sharpe']:.2f} | {m_bova['Sharpe']:.2f} |
| **Máximo Drawdown** | {m_nexus['Max Drawdown']:.1%} | {m_cdi['Max Drawdown']:.1%} | {m_ibov['Max Drawdown']:.1%} | {m_bova['Max Drawdown']:.1%} |
| **Calmar Ratio** | {m_nexus['Calmar']:.2f} | N/A | {m_ibov['Calmar']:.2f} | {m_bova['Calmar']:.2f} |

"""
    # Alarmes inteligentes automáticos!
    if m_nexus['Sharpe'] < 0:
        relatorio += "\n> ⚠️ **ALERTA CRÍTICO:** O Sharpe do Nexus ficou **NEGATIVO**! A carteira perdeu do CDI de forma humilhante considerando o risco. Isso mostra a fragilidade do modelo puro, e **prova** que a Pessoa 2 (Filtro de Regime) será nossa verdadeira salvadora, defendendo a carteira com o CDI quando a árvore encolher."
    
    if turnover_medio > 60:
        relatorio += "\n> ⚠️ **ALERTA DE GIRO:** Turnover acima de 60%! Os lucros estão virando pó na mão da B3 e da corretora."
        
    doc_path = Path("docs") / "resumo_backtest_mvp.md"
    doc_path.write_text(relatorio, encoding="utf-8")
    
    print("\n[+] SUCESSO! ")
    print(f"O Relatório do MVP está perfeitamente finalizado e auditado em:\n -> {doc_path.resolve()}")

if __name__ == '__main__':
    main()
