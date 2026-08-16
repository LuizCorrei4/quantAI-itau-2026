"""
===============================================================================
PROJETO NEXUS - DESAFIO ITAÚ ASSET QUANT AI 2026
Motor de Simulação Compartilhado (Ablação, Nulos e Out-of-Sample)
Arquivo: src/nexus/motor.py
===============================================================================

POR QUE ESTE MÓDULO EXISTE:
---------------------------
Os scripts 08, 09, 10 e 13 reimplementam, cada um, o mesmo loop mensal de
backtest. Isso já produziu divergências entre relatórios (contagem de meses,
tratamento do cap nos nulos). Este módulo centraliza o loop em UM caminho de
código, e cada experimento vira apenas uma escolha de:

  1. SELETOR   - de onde vem o pool de candidatas (MST, aleatório, beta, ...)
  2. FILTRO    - aplica ou não o momentum (SMA de L dias)
  3. CAP       - teto por ativo (o excedente vira caixa em CDI)
  4. REGIME    - multiplicador de exposição vindo da contração da MST

Assim, "MST + momentum + cap" e "pool aleatório + momentum + cap" diferem em
exatamente UMA linha, que é a condição para a comparação ser interpretável.

CONVENÇÕES TEMPORAIS (idênticas às do backtest oficial):
--------------------------------------------------------
- Toda informação usada na decisão do mês T vem estritamente de datas < T.
- A posição é assumida no fechamento do primeiro pregão do mês (data T).
- O retorno é apurado de T até T+1 (próximo rebalanceamento).

DEFEITO CONHECIDO QUE ESTE MÓDULO CORRIGE:
------------------------------------------
`portfolio.calcular_turnover` devolve 1.0 sempre que a carteira anterior está
vazia (`pesos_antigos.empty`). Quando a estratégia passa dois meses seguidos
100% em CDI, isso cobra custo de giro de uma carteira que não negociou. Aqui
usamos `calcular_turnover_corrigido`, que trata caixa->caixa como giro zero.
A função original NÃO foi alterada para não mudar retroativamente os números
já publicados em docs/03 a docs/11 (ver TICKET-C07).
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from . import config
from .alpha_filters import filtro_momentum
from .mst import (
    calcular_distancia_media_mst,
    calcular_farness,
    calcular_matriz_correlacao,
    construir_mst,
    correlacao_para_distancia,
)
from .portfolio import (
    apurar_retorno_periodo,
    calcular_pesos_equal_weight,
    selecionar_top_n,
)


# =============================================================================
# 1. CARGA DE DADOS
# =============================================================================

@dataclass
class Bases:
    """Painéis de mercado carregados uma única vez e compartilhados."""
    universo: pd.DataFrame
    retornos: pd.DataFrame
    precos: pd.DataFrame
    cdi: pd.DataFrame
    benchmarks: pd.DataFrame


def carregar_bases() -> Bases:
    """Lê os painéis processados de `dados/processados/`."""
    return Bases(
        universo=pd.read_parquet(config.PROCESSADOS / "universo_mensal.parquet"),
        retornos=pd.read_parquet(config.PROCESSADOS / "retornos_log.parquet"),
        precos=pd.read_parquet(config.PROCESSADOS / "precos_ajustados.parquet"),
        cdi=pd.read_parquet(config.PROCESSADOS / "cdi_diario.parquet"),
        benchmarks=pd.read_parquet(config.PROCESSADOS / "benchmarks.parquet"),
    )


def datas_do_periodo(
    universo: pd.DataFrame,
    inicio: Optional[str] = None,
    fim: Optional[str] = None,
) -> List[pd.Timestamp]:
    """
    Lista ordenada das datas de rebalanceamento dentro de [inicio, fim].

    A última data serve apenas como fechamento do período final: o número de
    meses de retorno é len(datas) - 1.
    """
    datas = sorted(universo["data_rebalanceamento"].unique())
    if inicio is not None:
        datas = [d for d in datas if d >= pd.Timestamp(inicio)]
    if fim is not None:
        datas = [d for d in datas if d <= pd.Timestamp(fim)]
    return list(datas)


# =============================================================================
# 2. CONTEXTO MENSAL (calculado uma vez, reaproveitado por todas as variantes)
# =============================================================================

@dataclass
class ContextoMes:
    """
    Tudo que é conhecido na data de decisão T, calculado com dados < T.

    Construir a MST é a etapa cara do backtest. Como todas as variantes da
    ablação compartilham o mesmo mês, o contexto é montado uma única vez.
    """
    data: pd.Timestamp
    data_prox: pd.Timestamp
    ativos: List[str]
    farness: pd.Series          # maior = mais periférico
    corr_media: pd.Series       # correlação média com as demais (controle sem grafo)
    beta: pd.Series             # beta vs. Ibovespa   (controle sem grafo)
    dist_media: float           # distância média das arestas da MST (regime)
    ret_cdi: float              # retorno do CDI em [T, T+1]
    precos_janela: pd.DataFrame  # últimos `max_L` pregões estritamente < T


def _retorno_cdi(cdi: pd.DataFrame, data: pd.Timestamp, data_prox: pd.Timestamp) -> float:
    i0 = cdi.index.get_indexer([data], method="pad")[0]
    i1 = cdi.index.get_indexer([data_prox], method="pad")[0]
    return float(cdi["cdi_acumulado"].iloc[i1] / cdi["cdi_acumulado"].iloc[i0] - 1.0)


def construir_contextos(
    bases: Bases,
    datas: List[pd.Timestamp],
    max_L: int = 200,
    verbose: bool = True,
) -> List[ContextoMes]:
    """
    Monta o contexto de cada mês do período.

    Args:
        max_L: maior janela de média móvel que será testada. A janela de preços
               guardada tem esse tamanho; `filtro_momentum` faz `.tail(L)` dentro.
    """
    contextos: List[ContextoMes] = []
    ret_ibov_full = bases.benchmarks["ret_ibov"]

    for i, data in enumerate(datas[:-1]):
        data_prox = datas[i + 1]
        ativos = bases.universo.loc[
            bases.universo["data_rebalanceamento"] == data, "ticker"
        ].tolist()

        # --- Janela de retornos: estritamente anterior a T ---
        idx_ret = bases.retornos.index[bases.retornos.index < data][-config.JANELA_CORRELACAO:]
        ret_hist = bases.retornos.loc[idx_ret, ativos]

        # --- Topologia ---
        corr = calcular_matriz_correlacao(ret_hist)
        dist = correlacao_para_distancia(corr)
        mst = construir_mst(dist)
        farness = calcular_farness(mst)
        dist_media = calcular_distancia_media_mst(mst)

        # --- Controle sem grafo 1: correlação média de cada ativo ---
        n = len(corr)
        corr_media = (corr.sum(axis=1) - 1.0) / max(n - 1, 1)

        # --- Controle sem grafo 2: beta vs. Ibovespa na mesma janela ---
        ret_ibov = ret_ibov_full.reindex(idx_ret)
        var_m = float(ret_ibov.var())
        if var_m > 0:
            beta = ret_hist.apply(lambda col: col.cov(ret_ibov) / var_m)
        else:
            beta = pd.Series(np.nan, index=ret_hist.columns)

        # --- Janela de preços para os filtros de momentum ---
        idx_pre = bases.precos.index[bases.precos.index < data][-max_L:]
        precos_janela = bases.precos.loc[idx_pre]

        contextos.append(
            ContextoMes(
                data=data,
                data_prox=data_prox,
                ativos=ativos,
                farness=farness,
                corr_media=corr_media,
                beta=beta,
                dist_media=dist_media,
                ret_cdi=_retorno_cdi(bases.cdi, data, data_prox),
                precos_janela=precos_janela,
            )
        )

        if verbose and (i + 1) % 24 == 0:
            print(f"    contexto: {i + 1}/{len(datas) - 1} meses")

    return contextos


# =============================================================================
# 3. SELETORES DE POOL ("onde olhar")
# =============================================================================

Seletor = Callable[[ContextoMes], List[str]]


def pool_mst(n: int) -> Seletor:
    """Top-N mais periféricas da MST (maior farness)."""
    return lambda ctx: selecionar_top_n(ctx.farness, n=n)


def pool_universo() -> Seletor:
    """Universo inteiro (piso de mercado equal-weight)."""
    return lambda ctx: list(ctx.ativos)


def pool_menor_correlacao(n: int) -> Seletor:
    """Controle sem grafo: N ativos de menor correlação média."""
    return lambda ctx: ctx.corr_media.nsmallest(n).index.tolist()


def pool_menor_beta(n: int) -> Seletor:
    """Controle sem grafo: N ativos de menor |beta| vs. Ibovespa."""
    return lambda ctx: ctx.beta.abs().nsmallest(n).index.tolist()


def pool_aleatorio(n: int, rng: np.random.Generator) -> Seletor:
    """Nulo pareado: N ativos sorteados do mesmo universo elegível."""
    def _seletor(ctx: ContextoMes) -> List[str]:
        k = min(n, len(ctx.ativos))
        return list(rng.choice(np.array(ctx.ativos, dtype=object), size=k, replace=False))
    return _seletor


# =============================================================================
# 4. TURNOVER CORRIGIDO
# =============================================================================

def calcular_turnover_corrigido(
    pesos_antigos: Optional[pd.Series], pesos_novos: pd.Series
) -> float:
    """
    Turnover = (1/2) * soma(|peso_novo - peso_antigo|).

    O custo aplicado sobre ele é `turnover * custo_por_perna * 2`, o que equivale a
    cobrar `custo_por_perna` sobre cada unidade de peso efetivamente negociada.
    A conta fecha nos dois extremos:

      - troca total de uma carteira 100% investida:
        soma|dw| = 2.0 -> turnover 1.0 -> custo = 2 pernas (vende tudo, compra tudo)
      - saída de caixa para 100% investido:
        soma|dw| = 1.0 -> turnover 0.5 -> custo = 1 perna (só compra)

    DUAS DIFERENÇAS vs. `portfolio.calcular_turnover` (ver TICKET-C07):

      1. Caixa -> caixa devolve 0.0, e não 1.0. Cobrar corretagem de uma carteira
         que ficou parada em CDI é custo fantasma — e a estratégia oficial passa
         vários meses seguidos 100% em caixa (warmup da SMA e meses sem aprovadas).
      2. Caixa -> investido devolve 0.5, e não 1.0. A função original cobra duas
         pernas onde só houve a perna de compra.

    A função original NÃO foi alterada, para não mudar retroativamente os números
    já publicados em docs/03 a docs/11.
    """
    if pesos_antigos is None:
        pesos_antigos = pd.Series(dtype=float)

    if len(pesos_antigos) == 0 and len(pesos_novos) == 0:
        return 0.0

    # A fórmula geral já cobre os casos de borda: o lado ausente entra como zero.
    df = pd.DataFrame(
        {"novo": pesos_novos, "antigo": pesos_antigos}, dtype=float
    ).fillna(0.0)
    return float((df["novo"] - df["antigo"]).abs().sum() / 2.0)


# =============================================================================
# 5. LOOP DE SIMULAÇÃO
# =============================================================================

def simular(
    contextos: List[ContextoMes],
    precos: pd.DataFrame,
    seletor: Seletor,
    aplicar_momentum: bool = True,
    L: int = 150,
    cap: Optional[float] = config.CAP_POR_ATIVO,
    custo_por_perna: float = config.CUSTO_POR_OPERACAO,
    multiplicadores_regime: Optional[pd.Series] = None,
) -> pd.DataFrame:
    """
    Executa uma variante do backtest sobre contextos já construídos.

    Args:
        seletor: função que devolve o pool de candidatas do mês.
        aplicar_momentum: se False, compra o pool inteiro (isola a seleção).
        cap: teto por ativo. `None` renormaliza para 100% investido (isola o
             efeito do colchão de caixa).
        multiplicadores_regime: série indexada por data com o multiplicador de
             exposição do filtro de regime. `None` desliga a camada.

    Returns:
        DataFrame mensal com retorno, alocação, giro e nº de posições.
    """
    linhas: List[Dict[str, Any]] = []
    pesos_ant: Optional[pd.Series] = None

    for ctx in contextos:
        pool = seletor(ctx)

        if aplicar_momentum:
            aprovadas = filtro_momentum(ctx.precos_janela, pool, L=L)
        else:
            aprovadas = [t for t in pool if t in ctx.precos_janela.columns]

        pesos = calcular_pesos_equal_weight(aprovadas, cap=cap)

        # Camada de regime: encolhe a exposição total, mantendo os pesos relativos
        mult = 1.0
        if multiplicadores_regime is not None:
            mult = float(multiplicadores_regime.get(ctx.data, 1.0))
            if len(pesos) > 0:
                pesos = pesos * mult

        turnover = calcular_turnover_corrigido(pesos_ant, pesos)
        custo = turnover * (custo_por_perna * 2.0)

        ret_acoes = (
            apurar_retorno_periodo(precos, aprovadas, ctx.data, ctx.data_prox)
            if len(aprovadas) > 0
            else 0.0
        )

        aloc_acoes = float(pesos.sum()) if len(pesos) > 0 else 0.0
        aloc_caixa = 1.0 - aloc_acoes
        ret_total = (ret_acoes * aloc_acoes) + (ctx.ret_cdi * aloc_caixa) - custo

        linhas.append(
            {
                "data": ctx.data,
                "retorno_total": ret_total,
                "retorno_cdi": ctx.ret_cdi,
                "n_acoes": len(aprovadas),
                "pct_acoes": aloc_acoes * 100.0,
                "pct_cdi": aloc_caixa * 100.0,
                "turnover": turnover,
                "mult_regime": mult,
                "dist_media_mst": ctx.dist_media,
            }
        )
        pesos_ant = pesos

    return pd.DataFrame(linhas)


def serie_retornos(df: pd.DataFrame) -> pd.Series:
    """Extrai a série de retornos mensais de uma saída de `simular`."""
    return df["retorno_total"].reset_index(drop=True)


def serie_cdi(df: pd.DataFrame) -> pd.Series:
    """Extrai a série do CDI de uma saída de `simular`."""
    return df["retorno_cdi"].reset_index(drop=True)
