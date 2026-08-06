"""Etapa 2 — Download dos preços e volumes das ações do universo.

Baixa com `auto_adjust=False` de propósito: precisamos das duas versões do
preço. O `Adj Close` (ajustado por proventos e desdobramentos) é o que gera
retornos economicamente corretos; o `Close` bruto multiplicado pelo `Volume`
bruto é o que gera volume financeiro em reais fiel ao que de fato girou no
pregão — usar preço ajustado aqui distorceria a liquidez do passado.

Saída:
    dados/brutos/precos_ohlcv.parquet   painel (data x ticker x campo)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nexus import config as cfg

LOTE = 20
CAMPOS = ["Adj Close", "Close", "Volume"]
TENTATIVAS = 3


def baixar_lote(simbolos: list[str]) -> pd.DataFrame:
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            dados = yf.download(
                simbolos,
                start=cfg.INICIO_COLETA,
                end=cfg.FIM_COLETA,
                auto_adjust=False,
                actions=False,
                progress=False,
                threads=False,
                group_by="column",
            )
            if not dados.empty:
                return dados
        except Exception as exc:  # noqa: BLE001
            print(f"    tentativa {tentativa} falhou: {type(exc).__name__}: {exc}")
        time.sleep(3 * tentativa)
    return pd.DataFrame()


def main() -> None:
    disp = pd.read_csv(cfg.PROCESSADOS / "disponibilidade.csv")
    codigos = sorted(disp.loc[disp["disponivel"], "codigo"])
    print(f"Baixando {len(codigos)} tickers de {cfg.INICIO_COLETA} a {cfg.FIM_COLETA}")

    partes = []
    for i in range(0, len(codigos), LOTE):
        lote = codigos[i : i + LOTE]
        simbolos = [c + cfg.SUFIXO_B3 for c in lote]
        n_lotes = -(-len(codigos) // LOTE)
        print(f"  lote {i // LOTE + 1}/{n_lotes}")

        dados = baixar_lote(simbolos)
        if dados.empty:
            print("    lote vazio, seguindo")
            continue

        for campo in CAMPOS:
            if campo not in dados.columns.get_level_values(0):
                continue
            bloco = dados[campo].copy()
            if isinstance(bloco, pd.Series):  # lote de 1 ticker
                bloco = bloco.to_frame(simbolos[0])
            bloco = bloco.rename(columns=lambda s: s.replace(cfg.SUFIXO_B3, ""))
            bloco = bloco.stack().rename("valor").reset_index()
            bloco.columns = ["data", "ticker", "valor"]
            bloco["campo"] = campo
            partes.append(bloco)
        time.sleep(1.0)

    longo = pd.concat(partes, ignore_index=True)
    longo = longo.dropna(subset=["valor"])
    longo["data"] = pd.to_datetime(longo["data"])

    painel = longo.pivot_table(
        index="data", columns=["campo", "ticker"], values="valor", aggfunc="last"
    ).sort_index()

    painel.to_parquet(cfg.BRUTOS / "precos_ohlcv.parquet")
    print(
        f"\nSalvo: {painel.shape[0]} pregões x "
        f"{painel['Adj Close'].shape[1]} tickers -> dados/brutos/precos_ohlcv.parquet"
    )
    print(f"Período: {painel.index.min().date()} a {painel.index.max().date()}")


if __name__ == "__main__":
    main()
