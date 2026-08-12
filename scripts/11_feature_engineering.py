"""
Feature Engineering para Machine Learning 

Este script prepara a "matéria prima" para os nossos modelos de IA.
Ele calcula indicadores financeiros complexos para cada ação no dia
do rebalanceamento, para que o modelo tente encontrar padrões
que antecedem retornos positivos.

Tudo é calculado estritamente no tempo T (sem olhar o futuro),
exceto a coluna `Target`, que olha o tempo T+1 para criar o "gabarito"
(a resposta correta se a ação subiu ou desceu).
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.nexus import config

def calcular_rsi(serie_precos: pd.Series, janela: int = 14) -> pd.Series:
    """Calcula o Índice de Força Relativa (RSI) clásico."""
    delta = serie_precos.diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    
    # Média móvel exponencial (comum no RSI)
    media_ganho = ganho.ewm(com=janela - 1, min_periods=janela).mean()
    media_perda = perda.ewm(com=janela - 1, min_periods=janela).mean()
    
    rs = media_ganho / media_perda
    rsi = 100 - (100 / (1 + rs))
    return rsi

def main():
    print("=== FEATURE ENGINEERING PARA MACHINE LEARNING ===")
    
    # 1. Carregar Dados
    print("Carregando bases históricas...")
    precos = pd.read_parquet(config.PROCESSADOS / "precos_ajustados.parquet")
    universo = pd.read_parquet(config.PROCESSADOS / "universo_mensal.parquet")
    
    # Tenta carregar farness do backtest MVP para incluir como feature topológica
    caminho_farness = config.RESULTADOS / "farness_completa.parquet"
    if caminho_farness.exists():
        df_farness = pd.read_parquet(caminho_farness)
    else:
        df_farness = None
        print("Aviso: farness_completa.parquet não encontrada. Farness não será usada como feature.")

    datas_rebalanceamento = sorted(universo['data_rebalanceamento'].unique())
    
    dataset_linhas = []
    
    print(f"Calculando features para {len(datas_rebalanceamento)-1} meses...")
    
    # Precisamos calcular as features por ação usando a série contínua
    print("Calculando features contínuas (pode demorar alguns segundos)...")
    
    retornos_diarios = precos.pct_change()
    
    # Features baseadas em janelas rolantes (aplicado no dataframe todo de uma vez)
    sma_50 = precos.rolling(window=50).mean()
    sma_200 = precos.rolling(window=200).mean()
    volatilidade_21 = retornos_diarios.rolling(window=21).std() * np.sqrt(252) # Volatilidade anualizada local
    
    retorno_5d = precos.pct_change(periods=5)
    retorno_21d = precos.pct_change(periods=21)
    
    # RSI exige cálculo por coluna
    rsi_14 = precos.apply(calcular_rsi, janela=14)
    
    # 2. Montar o Dataset no "Recorte Mensal"
    # O modelo não prevê o dia a dia, ele prevê de mês em mês (rebalanceamento a rebalanceamento).
    for i, data_atual in enumerate(datas_rebalanceamento):
        if i == len(datas_rebalanceamento) - 1:
            break # Não temos como criar o Target para o último mês
            
        data_prox = datas_rebalanceamento[i+1]
        
        # Ações que eram elegíveis neste mês
        ativos_elegiveis = universo[universo['data_rebalanceamento'] == data_atual]['ticker'].tolist()
        
        for ticker in ativos_elegiveis:
            # Garante que os dados existem para esta ação na data atual e futura
            if pd.isna(precos.loc[data_atual, ticker]) or pd.isna(precos.loc[data_prox, ticker]):
                continue
                
            preco_hoje = precos.loc[data_atual, ticker]
            preco_futuro = precos.loc[data_prox, ticker]
            
            # --- O GABARITO (Target) ---
            # A ação subiu ou caiu do rebalanceamento atual até o próximo?
            retorno_real_mes = (preco_futuro / preco_hoje) - 1
            alvo = 1 if retorno_real_mes > 0 else 0
            
            # --- AS FEATURES (O que o modelo sabe no dia T) ---
            val_sma50 = sma_50.loc[data_atual, ticker]
            val_sma200 = sma_200.loc[data_atual, ticker]
            
            dist_sma50 = (preco_hoje / val_sma50) - 1 if not pd.isna(val_sma50) and val_sma50 != 0 else np.nan
            dist_sma200 = (preco_hoje / val_sma200) - 1 if not pd.isna(val_sma200) and val_sma200 != 0 else np.nan
            
            val_vol = volatilidade_21.loc[data_atual, ticker]
            val_rsi = rsi_14.loc[data_atual, ticker]
            val_ret5 = retorno_5d.loc[data_atual, ticker]
            val_ret21 = retorno_21d.loc[data_atual, ticker]
            
            # Captura farness (a posição dela no grafo na data atual)
            val_farness = np.nan
            if df_farness is not None:
                # O df_farness do MVP salva ticker como string solta, vamos filtrar
                filtro = (df_farness['data_rebalanceamento'] == data_atual) & (df_farness['ticker'] == ticker)
                if filtro.any():
                    val_farness = df_farness.loc[filtro, 'farness'].values[0]
            
            linha = {
                'data_rebalanceamento': data_atual,
                'ticker': ticker,
                
                # Features
                'distancia_sma50': dist_sma50,
                'distancia_sma200': dist_sma200,
                'volatilidade_21d': val_vol,
                'rsi_14d': val_rsi,
                'retorno_5d': val_ret5,
                'retorno_21d': val_ret21,
                'farness_mst': val_farness,
                
                # Target
                'target_direcao': alvo,
                'retorno_real_prox_mes': retorno_real_mes # Guardado por curiosidade analítica
            }
            
            dataset_linhas.append(linha)
            
    df_features = pd.DataFrame(dataset_linhas)
    
    # Removemos linhas que ficaram com Nulos devido a falta de histórico (ex: primeiros 200 dias para a SMA200)
    qtd_antes = len(df_features)
    df_features = df_features.dropna()
    qtd_depois = len(df_features)
    
    print(f"Limpeza de Nulos: {qtd_antes - qtd_depois} amostras removidas devido a histórico insuficiente.")
    print(f"Dataset de Machine Learning finalizado com {qtd_depois} linhas válidas (amostras).")
    
    # Salva o Dataset de ML
    caminho_saida = config.PROCESSADOS / "features_ml.parquet"
    df_features.to_parquet(caminho_saida, index=False)
    
    print(f"[+] Features de Machine Learning salvas com sucesso em: {caminho_saida.resolve()}")

if __name__ == '__main__':
    main()
