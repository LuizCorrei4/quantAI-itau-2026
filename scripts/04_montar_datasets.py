"""Etapa 4 — Montagem dos datasets limpos que alimentam o backtest.

Três decisões metodológicas ficam registradas aqui, porque são justamente as
que a banca vai querer ver explicitadas:

1. RETORNOS vêm do `Adj Close` (ajustado por proventos e desdobramentos);
   LIQUIDEZ vem de `Close` bruto x `Volume` bruto. Misturar os dois inflaria o
   volume financeiro do passado pelo fator de ajuste acumulado.

2. O universo mensal é reconstruído com janela ESTRITAMENTE ANTERIOR à data de
   rebalanceamento. Na data t só entram pregões com índice < t. Nenhuma
   informação de t ou depois participa da escolha das ações de t.

3. Ações da mesma empresa (PETR3/PETR4, ITUB3/ITUB4, units) são deduplicadas
   pelo radical de 4 letras, mantendo a classe mais líquida. Sem isso a MST
   ganharia pares de correlação ~0,98 que são a mesma empresa, distorcendo
   completamente a topologia da rede e a medida de centralidade.

Saídas em dados/processados/:
    precos_ajustados.parquet    painel data x ticker
    retornos_log.parquet        painel data x ticker
    volume_financeiro.parquet   painel data x ticker (R$)
    cdi_diario.parquet          taxa e fator diário
    benchmarks.parquet          ibov, bova11 e seus retornos log
    universo_mensal.parquet     ações elegíveis por data de rebalanceamento
    metadados_tickers.csv       ficha de cada ticker
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nexus import config as cfg

# Retorno diário acima disso quase sempre é erro de ajuste, não evento real.
LIMITE_RETORNO_SUSPEITO = 0.60

# Um pregão de verdade tem cotação para boa parte do universo. O Yahoo insere
# cotações fantasma em feriados da B3 (Carnaval, 12/10, 20/11, 24/12...) para um
# punhado de tickers; se essas datas entrarem no calendário, elas viram o
# "último dia da janela" e derrubam a elegibilidade do universo inteiro.
FRACAO_MINIMA_PREGAO = 0.25


def carregar_painel() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    painel = pd.read_parquet(cfg.BRUTOS / "precos_ohlcv.parquet")
    ajustado = painel["Adj Close"].sort_index()
    fechamento = painel["Close"].sort_index()
    volume = painel["Volume"].sort_index()
    return ajustado, fechamento, volume


def calendario_pregao(ajustado: pd.DataFrame) -> pd.DatetimeIndex:
    """Datas com cotação para fração relevante do universo."""
    cobertura = ajustado.notna().sum(axis=1)
    corte = max(20, FRACAO_MINIMA_PREGAO * cobertura.median())
    validas = cobertura[cobertura >= corte].index
    descartadas = len(cobertura) - len(validas)
    print(f"  corte de {corte:.0f} ativos/dia -> {descartadas} datas fantasma descartadas")
    return pd.DatetimeIndex(validas)


def radical(ticker: str) -> str:
    """Radical de 4 letras que identifica a empresa na B3 (PETR4 -> PETR)."""
    achado = re.match(r"^([A-Z]{4})", ticker)
    return achado.group(1) if achado else ticker


def limpar_precos(ajustado: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Remove tickers curtos demais e neutraliza retornos absurdos."""
    validos = ajustado.notna().sum()
    ajustado = ajustado.loc[:, validos >= cfg.MIN_OBS_TICKER]

    # Preço não-positivo não existe; vira ausência.
    ajustado = ajustado.where(ajustado > 0)

    retornos = np.log(ajustado / ajustado.shift(1))

    suspeitos = retornos.abs() > LIMITE_RETORNO_SUSPEITO
    n_suspeitos = int(suspeitos.to_numpy().sum())
    if n_suspeitos:
        print(f"  {n_suspeitos} retornos diários acima de "
              f"{LIMITE_RETORNO_SUSPEITO:.0%} marcados como ausentes")
    retornos = retornos.where(~suspeitos)

    return ajustado, retornos


