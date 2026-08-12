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


def filtro_ml(features: pd.DataFrame, candidatas: List[str], modelo: Any) -> List[str]:
    """
    Filtro de Alpha Baseado em Machine Learning (Classificação de Probabilidade).
    
    Este filtro utiliza um modelo de Machine Learning (como Random Forest ou XGBoost)
    previamente treinado para prever a direcionalidade da ação. O modelo avalia as
    características (features) atuais da ação e retorna a probabilidade dela ter
    um retorno positivo nos próximos K dias.
    
    Se a probabilidade estimada de alta (classe 1) for maior que 50%, a ação é aprovada.
    
    Args:
        features (pd.DataFrame): DataFrame contendo as features (variáveis independentes)
            calculadas no dia T-1 para todas as ações. O índice deve ser o ticker.
            Exemplos de features: RSI, Volatilidade_21d, Distancia_MST, Razao_Preco_SMA200, etc.
        candidatas (List[str]): Lista com os tickers das ações candidatas vindas da MST.
        modelo (Any): O objeto do modelo treinado (ex: sklearn RandomForestClassifier).
            O modelo precisa expor o método `.predict()` ou `.predict_proba()`.
            
    Returns:
        List[str]: Lista contendo os tickers aprovados pelo modelo de Machine Learning.
    """
    # 1. Filtramos as features para incluir apenas as ações que estão na lista de candidatas.
    # Fazemos um .loc para pegar apenas as linhas (índice) correspondentes aos tickers.
    try:
        features_candidatas = features.loc[candidatas]
    except KeyError as e:
        # Se alguma ação da lista não estiver no dataset de features, isso previne que o código quebre.
        logging.error(f"Erro: Algumas candidatas não possuem features cadastradas. Detalhe: {e}")
        return []
    
    # 2. Verificação de segurança: os dados não podem conter Nulos (NaN) para o ML não quebrar.
    if features_candidatas.isnull().values.any():
        # Em produção, você poderia fazer uma imputação (ex: preencher NAs com média).
        # Aqui seremos conservadores: dropamos ações com dado faltando para evitar distorção.
        features_candidatas = features_candidatas.dropna()
        if features_candidatas.empty:
            return []
            
    # 3. O modelo faz as previsões.
    # Vamos assumir que o modelo é de classificação binária (0: cai, 1: sobe).
    # Usamos o método `.predict()` que retorna a classe final prevista.
    previsoes = modelo.predict(features_candidatas)
    
    # 4. Criamos uma série com os resultados.
    # O índice será o ticker (vindo do DataFrame de features) e o valor será a previsão (0 ou 1).
    resultado_series = pd.Series(data=previsoes, index=features_candidatas.index)
    
    # 5. Aplicamos o filtro.
    # Mantemos apenas os tickers cuja previsão é igual a 1 (retorno positivo).
    aprovadas = resultado_series[resultado_series == 1].index.tolist()
    
    # logging.info(f"Filtro ML: de {len(candidatas)} candidatas, {len(aprovadas)} foram aprovadas.")
    
    return aprovadas

