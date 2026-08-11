"""
Módulo de Portfólio do Robô Nexus.
Responsável por selecionar ativos, alocar pesos, calcular o retorno do período
e apurar métricas operacionais como turnover e custos de transação.
"""

import pandas as pd
import numpy as np

def selecionar_top_n(farness: pd.Series, n: int = 10) -> list[str]:
    """
    Ordena a Farness (do maior para o menor) e seleciona as N ações mais periféricas.
    """
    # Ordena decrescente (maior farness = mais na borda da rede)
    farness_ordenada = farness.sort_values(ascending=False)
    # Extrai apenas os tickers (índice da Series) das top N
    top_tickers = farness_ordenada.head(n).index.tolist()
    return top_tickers


def calcular_pesos_equal_weight(tickers: list[str]) -> pd.Series:
    """
    Gera um vetor de pesos iguais (1/N) para a lista de ativos selecionados.
    """
    n = len(tickers)
    # Se a lista vier vazia por algum erro, não quebra a matemática
    peso = 1.0 / n if n > 0 else 0.0
    
    # Cria uma Series com o peso uniforme para cada ticker
    return pd.Series(peso, index=tickers)


def descontar_custos(retorno_bruto: float, turnover: float, custo_pct: float = 0.0005) -> float:
    """
    Subtrai o custo de corretagem/emolumentos do retorno bruto com base no turnover.
    O turnover reflete o total girado (então o custo incide na perna de compra + venda).
    """
    # Multiplicamos por 2 porque o turnover é apenas uma "via" da troca 
    # (quem saiu e quem entrou). Na prática, pagamos taxa pra vender E pra comprar.
    custo_total = turnover * (custo_pct * 2)
    return retorno_bruto - custo_total


def apurar_retorno_periodo(precos: pd.DataFrame, tickers: list[str], data_inicio: pd.Timestamp, data_fim: pd.Timestamp) -> float:
    """
    Calcula o retorno equal-weight da carteira entre duas datas específicas.
    """
    # Recorte do dataframa de preços para o período e tickers desejados
    df_precos_recorte = precos.loc[data_inicio:data_fim, tickers]

    # Pegando a cotação do primeiro e último dia
    preco_inicial = df_precos_recorte.iloc[0]
    preco_final = df_precos_recorte.iloc[-1]

    # Calculando o retorno individual de cada ação
    retornos_individuais = (preco_final / preco_inicial) - 1

    # Retorno da carteira é a média dos retornos individuais
    return retornos_individuais.mean()  


def calcular_turnover(pesos_antigos: pd.Series, pesos_novos: pd.Series) -> float:
    """
    Mede a porcentagem da carteira que precisou ser comprada/vendida neste mês.
    Fórmula: Soma( |Peso_Novo - Peso_Antigo| ) / 2
    
    DICA 1: Se `pesos_antigos` for None ou estiver vazio (primeiro mês do backtest), 
    o turnover é 1.0 (ou seja, 100% da carteira foi comprada do zero). Trate esse 'if'.
    
    DICA 2: Crie um dataframe ou alinhe as duas Series para garantir que ações 
    que saíram ou entraram tenham peso 0.0 na outra ponta.
    O jeito mais fácil do Pandas é:
    `df_pesos = pd.DataFrame({'novo': pesos_novos, 'antigo': pesos_antigos}).fillna(0.0)`
    
    DICA 3: Calcule a diferença absoluta `(df_pesos['novo'] - df_pesos['antigo']).abs()`.
    
    DICA 4: Some todas as diferenças e divida por 2. Retorne esse valor.
    """
    # Se `pesos_antigos` for None ou estiver vazio (primeiro mês do backtest), o turnover é 1.0
    if pesos_antigos is None or pesos_antigos.empty:
        return 1.0  # Primeiro mês, toda a carteira foi comprada do zero
    
    # Alinhando as duas Series para garantir que ações que saíram ou entraram tenham peso 0.0 na outra ponta
    df_pesos = pd.DataFrame({'novo': pesos_novos, 'antigo': pesos_antigos}).fillna(0.0)

    # Calculando a diferença absoluta
    diferenca_absoluta = (df_pesos['novo'] - df_pesos['antigo']).abs()

    # Somando todas as diferenças e dividindo por 2
    turnover = diferenca_absoluta.sum() / 2.0
    return turnover