def datas_rebalanceamento(indice: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Primeiro pregão efetivo de cada mês."""
    serie = pd.Series(indice, index=indice)
    primeiros = serie.groupby([indice.year, indice.month]).min()
    return pd.DatetimeIndex(sorted(primeiros.values))


def montar_universo_mensal(
    volume_fin: pd.DataFrame, ajustado: pd.DataFrame
) -> pd.DataFrame:
    """Para cada rebalanceamento, as N ações mais líquidas elegíveis.

    Usa apenas pregões anteriores à data de rebalanceamento.
    """
    rebals = datas_rebalanceamento(ajustado.index)
    linhas = []

    for data in rebals:
        anteriores = ajustado.index[ajustado.index < data]
        if len(anteriores) < cfg.JANELA_LIQUIDEZ:
            continue
        janela = anteriores[-cfg.JANELA_LIQUIDEZ :]

        precos_janela = ajustado.loc[janela]
        cobertura = precos_janela.notna().mean()
        # Negociou perto da data de decisão — tolera 1 ou 2 pregões sem negócio.
        tem_preco_recente = precos_janela.tail(5).notna().any()
        liquidez = volume_fin.loc[janela].median(skipna=True)

        elegivel = (
            (cobertura >= cfg.COBERTURA_MINIMA) & tem_preco_recente & (liquidez > 0)
        )
        candidatos = liquidez[elegivel].dropna().sort_values(ascending=False)
        if candidatos.empty:
            continue

        # Uma classe por empresa: fica a mais líquida.
        df = candidatos.rename("liquidez").reset_index()
        df.columns = ["ticker", "liquidez"]
        df["grupo"] = df["ticker"].map(radical)
        df = df.drop_duplicates(subset="grupo", keep="first")

        escolhidos = df.head(cfg.TAMANHO_UNIVERSO).copy()
        escolhidos["data_rebalanceamento"] = data
        escolhidos["rank_liquidez"] = range(1, len(escolhidos) + 1)
        linhas.append(escolhidos)

    universo = pd.concat(linhas, ignore_index=True)
    return universo[["data_rebalanceamento", "ticker", "grupo", "rank_liquidez", "liquidez"]]


def montar_benchmarks() -> pd.DataFrame:
    bench = pd.read_csv(cfg.BRUTOS / "benchmarks.csv", parse_dates=["data"]).set_index("data")
    for col in list(bench.columns):
        bench[f"ret_{col}"] = np.log(bench[col] / bench[col].shift(1))
    return bench


def montar_cdi() -> pd.DataFrame:
    cdi = pd.read_csv(cfg.BRUTOS / "cdi_sgs12.csv", parse_dates=["data"]).set_index("data")
    cdi["ret_log_cdi"] = np.log(cdi["fator"])
    return cdi


def ficha_tickers(
    ajustado: pd.DataFrame, volume_fin: pd.DataFrame, universo: pd.DataFrame
) -> pd.DataFrame:
    disp = pd.read_csv(cfg.PROCESSADOS / "disponibilidade.csv")
    meses_no_universo = universo.groupby("ticker").size().rename("meses_no_universo")

    ficha = pd.DataFrame(
        {
            "ticker": ajustado.columns,
            "grupo": [radical(t) for t in ajustado.columns],
            "n_obs": ajustado.notna().sum().values,
            "inicio": [ajustado[t].dropna().index.min() for t in ajustado.columns],
            "fim": [ajustado[t].dropna().index.max() for t in ajustado.columns],
            "liquidez_mediana": volume_fin.median(skipna=True).reindex(ajustado.columns).values,
        }
    )
    ficha = ficha.merge(
        disp[["codigo", "empresa", "origem", "motivo_saida", "sucessor"]],
        left_on="ticker",
        right_on="codigo",
        how="left",
    ).drop(columns="codigo")
    ficha = ficha.merge(meses_no_universo, on="ticker", how="left")
    ficha["meses_no_universo"] = ficha["meses_no_universo"].fillna(0).astype(int)

    ultimo_pregao = ajustado.index.max()
    ficha["serie_encerrada"] = ficha["fim"] < ultimo_pregao - pd.Timedelta(days=30)
    return ficha.sort_values("liquidez_mediana", ascending=False)


def main() -> None:
    print("[1/5] Carregando painel bruto")
    ajustado, fechamento, volume = carregar_painel()
    print(f"  {ajustado.shape[0]} datas x {ajustado.shape[1]} tickers")

    calendario = calendario_pregao(ajustado)
    ajustado = ajustado.loc[calendario]
    fechamento = fechamento.reindex(calendario)
    volume = volume.reindex(calendario)
    print(f"  calendário final: {len(calendario)} pregões "
          f"({calendario.min().date()} a {calendario.max().date()})")

    print("\n[2/5] Limpando preços e calculando retornos log")
    ajustado, retornos = limpar_precos(ajustado)
    print(f"  {ajustado.shape[1]} tickers após filtro de histórico mínimo")

    print("\n[3/5] Volume financeiro (Close bruto x Volume bruto)")
    colunas = ajustado.columns
    volume_fin = (fechamento[colunas] * volume[colunas]).reindex(index=ajustado.index)
    print(f"  mediana global: R$ {volume_fin.stack().median():,.0f}/dia por ativo")

    print("\n[4/5] Universo mensal por liquidez (janela estritamente anterior)")
    universo = montar_universo_mensal(volume_fin, ajustado)
    por_data = universo.groupby("data_rebalanceamento").size()
    print(f"  {len(por_data)} rebalanceamentos | "
          f"{por_data.min()} a {por_data.max()} ações (mediana {int(por_data.median())})")
    print(f"  primeiro: {por_data.index.min().date()} | último: {por_data.index.max().date()}")

    print("\n[5/5] Benchmarks, CDI e metadados")
    bench = montar_benchmarks()
    cdi = montar_cdi()
    ficha = ficha_tickers(ajustado, volume_fin, universo)

    ajustado.to_parquet(cfg.PROCESSADOS / "precos_ajustados.parquet")
    retornos.to_parquet(cfg.PROCESSADOS / "retornos_log.parquet")
    volume_fin.to_parquet(cfg.PROCESSADOS / "volume_financeiro.parquet")
    universo.to_parquet(cfg.PROCESSADOS / "universo_mensal.parquet")
    bench.to_parquet(cfg.PROCESSADOS / "benchmarks.parquet")
    cdi.to_parquet(cfg.PROCESSADOS / "cdi_diario.parquet")
    ficha.to_csv(cfg.PROCESSADOS / "metadados_tickers.csv", index=False)

    print("\nArquivos gravados em dados/processados/:")
    for p in sorted(cfg.PROCESSADOS.glob("*")):
        print(f"  {p.name:30s} {p.stat().st_size / 1024:8.1f} KB")


if __name__ == "__main__":
    main()
