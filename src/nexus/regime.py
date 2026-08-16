"""
===============================================================================
PROJETO NEXUS - DESAFIO ITAÚ ASSET QUANT AI 2026
Filtro de Regime Topológico (Camada 4)
Arquivo: src/nexus/regime.py
===============================================================================

TESE DA CAMADA:
---------------
A MST se contrai em crashes e se expande em mercados calmos (Onnela et al., 2003).
Quando a distância média das arestas cai abaixo de um limiar histórico, o mercado
entrou em regime de correlação alta — o momento exato em que a diversificação
deixa de funcionar. A resposta é reduzir exposição em ações e migrar para o CDI.

Confirmado nos dados do projeto: a correlação média entre as 80 ações fica entre
0,10 e 0,22 em períodos normais e sobe para 0,595 em maio de 2020.

ESCOPO DELIBERADAMENTE MÍNIMO (ver TICKET-C05):
-----------------------------------------------
Um único parâmetro: o percentil de corte. A escada de três degraus descrita em
`docs/04` exigiria calibrar dois percentis sobre ~91 meses de amostra — superfície
de overfitting grande demais para o retorno esperado.

ZERO LOOK-AHEAD:
----------------
O limiar do mês T é o percentil da distribuição de distâncias observadas
ESTRITAMENTE ATÉ T-1. Nunca da série inteira. Calcular o percentil sobre todo o
histórico e aplicá-lo retroativamente é o erro clássico desta camada: em 2011 o
modelo estaria usando um limiar que só foi conhecido em 2026.

LIMITAÇÃO ESTRUTURAL A DECLARAR NO RELATÓRIO:
---------------------------------------------
A distância média vem de uma janela trailing de 63 pregões e é avaliada uma vez
por mês. Num crash que se desenvolve em dias (março de 2020), o filtro reage
DEPOIS do estrago. Ele protege contra crises que se arrastam, não contra choques
súbitos. `medir_atraso_reacao` quantifica esse atraso em vez de escondê-lo.
===============================================================================
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd


def serie_distancia_media(contextos) -> pd.Series:
    """
    Extrai a série mensal de distância média da MST a partir dos contextos.

    Args:
        contextos: lista de `motor.ContextoMes`.

    Returns:
        Série indexada pela data de rebalanceamento.
    """
    return pd.Series(
        {ctx.data: ctx.dist_media for ctx in contextos}, dtype=float
    ).sort_index()


def calcular_multiplicadores(
    dist_media: pd.Series,
    percentil: float,
    exposicao_crise: float = 0.30,
    min_historico: int = 24,
) -> pd.Series:
    """
    Multiplicador de exposição em ações, mês a mês.

    Regra:
        limiar(T) = percentil P da distribuição de dist_media em [0, T-1]
        se dist_media(T) < limiar(T)  ->  exposicao_crise  (defesa)
        senão                          ->  1.0             (normal)

    Enquanto houver menos de `min_historico` observações passadas, o filtro se
    abstém (multiplicador 1.0): um percentil estimado com 6 pontos não é um
    percentil, é ruído.

    Args:
        dist_media: série indexada por data (saída de `serie_distancia_media`).
        percentil: corte em [0, 100]. Menor = mais tolerante, aciona menos.
        exposicao_crise: fração da exposição mantida em ações durante a defesa.
        min_historico: mínimo de meses passados para o filtro começar a operar.

    Returns:
        Série de multiplicadores indexada pelas mesmas datas.
    """
    valores = dist_media.to_numpy(dtype=float)
    multiplicadores: Dict[pd.Timestamp, float] = {}

    for i, data in enumerate(dist_media.index):
        if i < min_historico:
            multiplicadores[data] = 1.0
            continue

        # Percentil calculado ESTRITAMENTE sobre o passado: valores[:i]
        limiar = float(np.percentile(valores[:i], percentil))
        multiplicadores[data] = (
            float(exposicao_crise) if valores[i] < limiar else 1.0
        )

    return pd.Series(multiplicadores, dtype=float).sort_index()


def resumo_acionamento(multiplicadores: pd.Series) -> Dict[str, float]:
    """Estatísticas descritivas de quanto o filtro atuou."""
    acionado = multiplicadores < 1.0
    return {
        "meses_totais": int(len(multiplicadores)),
        "meses_acionado": int(acionado.sum()),
        "pct_meses_acionado": float(acionado.mean() * 100.0),
        "exposicao_media": float(multiplicadores.mean()),
    }


def medir_atraso_reacao(
    multiplicadores: pd.Series,
    retornos_estrategia: pd.Series,
    datas: pd.Series,
    janela_crise: tuple,
) -> Dict[str, object]:
    """
    Quantifica o atraso do filtro em uma crise específica.

    Compara o mês em que a crise começou (primeiro retorno fortemente negativo
    dentro da janela) com o mês em que o filtro efetivamente cortou exposição.

    Args:
        multiplicadores: saída de `calcular_multiplicadores`.
        retornos_estrategia: retornos mensais da estratégia.
        datas: série de datas alinhada a `retornos_estrategia`.
        janela_crise: par ('2020-01-01', '2020-12-31').

    Returns:
        Dicionário com o mês do choque, o mês da reação e o atraso em meses.
    """
    inicio, fim = pd.Timestamp(janela_crise[0]), pd.Timestamp(janela_crise[1])

    df = pd.DataFrame(
        {"data": pd.to_datetime(datas.values), "retorno": retornos_estrategia.values}
    )
    janela = df[(df["data"] >= inicio) & (df["data"] <= fim)]
    if janela.empty:
        return {"mes_choque": None, "mes_reacao": None, "atraso_meses": None}

    mes_choque = janela.loc[janela["retorno"].idxmin(), "data"]

    mult_janela = multiplicadores[
        (multiplicadores.index >= inicio) & (multiplicadores.index <= fim)
    ]
    acionados = mult_janela[mult_janela < 1.0]
    mes_reacao = acionados.index[0] if len(acionados) > 0 else None

    if mes_reacao is None:
        atraso = None
    else:
        atraso = int(
            round((mes_reacao - mes_choque).days / 30.44)
        )

    return {
        "mes_choque": mes_choque,
        "mes_reacao": mes_reacao,
        "atraso_meses": atraso,
    }
