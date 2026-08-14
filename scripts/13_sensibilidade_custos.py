"""
===============================================================================
PROJETO NEXUS - DESAFIO ITAÚ ASSET QUANT AI 2026
Estudo de Robustez: Análise de Sensibilidade a Custos de Transação e Slippage
Arquivo: scripts/13_sensibilidade_custos.py
===============================================================================

OBJETIVO DO SCRIPT:
-------------------
Avalia a resiliência empírica da estratégia oficial (Momentum Puro SMA 150 com
CAP 10%) e da arquitetura em Cascata sob diferentes regimes de custos
operacionais, corretagem, emolumentos da B3 e slippage/market impact:
  - 0 bps (Custo Teórico Zero)
  - 2.5 bps por perna (Execução High-Volume Institucional)
  - 5.0 bps por perna (CASO BASE: Corretagem + B3 padrão)
  - 10.0 bps por perna (Spread Médio em Mid Caps)
  - 15.0 bps por perna (Small Caps com Baixa Liquidez)
  - 20.0 bps por perna (Cenário de Estresse e Alto Slippage)
  - 30.0 bps por perna (Pior Cenário de Choque de Iliquidez)

SAÍDAS GERADAS:
---------------
- Gráfico: `images/07_sensibilidade_custos_transacao.png`
- Tabela de sensibilidade impressa e consolidada.
===============================================================================
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Inclusão da raiz do projeto
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
    calcular_turnover,
    calcular_metricas_institucionais
)
from src.nexus.alpha_filters import filtro_momentum, filtro_ml

# Grade de custos por perna em pontos-base (bps)
CUSTOS_BPS_TESTADOS = [0.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0, 25.0, 30.0]
POOL_SIZE = 20
L_MOMENTUM = 150
MIN_MESES_TREINO = 12

IMG_DIR = Path("images")
IMG_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 80)
    print("  PROJETO NEXUS - ANÁLISE DE SENSIBILIDADE A CUSTOS DE TRANSAÇÃO")
    print("  (Avaliando Robustez sob Diferentes Níveis de Slippage e Corretagem)")
    print("=" * 80)
    
    # 1. Carregamento dos dados
    universo = pd.read_parquet(config.PROCESSADOS / "universo_mensal.parquet")
    retornos = pd.read_parquet(config.PROCESSADOS / "retornos_log.parquet")
    precos = pd.read_parquet(config.PROCESSADOS / "precos_ajustados.parquet")
    cdi = pd.read_parquet(config.PROCESSADOS / "cdi_diario.parquet")
    features_all = pd.read_parquet(config.PROCESSADOS / "features_ml.parquet")
    
    features_cols = [
        'distancia_sma50', 'distancia_sma200', 'volatilidade_21d',
        'rsi_14d', 'retorno_5d', 'retorno_21d', 'farness_mst'
    ]
    
    datas_rebalanceamento = sorted(universo['data_rebalanceamento'].unique())
    datas_in_sample = [d for d in datas_rebalanceamento if d <= pd.Timestamp('2018-12-31')]
    
    # Pré-cálculo da série temporal de decisões, retornos brutos e turnover (independente de custo)
    print(f"\n[1/3] Simulando alocações e apurando turnover em {len(datas_in_sample)-1} meses...")
    
    dados_simulacao = []
    pesos_ant_mom = None
    pesos_ant_cascata = None
    
    for i, data_atual in enumerate(datas_in_sample):
        if i == len(datas_in_sample) - 1:
            break
            
        data_prox = datas_in_sample[i + 1]
        ativos_elegiveis = universo[universo['data_rebalanceamento'] == data_atual]['ticker'].tolist()
        
        # MST
        mascara_hist_ret = (retornos.index < data_atual)
        janela_ret = retornos.index[mascara_hist_ret][-config.JANELA_CORRELACAO:]
        ret_hist = retornos.loc[janela_ret, ativos_elegiveis]
        corr = calcular_matriz_correlacao(ret_hist)
        dist = correlacao_para_distancia(corr)
        mst = construir_mst(dist)
        farness = calcular_farness(mst)
        candidatas = selecionar_top_n(farness, n=POOL_SIZE)
        
        # CDI
        idx_c_start = cdi.index.get_indexer([data_atual], method='pad')[0]
        idx_c_end = cdi.index.get_indexer([data_prox], method='pad')[0]
        ret_cdi = float((cdi['cdi_acumulado'].iloc[idx_c_end] / cdi['cdi_acumulado'].iloc[idx_c_start]) - 1.0)
        
        # Momentum
        mascara_hist_precos = (precos.index < data_atual)
        janela_precos = precos.index[mascara_hist_precos][-L_MOMENTUM:]
        precos_hist_para_filtro = precos.loc[janela_precos, candidatas]
        aprov_mom = filtro_momentum(precos_hist_para_filtro, candidatas, L=L_MOMENTUM)
        
        # ML Walk-Forward
        df_treino_wf = features_all[features_all['data_rebalanceamento'] < data_atual].dropna(subset=features_cols)
        n_meses_treino_disp = df_treino_wf['data_rebalanceamento'].nunique()
        feat_mes = features_all[features_all['data_rebalanceamento'] == data_atual].set_index('ticker')
        
        if n_meses_treino_disp >= MIN_MESES_TREINO:
            scaler_wf = StandardScaler()
            X_train_scaled = scaler_wf.fit_transform(df_treino_wf[features_cols])
            modelo_wf = LogisticRegression(max_iter=1000, class_weight='balanced', C=1.0, random_state=42)
            modelo_wf.fit(X_train_scaled, df_treino_wf['target_direcao'])
            artefato_local = {'modelo': modelo_wf, 'scaler': scaler_wf, 'features': features_cols}
            aprov_cascata = filtro_ml(feat_mes, aprov_mom, artefato_local) if len(aprov_mom) > 0 else []
        else:
            aprov_cascata = aprov_mom
            
        # Ponderações
        pesos_mom = calcular_pesos_equal_weight(aprov_mom, cap=config.CAP_POR_ATIVO)
        pesos_cascata = calcular_pesos_equal_weight(aprov_cascata, cap=config.CAP_POR_ATIVO)
        
        turnover_mom = calcular_turnover(pesos_ant_mom, pesos_mom)
        turnover_cascata = calcular_turnover(pesos_ant_cascata, pesos_cascata)
        
        ret_bruto_mom = apurar_retorno_periodo(precos, aprov_mom, data_atual, data_prox) if len(aprov_mom) > 0 else 0.0
        ret_bruto_cascata = apurar_retorno_periodo(precos, aprov_cascata, data_atual, data_prox) if len(aprov_cascata) > 0 else 0.0
        
        dados_simulacao.append({
            'data': data_atual,
            'ret_cdi': ret_cdi,
            'aloc_acoes_mom': float(pesos_mom.sum()),
            'aloc_caixa_mom': float(1.0 - pesos_mom.sum()),
            'ret_bruto_mom': ret_bruto_mom,
            'turnover_mom': turnover_mom,
            'aloc_acoes_cascata': float(pesos_cascata.sum()),
            'aloc_caixa_cascata': float(1.0 - pesos_cascata.sum()),
            'ret_bruto_cascata': ret_bruto_cascata,
            'turnover_cascata': turnover_cascata
        })
        
        pesos_ant_mom = pesos_mom
        pesos_ant_cascata = pesos_cascata
        
    df_sim = pd.DataFrame(dados_simulacao)
    serie_cdi = df_sim['ret_cdi']
    
    # 2. Avaliação dos diferentes níveis de custo
    print("\n[2/3] Avaliando a grade de custos transacionais (0 a 30 bps por perna)...")
    
    linhas_tabela = []
    
    for custo_bps in CUSTOS_BPS_TESTADOS:
        custo_frac = custo_bps / 10000.0  # Converte bps em fração decimal (ex: 5 bps = 0.0005)
        
        # Aplicação dos custos
        custo_total_mom = df_sim['turnover_mom'] * (custo_frac * 2.0)
        ret_liq_mom = (df_sim['ret_bruto_mom'] * df_sim['aloc_acoes_mom']) + (df_sim['ret_cdi'] * df_sim['aloc_caixa_mom']) - custo_total_mom
        
        custo_total_cascata = df_sim['turnover_cascata'] * (custo_frac * 2.0)
        ret_liq_cascata = (df_sim['ret_bruto_cascata'] * df_sim['aloc_acoes_cascata']) + (df_sim['ret_cdi'] * df_sim['aloc_caixa_cascata']) - custo_total_cascata
        
        m_mom = calcular_metricas_institucionais(ret_liq_mom, serie_cdi)
        m_cascata = calcular_metricas_institucionais(ret_liq_cascata, serie_cdi)
        
        linhas_tabela.append({
            'custo_bps_perna': custo_bps,
            'custo_bps_turnover': custo_bps * 2.0,
            'sharpe_mom_classico': m_mom['sharpe_classico'],
            'sharpe_mom_geom': m_mom['sharpe_geometrico'],
            'cagr_mom': m_mom['ret_anual_cagr'],
            'vol_mom': m_mom['vol_anual'],
            'sharpe_cascata_classico': m_cascata['sharpe_classico'],
            'sharpe_cascata_geom': m_cascata['sharpe_geometrico'],
            'cagr_cascata': m_cascata['ret_anual_cagr'],
            'vol_cascata': m_cascata['vol_anual']
        })
        
    df_sensibilidade = pd.DataFrame(linhas_tabela)
    
    print("\n=== TABELA DE SENSIBILIDADE A CUSTOS OPERACIONAIS (IN-SAMPLE 2011-2018) ===")
    print(df_sensibilidade[['custo_bps_perna', 'cagr_mom', 'vol_mom', 'sharpe_mom_classico', 'sharpe_mom_geom', 'cagr_cascata', 'sharpe_cascata_geom']].to_string(index=False))
    
    # 3. Geração do Gráfico Institucional
    print("\n[3/3] Gerando gráfico em 'images/07_sensibilidade_custos_transacao.png'...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 9), sharex=True)
    
    custos_x = df_sensibilidade['custo_bps_perna']
    cdi_cagr = calcular_metricas_institucionais(serie_cdi, serie_cdi)['ret_anual_cagr']
    
    # Painel 1: Sharpe Ratio vs Custo
    ax1.plot(custos_x, df_sensibilidade['sharpe_mom_geom'], marker='o', linewidth=2.5, color='#1f77b4', label='Momentum Puro (SMA 150) - Sharpe Geométrico')
    ax1.plot(custos_x, df_sensibilidade['sharpe_mom_classico'], marker='s', linestyle=':', linewidth=1.8, color='#1f77b4', alpha=0.7, label='Momentum Puro - Sharpe Clássico (Aritmético)')
    ax1.plot(custos_x, df_sensibilidade['sharpe_cascata_geom'], marker='^', linewidth=2.2, color='#9467bd', label='Cascata (Momentum + ML) - Sharpe Geométrico')
    
    ax1.axhline(y=0.107, color='orange', linestyle='--', linewidth=1.8, label='Threshold Monte Carlo Macacos 95% (0.107)')
    ax1.axhline(y=0.0, color='gray', linestyle='-', linewidth=1.0, alpha=0.5)
    ax1.axvline(x=5.0, color='red', linestyle=':', linewidth=2.0, label='Caso Base Institucional (5 bps/perna)')
    
    ax1.set_title("Sensibilidade do Sharpe Ratio aos Custos de Transação (Corretagem + B3 + Slippage)", fontsize=12, fontweight='bold')
    ax1.set_ylabel("Sharpe Ratio Anualizado", fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.4)
    ax1.legend(loc='upper right', frameon=True, fontsize=9)
    
    # Painel 2: Retorno Anualizado (CAGR) vs Custo
    ax2.plot(custos_x, df_sensibilidade['cagr_mom'] * 100, marker='o', linewidth=2.5, color='#1f77b4', label='Momentum Puro (SMA 150) CAGR')
    ax2.plot(custos_x, df_sensibilidade['cagr_cascata'] * 100, marker='^', linewidth=2.2, color='#9467bd', label='Cascata (Momentum + ML) CAGR')
    ax2.axhline(y=cdi_cagr * 100, color='black', linestyle='--', linewidth=2.0, label=f'Benchmark CDI Líquido ({cdi_cagr*100:.1f}% a.a.)')
    ax2.axvline(x=5.0, color='red', linestyle=':', linewidth=2.0, label='Caso Base (5 bps/perna)')
    
    ax2.set_title("Sensibilidade do Retorno Anualizado (CAGR) aos Custos de Transação", fontsize=12, fontweight='bold')
    ax2.set_ylabel("Retorno Anualizado Composto (%)", fontsize=10)
    ax2.set_xlabel("Custo por Perna de Operação (pontos-base / bps)", fontsize=10)
    ax2.grid(True, linestyle='--', alpha=0.4)
    ax2.legend(loc='upper right', frameon=True, fontsize=9)
    
    plt.suptitle("Estudo de Robustez: Impacto de Custos Operacionais e Slippage no Robô Nexus", fontsize=13, fontweight='bold', y=0.99)
    plt.tight_layout()
    
    caminho_grafico = IMG_DIR / "07_sensibilidade_custos_transacao.png"
    plt.savefig(caminho_grafico, dpi=180)
    plt.close()
    
    print(f" -> [SUCESSO] Gráfico de sensibilidade salvo em: {caminho_grafico.resolve()}")
    
    # Salva dataset com os resultados numéricos
    caminho_csv = config.RESULTADOS / "sensibilidade_custos_transacao.csv"
    df_sensibilidade.to_csv(caminho_csv, index=False)
    print(f" -> Tabela consolidada salva em: {caminho_csv.resolve()}")
    print("=" * 80)


if __name__ == '__main__':
    main()
