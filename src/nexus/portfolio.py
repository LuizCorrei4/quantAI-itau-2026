"""
===============================================================================
PROJETO NEXUS - DESAFIO ITAÚ ASSET QUANT AI 2026
Módulo de Construção de Portfólio, Alocação, Custos, Operações e Métricas
Arquivo: src/nexus/portfolio.py
===============================================================================

Este módulo contém as funções fundamentais de dimensionamento de posições,
cálculo de pesos, apuração de retornos de período, controle de custos de transação
e cálculo institucional de métricas de performance e risco (Sharpe, Sortino, Drawdown).

DESTAQUES METODOLÓGICOS:
-----------------------
- Introdução do parâmetro `cap` na função `calcular_pesos_equal_weight` (CVM 175).
- Suporte a apuração padronizada de Sharpe Ratio em duas convenções institucionais:
    1. Sharpe Clássico (Excesso Aritmético Anualizado)
    2. Sharpe Geométrico (CAGR Excess / Volatilidade)
- Apuração precisa de Turnover e custos transacionais.
===============================================================================
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any


def selecionar_top_n(farness: pd.Series, n: int = 10) -> List[str]:
    """
    Ordena a série de Farness da MST em ordem decrescente e seleciona as N ações mais periféricas.
    
    No grafo de correlação financeira:
    - Maior Farness = maior soma de distâncias aos outros nós = nó na periferia do mercado.
    - Menor Farness = nó central (ex: bancos, blue chips altamente correlacionadas com o índice).
    
    Args:
        farness (pd.Series): Série indexada por tickers contendo o valor de Farness de cada ação.
        n (int): Quantidade de ativos a selecionar (padrão = 10).
        
    Returns:
        List[str]: Lista contendo os tickers das N ações mais periféricas.
    """
    # Ordenação decrescente: do ativo mais afastado para o mais central
    farness_ordenada = farness.sort_values(ascending=False)
    top_tickers = farness_ordenada.head(n).index.tolist()
    return top_tickers


def calcular_pesos_equal_weight(tickers: List[str], cap: Optional[float] = None) -> pd.Series:
    """
    Gera o vetor de alocação de pesos ponderados igualmente (Equal-Weight) para os ativos aprovados.
    
    REGRA DE CONCENTRAÇÃO MÁXIMA (CAP):
    ----------------------------------
    Se o parâmetro `cap` for fornecido (ex: 0.10 para 10% máximo por ativo):
    - Se N = 20: Peso individual = 1/20 = 5%  (soma = 100%, 0% em caixa)
    - Se N = 10: Peso individual = 1/10 = 10% (soma = 100%, 0% em caixa)
    - Se N = 5:  Peso individual = min(1/5, 0.10) = 10% (soma = 50%, 50% em CDI)
    - Se N = 2:  Peso individual = min(1/2, 0.10) = 10% (soma = 20%, 80% em CDI)
    - Se N = 0:  Retorna Series vazia (soma = 0%, 100% em CDI)
    
    O excedente de capital não alocado em ações fica implicitamente preservado em CDI,
    criando um mecanismo automático de proteção contra períodos de poucas oportunidades.
    
    Args:
        tickers (List[str]): Lista com os tickers dos ativos aprovados para a carteira.
        cap (Optional[float]): Teto máximo de peso individual por ativo (ex: 0.10).
        
    Returns:
        pd.Series: Série indexada pelos tickers com os pesos individuais de cada posição.
    """
    n = len(tickers)
    if n == 0:
        return pd.Series(dtype=float)
    
    # Peso uniforme base (1/N)
    peso_individual = 1.0 / n
    
    # Aplicação do teto máximo de concentração prudencial (CAP)
    if cap is not None and peso_individual > cap:
        peso_individual = cap
    
    return pd.Series(peso_individual, index=tickers)


def descontar_custos(retorno_bruto: float, turnover: float, custo_pct: float = 0.0005) -> float:
    """
    Subtrai as despesas de corretagem, emolumentos B3 e slippage do retorno bruto da carteira.
    
    Fórmula de Custo:
        Custo Total = Turnover * (Custo por perna * 2)
        - O turnover mede a fração substituída da carteira [0.0 a 1.0].
        - Multiplica-se por 2 porque uma substituição envolve uma perna de venda E uma perna de compra.
        
    Args:
        retorno_bruto (float): Retorno percentual bruto das ações investidas no período.
        turnover (float): Fração de giro da carteira apurada entre os meses [0.0, 1.0].
        custo_pct (float): Taxa de corretagem e emolumentos por perna (padrão = 0.0005, ou 5 bps).
        
    Returns:
        float: Retorno líquido das ações após o desconto das taxas operacionais.
    """
    custo_total = turnover * (custo_pct * 2.0)
    return retorno_bruto - custo_total


def apurar_retorno_periodo(precos: pd.DataFrame, tickers: List[str], 
                           data_inicio: pd.Timestamp, data_fim: pd.Timestamp) -> float:
    """
    Calcula o retorno médio equal-weight dos ativos mantidos na carteira entre duas datas de rebalanceamento.
    
    Args:
        precos (pd.DataFrame): DataFrame histórico de preços de fechamento ajustados (índice = datas).
        tickers (List[str]): Lista com os tickers pertencentes à carteira no período.
        data_inicio (pd.Timestamp): Data de início da posição (T).
        data_fim (pd.Timestamp): Data de encerramento da posição (T+1).
        
    Returns:
        float: Retorno médio percentual simples da cesta de ações no período.
    """
    if len(tickers) == 0:
        return 0.0
        
    # Recorte da matriz de preços para o intervalo [data_inicio, data_fim] e ativos da carteira
    df_precos_recorte = precos.loc[data_inicio:data_fim, tickers]
    
    # Cotações no primeiro pregão (entrada) e no último pregão (saída)
    preco_inicial = df_precos_recorte.iloc[0]
    preco_final = df_precos_recorte.iloc[-1]
    
    # Retornos individuais de cada ativo
    retornos_individuais = (preco_final / preco_inicial) - 1.0
    
    # Retorno equal-weight da carteira
    return float(retornos_individuais.mean())


def calcular_turnover(pesos_antigos: Optional[pd.Series], pesos_novos: pd.Series) -> float:
    """
    Calcula a taxa de Turnover (giro da carteira) entre dois rebalanceamentos consecutivos.
    
    Fórmula:
        Turnover = (1/2) * Sum( |Peso_Novo_i - Peso_Antigo_i| )
        
    Propriedades:
        - 0.0: Nenhuma alteração nos pesos (carteira idêntica).
        - 1.0: Substituição integral de todos os ativos da carteira (giro de 100%).
        - No primeiro mês (pesos_antigos is None ou vazio), o turnover é definido como 1.0 (compra inicial).
        
    Args:
        pesos_antigos (Optional[pd.Series]): Série com os pesos dos ativos no mês anterior (T-1).
        pesos_novos (pd.Series): Série com os pesos dos ativos no novo mês (T).
        
    Returns:
        float: Taxa de turnover do portfólio no intervalo [0.0, 1.0].
    """
    if pesos_antigos is None or pesos_antigos.empty:
        return 1.0  # Primeiro mês da estratégia: 100% da carteira comprada do zero
        
    # Alinhamento dos dois vetores de pesos preenchendo ativos que saíram/entraram com 0.0
    df_pesos = pd.DataFrame({'novo': pesos_novos, 'antigo': pesos_antigos}).fillna(0.0)
    
    # Diferença absoluta entre os pesos de cada ativo
    diferenca_absoluta = (df_pesos['novo'] - df_pesos['antigo']).abs()
    
    # Soma de todas as diferenças dividida por 2
    turnover = float(diferenca_absoluta.sum() / 2.0)
    return turnover


def calcular_metricas_institucionais(serie_retornos: pd.Series, serie_cdi: pd.Series) -> Dict[str, float]:
    """
    Calcula o conjunto completo e auditável de métricas estatísticas e de risco do portfólio.
    
    Convenções de Sharpe Ratio incluídas:
    1. Sharpe Clássico Anualizado (Excesso Aritmético):
       Sharpe = sqrt(12) * mean(R_p - R_cdi) / std(R_p - R_cdi)
    2. Sharpe Geométrico (CAGR Excess):
       Sharpe = (CAGR_p - CAGR_cdi) / Volatilidade_Anualizada
       
    Args:
        serie_retornos (pd.Series): Série temporal de retornos mensais líquidos da estratégia.
        serie_cdi (pd.Series): Série temporal de retornos mensais do benchmark CDI.
        
    Returns:
        Dict[str, float]: Dicionário com todas as métricas calculadas.
    """
    n_meses = len(serie_retornos)
    anos = n_meses / 12.0
    if anos <= 0:
        return {
            'ret_anual_cagr': 0.0, 'ret_anual_aritmetico': 0.0,
            'vol_anual': 0.0, 'cdi_anual_cagr': 0.0,
            'sharpe_classico': 0.0, 'sharpe_geometrico': 0.0,
            'sortino_ratio': 0.0, 'max_drawdown': 0.0, 'calmar_ratio': 0.0,
            'taxa_acerto': 0.0, 'meses_acima_cdi': 0.0
        }
        
    # Retornos Anualizados
    cagr_p = float((1.0 + serie_retornos).prod() ** (1.0 / anos) - 1.0)
    cagr_cdi = float((1.0 + serie_cdi).prod() ** (1.0 / anos) - 1.0)
    ret_aritmetico = float(serie_retornos.mean() * 12.0)
    
    # Volatilidade Anualizada
    vol_anual = float(serie_retornos.std() * np.sqrt(12.0))
    
    # Série de Excesso de Retorno sobre o CDI
    excesso = serie_retornos - serie_cdi
    media_excesso = float(excesso.mean())
    vol_excesso = float(excesso.std() * np.sqrt(12.0))
    
    # 1. Sharpe Clássico (Excesso de Retorno Aritmético Anualizado)
    sharpe_classico = float((media_excesso * 12.0) / vol_excesso) if vol_excesso > 0 else 0.0
    
    # 2. Sharpe Geométrico (Diferença de CAGR dividida pela Volatilidade)
    sharpe_geometrico = float((cagr_p - cagr_cdi) / vol_anual) if vol_anual > 0 else 0.0
    
    # 3. Sortino Ratio (Downside Risk abaixo do CDI)
    desvios_negativos = excesso.clip(upper=0.0)
    downside_vol = float(np.sqrt((desvios_negativos ** 2).mean()) * np.sqrt(12.0))
    sortino = float((media_excesso * 12.0) / downside_vol) if downside_vol > 0 else 0.0
    
    # 4. Máximo Drawdown e Calmar Ratio
    patrimonio = (1.0 + serie_retornos).cumprod()
    picos = patrimonio.cummax()
    drawdowns = (patrimonio - picos) / picos
    max_dd = float(drawdowns.min())
    calmar = float(cagr_p / abs(max_dd)) if max_dd < 0 else 0.0
    
    # 5. Métricas Operacionais de Frequência
    taxa_acerto = float((serie_retornos > 0.0).mean())
    meses_acima_cdi = float((serie_retornos > serie_cdi).mean())
    
    return {
        'ret_anual_cagr': cagr_p,
        'ret_anual_aritmetico': ret_aritmetico,
        'vol_anual': vol_anual,
        'cdi_anual_cagr': cagr_cdi,
        'sharpe_classico': sharpe_classico,
        'sharpe_geometrico': sharpe_geometrico,
        'sortino_ratio': sortino,
        'max_drawdown': max_dd,
        'calmar_ratio': calmar,
        'taxa_acerto': taxa_acerto,
        'meses_acima_cdi': meses_acima_cdi
    }
