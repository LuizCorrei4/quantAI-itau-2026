"""Etapa 1 — Construção do universo de tickers e teste de disponibilidade.

Junta (a) as carteiras teóricas vigentes dos índices da B3 e (b) a lista de
candidatos históricos, e submete cada código ao yfinance para descobrir
empiricamente o que existe. O resultado alimenta a etapa de coleta e é a base
factual da discussão de survivorship bias no relatório.

Saídas:
    dados/brutos/b3_carteiras.csv          carteiras vigentes por índice
    dados/brutos/universo_candidatos.csv   todos os códigos testados
    dados/processados/disponibilidade.csv  o que o yfinance devolve por código
"""

from __future__ import annotations

import sys
import time
import urllib3
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nexus import config as cfg
from nexus.b3 import carteira_indice
from nexus.historicos import candidatos_historicos

urllib3.disable_warnings()

INDICES = ["IBOV", "IBXX", "IBRA", "SMLL", "IGCX"]
LOTE = 25


def coletar_carteiras() -> pd.DataFrame:
    partes = []
    for indice in INDICES:
        try:
            df = carteira_indice(indice)
            print(f"  {indice}: {len(df)} ativos")
            partes.append(df)
        except Exception as exc:  # noqa: BLE001 - índice indisponível não é fatal
            print(f"  {indice}: FALHOU ({type(exc).__name__}: {exc})")
    if not partes:
        raise RuntimeError("Nenhuma carteira da B3 pôde ser obtida.")
    return pd.concat(partes, ignore_index=True)


def testar_disponibilidade(codigos: list[str]) -> pd.DataFrame:
    """Baixa uma amostra de cada ticker e registra o que o Yahoo devolve."""
    linhas = []
    for i in range(0, len(codigos), LOTE):
        lote = codigos[i : i + LOTE]
        simbolos = [c + cfg.SUFIXO_B3 for c in lote]
        print(f"  lote {i // LOTE + 1}/{-(-len(codigos) // LOTE)} ({len(lote)} tickers)")
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
        except Exception as exc:  # noqa: BLE001
            print(f"    lote falhou: {type(exc).__name__}: {exc}")
            dados = pd.DataFrame()

        for codigo, simbolo in zip(lote, simbolos):
            serie = pd.Series(dtype="float64")
            if not dados.empty:
                try:
                    serie = dados["Adj Close"][simbolo].dropna()
                except (KeyError, TypeError):
                    serie = pd.Series(dtype="float64")
            linhas.append(
                {
                    "codigo": codigo,
                    "n_obs": int(len(serie)),
                    "inicio": serie.index.min().date() if len(serie) else None,
                    "fim": serie.index.max().date() if len(serie) else None,
                    "disponivel": len(serie) >= cfg.MIN_OBS_TICKER,
                }
            )
        time.sleep(1.0)
    return pd.DataFrame(linhas)


def main() -> None:
    print("[1/3] Carteiras teóricas vigentes da B3")
    carteiras = coletar_carteiras()
    carteiras.to_csv(cfg.BRUTOS / "b3_carteiras.csv", index=False)

    atuais = (
        carteiras.groupby("codigo")
        .agg(empresa=("empresa", "first"), indices=("indice", lambda s: "|".join(sorted(set(s)))))
        .reset_index()
    )
    atuais["origem"] = "indice_vigente"
    atuais["motivo_saida"] = None
    atuais["sucessor"] = None

    historicos = candidatos_historicos()
    historicos["indices"] = None
    historicos["origem"] = "candidato_historico"

    candidatos = pd.concat(
        [atuais, historicos[["codigo", "empresa", "indices", "origem", "motivo_saida", "sucessor"]]],
        ignore_index=True,
    ).drop_duplicates(subset="codigo", keep="first")

    candidatos.to_csv(cfg.BRUTOS / "universo_candidatos.csv", index=False)
    print(
        f"  {len(atuais)} de índices vigentes + {len(historicos)} históricos "
        f"= {len(candidatos)} códigos únicos"
    )

    print("\n[2/3] Testando disponibilidade no yfinance")
    disp = testar_disponibilidade(sorted(candidatos["codigo"]))

    print("\n[3/3] Consolidando")
    resultado = candidatos.merge(disp, on="codigo", how="left")
    resultado = resultado.sort_values(["disponivel", "codigo"], ascending=[False, True])
    resultado.to_csv(cfg.PROCESSADOS / "disponibilidade.csv", index=False)

    resumo = resultado.groupby(["origem", "disponivel"]).size().unstack(fill_value=0)
    print("\n" + resumo.to_string())
    print(f"\nTotal disponível: {int(resultado['disponivel'].sum())} de {len(resultado)}")


if __name__ == "__main__":
    main()
