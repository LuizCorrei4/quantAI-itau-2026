"""Etapa 3 — Taxa livre de risco (CDI) e benchmark de mercado (Ibovespa).

O CDI vem da série 12 do SGS/BCB, publicada como taxa percentual ao dia. É a
taxa efetiva do dia, então o fator de capitalização é (1 + taxa/100) — não há
conversão de base anual envolvida.

O Ibovespa vem do Yahoo (^BVSP). Atenção: é o índice de preços, que já embute
os proventos das ações componentes (o IBOV é um índice de retorno total desde
sempre), mas não é investível diretamente; o BOVA11 seria o proxy investível.
Coletamos os dois para permitir comparação honesta no relatório.

Saídas:
    dados/brutos/cdi_sgs12.csv
    dados/brutos/benchmarks.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nexus import config as cfg

URL_SGS = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados"
    "?formato=json&dataInicial={inicio}&dataFinal={fim}"
)


def _trecho_sgs(serie: int, inicio: pd.Timestamp, fim: pd.Timestamp) -> pd.DataFrame:
    url = URL_SGS.format(
        serie=serie, inicio=inicio.strftime("%d/%m/%Y"), fim=fim.strftime("%d/%m/%Y")
    )
    resposta = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    resposta.raise_for_status()
    return pd.DataFrame(resposta.json())


def baixar_cdi() -> pd.DataFrame:
    # O SGS recusa (HTTP 406) janelas longas em séries diárias, então fatiamos
    # em blocos de 5 anos e concatenamos.
    inicio = pd.Timestamp(cfg.INICIO_COLETA)
    fim = pd.Timestamp(cfg.FIM_COLETA)

    blocos = []
    cursor = inicio
    while cursor < fim:
        limite = min(cursor + pd.DateOffset(years=5), fim)
        print(f"  bloco {cursor.date()} -> {limite.date()}")
        blocos.append(_trecho_sgs(cfg.SGS_CDI, cursor, limite))
        cursor = limite + pd.Timedelta(days=1)

    df = pd.concat(blocos, ignore_index=True)

    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df = df.drop_duplicates(subset="data").sort_values("data")
    df["cdi_dia_pct"] = df["valor"].astype(float)
    df["fator"] = 1 + df["cdi_dia_pct"] / 100
    df["cdi_acumulado"] = df["fator"].cumprod()
    return df[["data", "cdi_dia_pct", "fator", "cdi_acumulado"]].set_index("data")


def baixar_benchmarks() -> pd.DataFrame:
    simbolos = [cfg.TICKER_IBOV, "BOVA11" + cfg.SUFIXO_B3]
    dados = yf.download(
        simbolos,
        start=cfg.INICIO_COLETA,
        end=cfg.FIM_COLETA,
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=False,
    )
    fechamento = dados["Adj Close"].rename(
        columns={cfg.TICKER_IBOV: "ibov", "BOVA11" + cfg.SUFIXO_B3: "bova11"}
    )
    fechamento.index.name = "data"
    return fechamento


def main() -> None:
    print("[1/2] CDI (SGS série 12)")
    cdi = baixar_cdi()
    cdi.to_csv(cfg.BRUTOS / "cdi_sgs12.csv")
    anos = (cdi.index.max() - cdi.index.min()).days / 365.25
    aa = cdi["cdi_acumulado"].iloc[-1] ** (1 / anos) - 1
    print(f"  {len(cdi)} dias úteis | {cdi.index.min().date()} a {cdi.index.max().date()}")
    print(f"  acumulado no período: {cdi['cdi_acumulado'].iloc[-1]:.3f}x ({aa:.2%} a.a.)")

    print("\n[2/2] Benchmarks (^BVSP, BOVA11)")
    bench = baixar_benchmarks()
    bench.to_csv(cfg.BRUTOS / "benchmarks.csv")
    for col in bench.columns:
        serie = bench[col].dropna()
        print(f"  {col}: {len(serie)} obs | {serie.index.min().date()} a {serie.index.max().date()}")


if __name__ == "__main__":
    main()
