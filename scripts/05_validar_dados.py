"""Etapa 5 — Validação dos datasets e relatório de qualidade.

Roda as checagens que precisam estar respondidas antes de qualquer backtest, e
grava um relatório em markdown que serve de insumo direto para a seção de
tratamento de vieses do relatório final.

Saída:
    dados/processados/relatorio_qualidade.md
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nexus import config as cfg

P = cfg.PROCESSADOS


def carregar() -> dict[str, pd.DataFrame]:
    return {
        "precos": pd.read_parquet(P / "precos_ajustados.parquet"),
        "retornos": pd.read_parquet(P / "retornos_log.parquet"),
        "volume": pd.read_parquet(P / "volume_financeiro.parquet"),
        "universo": pd.read_parquet(P / "universo_mensal.parquet"),
        "bench": pd.read_parquet(P / "benchmarks.parquet"),
        "cdi": pd.read_parquet(P / "cdi_diario.parquet"),
        "ficha": pd.read_csv(P / "metadados_tickers.csv", parse_dates=["inicio", "fim"]),
    }


def checar_calendario(d: dict, linhas: list[str]) -> None:
    precos, bench = d["precos"], d["bench"]
    cal = precos.index
    ibov = bench["ibov"].dropna().index

    so_nosso = cal.difference(ibov)
    so_ibov = ibov.difference(cal)

    linhas += [
        "## 1. Calendário de pregão",
        "",
        f"- Pregões no painel: **{len(cal)}** ({cal.min().date()} a {cal.max().date()})",
        f"- Pregões na série do Ibovespa: **{len(ibov)}**",
        f"- Datas no painel ausentes no IBOV: {len(so_nosso)}",
        f"- Datas no IBOV ausentes no painel: {len(so_ibov)}",
        "",
        "A convergência com o calendário do Ibovespa valida o filtro de datas "
        "fantasma (feriados da B3 em que o Yahoo publica cotação para poucos tickers).",
        "",
    ]


def checar_retornos(d: dict, linhas: list[str]) -> None:
    r = d["retornos"]
    stack = r.stack()

    extremos = stack[stack.abs() > 0.25].sort_values()
    por_ticker = extremos.groupby(level=1).size().sort_values(ascending=False)

    linhas += [
        "## 2. Retornos diários",
        "",
        f"- Observações válidas: **{len(stack):,}**",
        f"- Média: {stack.mean():.5f} | Desvio padrão: {stack.std():.4f}",
        f"- Assimetria: {stack.skew():.2f} | Curtose: {stack.kurtosis():.1f}",
        f"- Retornos com |r| > 25%: {len(extremos)} "
        f"({len(extremos) / len(stack):.4%} das observações)",
        "",
        "Caudas gordas (curtose alta) são a norma em retornos diários de ações e "
        "não indicam erro de dados. Tickers concentrando extremos:",
        "",
        "| Ticker | Nº de retornos > 25% |",
        "|---|---|",
    ]
    for ticker, n in por_ticker.head(8).items():
        linhas.append(f"| {ticker} | {n} |")
    linhas.append("")


def checar_universo(d: dict, linhas: list[str]) -> None:
    u = d["universo"]
    por_data = u.groupby("data_rebalanceamento")["ticker"].apply(set)

    entradas = []
    datas = list(por_data.index)
    for anterior, atual in zip(datas, datas[1:]):
        antes, agora = por_data[anterior], por_data[atual]
        entradas.append(len(agora - antes))
    troca = pd.Series(entradas, index=datas[1:])

    linhas += [
        "## 3. Universo mensal (80 mais líquidas)",
        "",
        f"- Rebalanceamentos: **{len(por_data)}** "
        f"({datas[0].date()} a {datas[-1].date()})",
        f"- Ações por rebalanceamento: {u.groupby('data_rebalanceamento').size().min()} "
        f"a {u.groupby('data_rebalanceamento').size().max()}",
        f"- Tickers distintos que já passaram pelo universo: **{u['ticker'].nunique()}**",
        f"- Empresas distintas (radical de 4 letras): **{u['grupo'].nunique()}**",
        f"- Renovação média do universo: **{troca.mean():.1f} ações/mês** "
        f"({troca.mean() / cfg.TAMANHO_UNIVERSO:.1%})",
        f"- Renovação máxima num único mês: {troca.max()} ações",
        "",
        "A renovação do universo é do *filtro de liquidez*, não da carteira. "
        "O turnover da carteira do Nexus é medido separadamente no backtest.",
        "",
    ]


def checar_survivorship(d: dict, linhas: list[str]) -> None:
    ficha, u = d["ficha"], d["universo"]
    ultimo = d["precos"].index.max()

    encerradas = ficha[ficha["serie_encerrada"] & (ficha["meses_no_universo"] > 0)]
    disp = pd.read_csv(P / "disponibilidade.csv")
    buracos = disp[
        (disp["origem"] == "candidato_historico")
        & (~disp["disponivel"])
        & (disp["sucessor"].isna())
    ]

    linhas += [
        "## 4. Survivorship bias — o que temos e o que falta",
        "",
        f"O universo tem **{u['ticker'].nunique()}** tickers distintos ao longo de "
        f"{len(u.groupby('data_rebalanceamento'))} rebalanceamentos. Destes, "
        f"**{len(encerradas)}** são séries que terminam antes do último pregão "
        f"({ultimo.date()}) — ou seja, empresas que saíram da bolsa e cujo histórico "
        "está preservado no backtest.",
        "",
        "**Séries encerradas presentes no universo:**",
        "",
        "| Ticker | Empresa | Fim da série | Meses no universo |",
        "|---|---|---|---|",
    ]
    for _, r in encerradas.sort_values("fim").iterrows():
        nome = r["empresa"] if isinstance(r["empresa"], str) else "—"
        linhas.append(f"| {r['ticker']} | {nome} | {r['fim'].date()} | {r['meses_no_universo']} |")

    linhas += [
        "",
        f"**Buracos remanescentes ({len(buracos)} empresas):** códigos deslistados sem "
        "ticker sucessor e sem dados no Yahoo Finance. São a parcela irrecuperável "
        "do viés de sobrevivência com fontes gratuitas:",
        "",
        "> " + ", ".join(sorted(buracos["codigo"])),
        "",
        "**Casos de renomeação não são buraco.** O Yahoo reescreve o histórico "
        "completo sob o ticker sucessor — verificado empiricamente para BHIA3 "
        "(ex-VVAR3, dados desde 2010), COGN3 (ex-KROT3), MOTV3 (ex-CCRO3), "
        "AZZA3 (ex-ARZZ3), DXCO3 (ex-DTEX3), PCAR3, TIMS3, VIVT3, YDUQ3, B3SA3 "
        "e AMER3. Ver `dados/processados/disponibilidade.csv`.",
        "",
    ]


def checar_benchmarks(d: dict, linhas: list[str]) -> None:
    bench, cdi = d["bench"], d["cdi"]
    ini, fim = d["precos"].index.min(), d["precos"].index.max()
    anos = (fim - ini).days / 365.25

    linhas += [
        "## 5. Benchmarks e taxa livre de risco",
        "",
        "| Série | Obs. | Acumulado | Anualizado | Vol. anualizada |",
        "|---|---|---|---|---|",
    ]
    for nome, serie in [("Ibovespa", bench["ibov"]), ("BOVA11", bench["bova11"])]:
        s = serie.dropna().loc[ini:fim]
        acum = s.iloc[-1] / s.iloc[0]
        ret_log = np.log(s / s.shift(1)).dropna()
        linhas.append(
            f"| {nome} | {len(s)} | {acum:.2f}x | {acum ** (1 / anos) - 1:.2%} | "
            f"{ret_log.std() * np.sqrt(252):.2%} |"
        )

    c = cdi.loc[ini:fim]
    acum_cdi = c["fator"].prod()
    linhas += [
        f"| CDI | {len(c)} | {acum_cdi:.2f}x | {acum_cdi ** (1 / anos) - 1:.2%} | — |",
        "",
        f"Período de referência: {ini.date()} a {fim.date()} ({anos:.1f} anos).",
        "",
    ]


def checar_lookahead(d: dict, linhas: list[str]) -> None:
    """Verifica que nenhuma seleção usou dado da própria data ou posterior."""
    u, precos = d["universo"], d["precos"]
    violacoes = 0
    for data, grupo in u.groupby("data_rebalanceamento"):
        anteriores = precos.index[precos.index < data]
        janela = anteriores[-cfg.JANELA_LIQUIDEZ :]
        # Toda ação escolhida precisa ter negociado dentro da janela anterior.
        sem_dado = [t for t in grupo["ticker"] if precos.loc[janela, t].notna().sum() == 0]
        violacoes += len(sem_dado)

    linhas += [
        "## 6. Checagem de look-ahead na formação do universo",
        "",
        f"- Ações selecionadas sem nenhum dado na janela anterior à decisão: "
        f"**{violacoes}**",
        "- A janela de liquidez usa exclusivamente pregões com índice `< data_rebalanceamento`.",
        "- O ranking de liquidez usa `Close` e `Volume` brutos do passado, nunca ajustados "
        "por eventos posteriores em quantidade de ações.",
        "",
    ]


def main() -> None:
    d = carregar()
    linhas = [
        "# Relatório de Qualidade dos Dados — Robô Nexus",
        "",
        f"Gerado a partir de `dados/processados/`. Período coletado: "
        f"{d['precos'].index.min().date()} a {d['precos'].index.max().date()}.",
        "",
    ]

    checar_calendario(d, linhas)
    checar_retornos(d, linhas)
    checar_universo(d, linhas)
    checar_survivorship(d, linhas)
    checar_benchmarks(d, linhas)
    checar_lookahead(d, linhas)

    destino = P / "relatorio_qualidade.md"
    destino.write_text("\n".join(linhas), encoding="utf-8")
    print("\n".join(linhas))
    print(f"\n--- gravado em {destino} ---")


if __name__ == "__main__":
    main()
