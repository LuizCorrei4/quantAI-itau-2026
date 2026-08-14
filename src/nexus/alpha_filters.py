"""
===============================================================================
PROJETO NEXUS - DESAFIO ITAÚ ASSET QUANT AI 2026
Módulo de Filtros de Alpha (Convicção Direcional - Camadas 2 e 3)
Arquivo: src/nexus/alpha_filters.py
===============================================================================

Este módulo contém as funções de filtragem direcional aplicadas sobre o pool de
ações descorrelacionadas selecionadas na periferia da Minimum Spanning Tree (MST).

ARQUITETURA EM CASCATA:
-----------------------
1. Camada 1 (MST): Filtro de Universo Descorrelacionado (Farness Topológica)
2. Camada 2 (Momentum): Filtro Linear de Tendência (Preço > SMA_L)
3. Camada 3 (Machine Learning): Filtro Probabilístico Não-Linear (Classificador LogReg)

RIGOR METODOLÓGICO:
-------------------
- Todos os filtros consom estritamente informações conhecidas até o tempo T-1.
- Imputações de dados ausentes utilizam a mediana da amostra local (evitando outliers).
===============================================================================
"""

import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Configuração de logging estruturado
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


def filtro_momentum(precos_historicos: pd.DataFrame, candidatas: List[str], L: int = 150) -> List[str]:
    """
    Filtro de Alpha Baseado em Tendência e Momentum Clássico (Camada 2).
    
    Princípio Econômico:
        Baseado na premissa da persistência temporal de retornos (Jegadeesh & Titman, 1993)
        e na Navalha de Occam: alocar capital exclusivamente em ativos cuja trajetória
        recente demonstre tendência primária de alta.
        
    Regra de Decisão:
        Aprova o ativo 'i' se e somente se:
            Preco_Fechamento[T-1] > SMA_L(Preco_Fechamento)[T-1]
            
    Args:
        precos_historicos (pd.DataFrame): Matriz histórica de preços ajustados contendo
            estritamente dados até T-1 (zero look-ahead bias). Linhas = datas, Colunas = tickers.
        candidatas (List[str]): Lista de tickers das ações vindas do filtro topológico (MST).
        L (int): Janela de observação em pregões úteis para a Média Móvel Simples (padrão = 150 dias).
        
    Returns:
        List[str]: Subconjunto contendo apenas os tickers dos ativos aprovados no critério de momentum.
    """
    # 1. Filtra apenas as colunas das ações candidatas presentes no DataFrame
    colunas_validas = [c for c in candidatas if c in precos_historicos.columns]
    if len(colunas_validas) == 0:
        return []
        
    precos_candidatas = precos_historicos[colunas_validas]
    
    # 2. Verificação de suficiência amostral
    if len(precos_candidatas) < L:
        logging.warning(f"Histórico de preços ({len(precos_candidatas)} dias) inferior a L={L}. Nenhuma ação aprovada.")
        return []
        
    # 3. Recorte dos últimos L pregões encerrados
    janela_l_dias = precos_candidatas.tail(L)
    
    # 4. Cálculo da Média Móvel Simples (SMA)
    sma_l = janela_l_dias.mean()
    
    # 5. Preço no último pregão disponível (T-1)
    preco_atual = janela_l_dias.iloc[-1]
    
    # 6. Aplicação da condição booleana: Preço > SMA
    sinal_positivo = preco_atual > sma_l
    aprovadas = sinal_positivo[sinal_positivo].index.tolist()
    
    return aprovadas


def filtro_ml(features: pd.DataFrame, candidatas: List[str], artefato_modelo: Dict[str, Any]) -> List[str]:
    """
    Filtro de Alpha Baseado em Classificação por Machine Learning (Camada 3).
    
    Princípio de Modelagem:
        Utiliza um modelo preditivo (ex: Regressão Logística treinada via Walk-Forward)
        para estimar a probabilidade condicional de retorno positivo no mês subsequente [T, T+1].
        
    Regra de Decisão:
        Aprova o ativo 'i' se a previsão do modelo for positiva (Classe = 1, ou P(Alta) > 0.50).
        
    Args:
        features (pd.DataFrame): Painel de features do mês atual T (calculadas em T-1).
                                 Índice = tickers, Colunas = features técnicas e topológicas.
        candidatas (List[str]): Lista de tickers das ações candidatas a serem filtradas.
        artefato_modelo (Dict[str, Any]): Dicionário contendo o modelo treinado, o scaler ajustado
                                          e a lista de colunas esperadas.
                                          
    Returns:
        List[str]: Lista contendo os tickers das ações aprovadas pela inteligência do modelo.
    """
    if artefato_modelo is None or len(candidatas) == 0:
        return []
        
    modelo = artefato_modelo['modelo']
    scaler = artefato_modelo['scaler']
    colunas_treino = artefato_modelo['features']
    
    # Filtra apenas as candidatas presentes no painel de features
    tickers_presentes = [t for t in candidatas if t in features.index]
    if len(tickers_presentes) == 0:
        return []
        
    features_candidatas = features.loc[tickers_presentes].copy()
    
    # Imputação prudencial de valores faltantes (usando mediana local em vez de 1.0)
    if 'farness_mst' in features_candidatas.columns:
        mediana_farness = features_candidatas['farness_mst'].median()
        if pd.isna(mediana_farness):
            mediana_farness = 100.0  # Valor médio típico na escala de farness da MST
        features_candidatas['farness_mst'] = features_candidatas['farness_mst'].fillna(mediana_farness)
        
    features_candidatas = features_candidatas.dropna(subset=colunas_treino)
    if features_candidatas.empty:
        return []
        
    # Extrai estritamente a matriz X nas colunas de treinamento
    X = features_candidatas[colunas_treino]
    
    # Normalização Z-score com o scaler do modelo
    if scaler is not None:
        X_scaled = scaler.transform(X)
    else:
        X_scaled = X
        
    # Predição de direção
    previsoes = modelo.predict(X_scaled)
    
    # Seleção dos ativos com previsão positiva (Target = 1)
    series_pred = pd.Series(previsoes, index=features_candidatas.index)
    aprovadas = series_pred[series_pred == 1].index.tolist()
    
    return aprovadas
