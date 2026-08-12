"""
Módulo de Filtros de Alpha (Convicção Direcional) - Projeto Nexus
Desafio Itaú Asset Quant AI 2026

Este módulo contém as lógicas de filtro aplicadas após a seleção topológica (MST).
Enquanto a MST atua como um 'Filtro de Universo' para encontrar ações descorrelacionadas,
estes filtros de Alpha atuam como 'Filtros Direcionais', garantindo que só compraremos 
aquelas ações periféricas se elas também tiverem perspectiva de alta (seja por Momentum
via Média Móvel ou previsão de Machine Learning).
"""

import pandas as pd
import numpy as np
from typing import List, Any
import logging

# Configuração básica de log para acompanharmos o que o filtro está fazendo
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def filtro_momentum(precos_historicos: pd.DataFrame, candidatas: List[str], L: int) -> List[str]:
    """
    Filtro de Alpha Baseado em Momentum (Tendência de Preço).
    
    A premissa deste filtro é a Navalha de Occam: comprar ativos apenas se eles
    estiverem em tendência de alta. Como proxy para tendência, usamos a Média 
    Móvel Simples (SMA - Simple Moving Average) de L dias.
    
    Se o preço atual do ativo estiver ACIMA da sua média histórica recente,
    consideramos que ele tem "momentum positivo" e ele é aprovado.
    
    Args:
        precos_historicos (pd.DataFrame): DataFrame contendo os preços ajustados das ações.
            O índice deve ser de datas (cronológico) e as colunas os tickers (ex: 'PETR4.SA').
            IMPORTANTE: Este DataFrame deve conter preços apenas até o dia T-1 para 
            evitar "look-ahead bias" (viés de olhar o futuro) na tomada de decisão do dia T.
        candidatas (List[str]): Lista com os tickers das ações que vieram do filtro de 
            universo (a MST). Por exemplo: as Top 20 ações periféricas.
        L (int): Comprimento (lookback window) da média móvel em dias úteis. 
            Valores comuns: 50 (curto/médio prazo) ou 200 (longo prazo).
            
    Returns:
        List[str]: Lista contendo apenas os tickers que passaram no filtro (Preço > SMA).
    """
    # 1. Filtramos o DataFrame de preços para conter apenas as colunas das ações candidatas.
    # Isso economiza processamento e evita erros com ações que não nos interessam.
    precos_candidatas = precos_historicos[candidatas]
    
    # 2. Verificação de segurança: temos dados suficientes para calcular a média de L dias?
    # Se o DataFrame tiver menos linhas que L, não podemos calcular a média.
    if len(precos_candidatas) < L:
        logging.warning(f"Histórico insuficiente para calcular SMA({L}). Aprovando nenhuma ação por segurança.")
        return []
    
    # 3. Pegamos a "janela" exata dos últimos L dias disponíveis na base de histórico.
    # Usamos .tail(L) que pega as últimas L linhas do DataFrame.
    janela_l_dias = precos_candidatas.tail(L)
    
    # 4. Calculamos a Média Móvel Simples (SMA).
    # Como pegamos exatamente os últimos L dias, a SMA é simplesmente a média (mean) dessa janela.
    # O resultado é uma pd.Series onde o índice é o Ticker e o valor é a Média.
    sma_L = janela_l_dias.mean()
    
    # 5. Pegamos o "Preço Atual".
    # Como estamos no fim do mês T-1 tomando decisão para o mês T, o "preço atual"
    # conhecido é o da última linha do histórico (o fechamento do último pregão).
    preco_atual = janela_l_dias.iloc[-1]
    
    # 6. Aplicamos a regra de decisão (O Filtro).
    # Comparamos a série de preços atuais com a série da SMA.
    # Isso gera uma pd.Series booleana (True se preco > sma, False caso contrário).
    sinal_momentum = preco_atual > sma_L
    
    # 7. Filtramos a lista original.
    # Selecionamos no índice da série (que são os Tickers) apenas aqueles onde o valor é True.
    aprovadas = sinal_momentum[sinal_momentum].index.tolist()
    
    # Logamos o resultado para transparência no debug (opcional, mas bom pra checar sanidade).
    # logging.info(f"Filtro Momentum (L={L}): de {len(candidatas)} candidatas, {len(aprovadas)} foram aprovadas.")
    
    return aprovadas


def filtro_ml(features: pd.DataFrame, candidatas: List[str], artefato_modelo: dict) -> List[str]:
    """
    Filtro de Alpha Baseado em Machine Learning (Classificação de Probabilidade).
    
    Este filtro utiliza um modelo de Machine Learning treinado para prever a direcionalidade.
    
    Args:
        features (pd.DataFrame): DataFrame contendo as features (calculadas no dia T-1).
                                 Deve conter as colunas esperadas pelo modelo e índice = ticker.
        candidatas (List[str]): Lista com os tickers das ações candidatas vindas da MST.
        artefato_modelo (dict): Dicionário salvo pelo treinamento contendo 'modelo', 'scaler' e 'features'.
            
    Returns:
        List[str]: Lista contendo os tickers aprovados.
    """
    modelo = artefato_modelo['modelo']
    scaler = artefato_modelo['scaler']
    colunas_treino = artefato_modelo['features']
    
    try:
        features_candidatas = features.loc[candidatas]
    except KeyError as e:
        logging.error(f"Erro: Algumas candidatas não possuem features cadastradas. Detalhe: {e}")
        return []
    
    # Preencher Nulos pontuais como fizemos no treinamento
    if 'farness_mst' in features_candidatas.columns:
        features_candidatas['farness_mst'] = features_candidatas['farness_mst'].fillna(1.0)
        
    features_candidatas = features_candidatas.dropna()
    if features_candidatas.empty:
        return []
        
    # Garante que passamos apenas as colunas exatas na ordem exata do treino
    X = features_candidatas[colunas_treino]
    
    # Aplica o Scaler (se existir)
    if scaler is not None:
        X_scaled = scaler.transform(X)
    else:
        X_scaled = X
        
    previsoes = modelo.predict(X_scaled)
    
    resultado_series = pd.Series(data=previsoes, index=features_candidatas.index)
    aprovadas = resultado_series[resultado_series == 1].index.tolist()
    
    return aprovadas

