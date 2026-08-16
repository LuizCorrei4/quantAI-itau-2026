"""
Gráficos do Relatório Final — Robô Nexus

Regera as figuras que entram no PDF de 5 páginas já na identidade visual do
Nexus (fundo escuro, acento neon), para que gráfico e slide sejam a mesma peça
de design. Os gráficos técnicos dos scripts 07 a 13 continuam existindo em
`images/` no estilo padrão do matplotlib para consumo interno; aqui produzimos
as versões de apresentação em `images/relatorio/`.

Saídas:
    rel_01_mst_comparativa.png   MST em mercado calmo vs. crash da COVID
    rel_02_equity_insample.png   Curva de equity In-Sample (Momentum / ML / Cascata / CDI)
    rel_03_montecarlo.png        Distribuição dos 200 macacos vs. Nexus
    rel_04_custos.png            Sensibilidade a custos e ponto de break-even
    rel_05_drawdown.png          Drawdown: Nexus vs. MVP puro vs. Ibovespa
    rel_06_alocacao.png          Alocação Ações vs. CDI (mecanismo do CAP de 10%)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from src.nexus import config
from src.nexus.mst import (
    calcular_matriz_correlacao,
    construir_mst,
    correlacao_para_distancia,
)
from src.nexus.portfolio import (
    apurar_retorno_periodo,
    calcular_pesos_equal_weight,
    calcular_turnover,
    descontar_custos,
)

# -----------------------------------------------------------------------------
# Identidade visual (mesmos tokens do deck, convertidos de oklch para hex)
# -----------------------------------------------------------------------------
FUNDO = "#08121F"       # fundo primário das páginas
CARTAO = "#111D2E"      # fundo de cartões/painéis
TEXTO = "#EDEFF1"       # texto primário
TEXTO2 = "#81878D"      # texto secundário, eixos
ARESTA = "#8B9095"      # arestas do grafo, grade
CENTRAL = "#464E58"     # nós centrais (sistêmicos)
ACENTO = "#3DFFA0"      # nós periféricos, a estratégia
ALERTA = "#FFD447"      # atenção, limiares
PERIGO = "#FF6B6B"      # crise, perda
ROXO = "#B18CFF"        # camada de ML

SAIDA = Path("images/relatorio")
SAIDA.mkdir(parents=True, exist_ok=True)


def aplicar_estilo() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": FUNDO,
            "axes.facecolor": FUNDO,
            "savefig.facecolor": FUNDO,
            "text.color": TEXTO,
            "axes.labelcolor": TEXTO2,
            "axes.edgecolor": "#2A3444",
            "xtick.color": TEXTO2,
            "ytick.color": TEXTO2,
            "grid.color": "#1E2938",
            "grid.linewidth": 0.9,
            "axes.grid": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.family": "DejaVu Sans",
            "font.size": 15,
            "axes.titlesize": 19,
            "axes.titleweight": "bold",
            "legend.frameon": False,
            "figure.dpi": 200,
        }
    )


def salvar(fig, nome: str) -> None:
    caminho = SAIDA / nome
    fig.savefig(caminho, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print(f"[+] {caminho}")


# =============================================================================
# 1. MST comparativa: mercado calmo vs. crash
# =============================================================================
DATA_CALMA = pd.Timestamp("2017-06-01")
DATA_CRISE = pd.Timestamp("2020-04-01")
TOP_PERIFERIA = 10


def _mst_do_mes(retornos, universo, data):
    """Reproduz exatamente a camada 1 do robô para uma data de rebalanceamento."""
    tickers = universo.loc[
        universo["data_rebalanceamento"] == data, "ticker"
    ].tolist()
    janela = retornos.loc[retornos.index < data, tickers].tail(config.JANELA_CORRELACAO)

    corr = calcular_matriz_correlacao(janela)
    dist = correlacao_para_distancia(corr)
    mst = construir_mst(dist)

    # Farness = soma das distâncias de caminho mínimo até todos os outros nós.
    caminhos = dict(nx.all_pairs_dijkstra_path_length(mst, weight="weight"))
    farness = pd.Series({no: sum(d.values()) for no, d in caminhos.items()})

    # Correlação média fora da diagonal — o termômetro sistêmico.
    triangulo = corr.values[np.triu_indices_from(corr.values, k=1)]
    return mst, farness, float(triangulo.mean())


def _rotulos_sem_colisao(ax, pos, nos, deslocamento=0.062, minimo=0.060):
    """Posiciona os tickers abaixo de cada nó, empurrando quem colidir.

    Sem isso os rótulos da periferia se sobrepõem justamente nos meses de crise,
    que é quando as ações periféricas se aglomeram no mesmo canto da árvore.
    """
    alvos = []
    for no in sorted(nos, key=lambda n: (-pos[n][1], pos[n][0])):
        x, y = pos[no][0], pos[no][1] - deslocamento
        for xa, ya in alvos:
            if abs(x - xa) < 0.24 and abs(y - ya) < minimo:
                y = ya - minimo
        alvos.append((x, y))
        ax.text(
            x, y, no, ha="center", va="top", color=ACENTO,
            fontsize=10.5, family="DejaVu Sans", fontweight="bold", zorder=6,
            # A caixa escura evita que o ticker suma quando cai em cima de
            # outro nó verde — verde sobre verde é ilegível.
            bbox=dict(boxstyle="round,pad=0.20", facecolor=FUNDO, edgecolor="none", alpha=0.88),
        )


def grafico_mst_comparativa():
    retornos = pd.read_parquet(config.PROCESSADOS / "retornos_log.parquet")
    universo = pd.read_parquet(config.PROCESSADOS / "universo_mensal.parquet")

    fig, eixos = plt.subplots(1, 2, figsize=(16, 7.2))

    painéis = [
        (eixos[0], DATA_CALMA, "MERCADO CALMO", "jun/2017"),
        (eixos[1], DATA_CRISE, "CRASH DA COVID", "abr/2020"),
    ]

    for ax, data, titulo, legenda_data in painéis:
        mst, farness, rho_medio = _mst_do_mes(retornos, universo, data)
        periferia = set(farness.nlargest(TOP_PERIFERIA).index)
        centro = set(farness.nsmallest(8).index)

        pos = nx.kamada_kawai_layout(mst, weight="weight")

        nx.draw_networkx_edges(
            mst, pos, ax=ax, edge_color=ARESTA, width=0.9, alpha=0.30
        )

        # Nós comuns
        comuns = [n for n in mst.nodes if n not in periferia and n not in centro]
        nx.draw_networkx_nodes(
            mst, pos, nodelist=comuns, ax=ax,
            node_color=TEXTO2, node_size=55, alpha=0.55, linewidths=0,
        )
        # Núcleo sistêmico
        nx.draw_networkx_nodes(
            mst, pos, nodelist=sorted(centro), ax=ax,
            node_color=CENTRAL, node_size=170, linewidths=0,
        )
        # Periferia selecionada — halo + miolo
        peri = sorted(periferia)
        for tamanho, alpha in ((620, 0.10), (400, 0.18), (250, 0.30)):
            nx.draw_networkx_nodes(
                mst, pos, nodelist=peri, ax=ax,
                node_color=ACENTO, node_size=tamanho, alpha=alpha, linewidths=0,
            )
        nx.draw_networkx_nodes(
            mst, pos, nodelist=peri, ax=ax,
            node_color=ACENTO, node_size=150, linewidths=0,
        )
        _rotulos_sem_colisao(ax, pos, peri)

        comprimento = float(
            np.mean([d["weight"] for *_, d in mst.edges(data=True)])
        )

        ax.set_title(f"{titulo}   ·   {legenda_data}", color=TEXTO, pad=22, fontsize=20)
        ax.text(
            0.5, -0.02,
            f"correlação média  ρ = {rho_medio:.2f}          aresta média = {comprimento:.2f}",
            transform=ax.transAxes, ha="center", va="top",
            color=TEXTO2, fontsize=15, family="DejaVu Sans",
        )
        ax.margins(0.07)
        ax.set_axis_off()

    fig.text(
        0.5, 1.045,
        "A MESMA REDE, DOIS REGIMES — 80 AÇÕES, 79 ARESTAS",
        ha="center", color=TEXTO, fontsize=22, fontweight="bold",
    )
    fig.text(
        0.5, 1.005,
        "Verde: as 10 ações de maior Farness, compradas no mês.      Cinza-escuro: o núcleo sistêmico, sempre evitado.",
        ha="center", color=TEXTO2, fontsize=15,
    )
    fig.subplots_adjust(top=0.93, bottom=0.05, wspace=0.02)
    salvar(fig, "rel_01_mst_comparativa.png")


# =============================================================================
# 2. Curva de equity In-Sample
# =============================================================================
def _carregar_batalha(nome: str) -> pd.DataFrame:
    df = pd.read_parquet(config.RESULTADOS / "cv_temporal" / f"serie_retornos_batalha_{nome}.parquet")
    return df.set_index(pd.to_datetime(df["data"]))


def grafico_equity():
    mom = _carregar_batalha("Momentum_Puro")
    ml = _carregar_batalha("ML_Puro")
    casc = _carregar_batalha("Cascata")

    series = [
        ("Nexus · Momentum SMA 150", mom["retorno_total"], ACENTO, 3.4, "-"),
        ("Cascata com ML", casc["retorno_total"], ROXO, 2.0, "-"),
        ("ML puro (walk-forward)", ml["retorno_total"], PERIGO, 2.0, "-"),
        ("CDI", mom["retorno_cdi"], TEXTO2, 2.0, "--"),
    ]

    fig, ax = plt.subplots(figsize=(12.5, 6.6))
    for rotulo, ret, cor, lw, ls in series:
        equity = 100 * (1 + ret).cumprod()
        equity = pd.concat([pd.Series([100.0], index=[mom.index[0]]), equity])
        ax.plot(equity.index, equity.values, color=cor, lw=lw, ls=ls, label=rotulo,
                solid_capstyle="round")
        ax.annotate(
            f"R$ {equity.iloc[-1]:.0f}",
            xy=(equity.index[-1], equity.iloc[-1]),
            xytext=(10, 0), textcoords="offset points",
            color=cor, fontsize=15, fontweight="bold", va="center",
        )

    ax.set_title("R$ 100 investidos — In-Sample 2011–2018", color=TEXTO, loc="left", pad=14)
    ax.set_ylabel("patrimônio (R$)")
    ax.legend(loc="upper left", fontsize=14, labelcolor=TEXTO2)
    ax.margins(x=0.12)
    salvar(fig, "rel_02_equity_insample.png")


# =============================================================================
# 3. Monte Carlo — 200 macacos
# =============================================================================
N_SIMULACOES = 200
CARTEIRA_MACACO = 10
SHARPE_NEXUS = 0.122


def _sharpe_geometrico(ret: pd.Series, cdi: pd.Series) -> float:
    anos = len(ret) / 12
    if anos == 0:
        return 0.0
    cagr = (1 + ret).prod() ** (1 / anos) - 1
    cagr_cdi = (1 + cdi).prod() ** (1 / anos) - 1
    vol = ret.std() * np.sqrt(12)
    return 0.0 if vol == 0 else (cagr - cagr_cdi) / vol


def _simular_macacos() -> np.ndarray:
    universo = pd.read_parquet(config.PROCESSADOS / "universo_mensal.parquet")
    precos = pd.read_parquet(config.PROCESSADOS / "precos_ajustados.parquet")
    cdi = pd.read_parquet(config.PROCESSADOS / "cdi_diario.parquet")

    datas = [d for d in sorted(universo["data_rebalanceamento"].unique())
             if d <= pd.Timestamp("2018-12-31")]

    sharpes = []
    for sim in range(N_SIMULACOES):
        np.random.seed(sim + 42)
        rets, cdis, pesos_ant = [], [], None

        for i, data in enumerate(datas[:-1]):
            prox = datas[i + 1]
            elegiveis = universo.loc[
                universo["data_rebalanceamento"] == data, "ticker"
            ].tolist()
            escolhidas = list(np.random.choice(elegiveis, size=CARTEIRA_MACACO, replace=False))

            pesos = calcular_pesos_equal_weight(escolhidas)
            giro = calcular_turnover(pesos_ant, pesos)
            bruto = apurar_retorno_periodo(precos, escolhidas, data, prox)
            rets.append(descontar_custos(bruto, giro, config.CUSTO_POR_OPERACAO))

            ini = cdi.index.get_indexer([data], method="pad")[0]
            fim = cdi.index.get_indexer([prox], method="pad")[0]
            cdis.append(cdi["cdi_acumulado"].iloc[fim] / cdi["cdi_acumulado"].iloc[ini] - 1)

            pesos_ant = pesos

        sharpes.append(_sharpe_geometrico(pd.Series(rets), pd.Series(cdis)))
        if (sim + 1) % 50 == 0:
            print(f"    macacos: {sim + 1}/{N_SIMULACOES}")

    return np.array(sharpes)


def grafico_montecarlo():
    print("  simulando 200 carteiras aleatórias...")
    sharpes = _simular_macacos()
    media = sharpes.mean()
    p95 = np.percentile(sharpes, 95)
    p_value = float(np.mean(sharpes >= SHARPE_NEXUS))

    print(f"    média={media:.3f}  p95={p95:.3f}  p-value={p_value:.1%}")

    fig, ax = plt.subplots(figsize=(12.5, 6.0))
    ax.hist(sharpes, bins=28, color="#243349", edgecolor="#33445E", linewidth=1.0)

    ax.axvline(media, color=TEXTO2, ls="--", lw=2)
    ax.axvline(p95, color=ALERTA, ls=":", lw=2.4)
    for lw, alpha in ((9, 0.12), (5, 0.22)):
        ax.axvline(SHARPE_NEXUS, color=ACENTO, lw=lw, alpha=alpha)
    ax.axvline(SHARPE_NEXUS, color=ACENTO, lw=2.8)

    topo = ax.get_ylim()[1]
    ax.annotate(f"acaso\n{media:.2f}", xy=(media, topo * 0.97), color=TEXTO2,
                fontsize=14, ha="center", va="top")
    ax.annotate(f"barreira 95%\n{p95:.3f}", xy=(p95, topo * 0.62), xytext=(-16, 0),
                textcoords="offset points", color=ALERTA, fontsize=14,
                ha="right", va="center")
    ax.annotate(f"NEXUS\n{SHARPE_NEXUS:.3f}", xy=(SHARPE_NEXUS, topo * 0.97),
                xytext=(14, 0), textcoords="offset points", color=ACENTO,
                fontsize=15, fontweight="bold", ha="left", va="top")

    ax.set_title("Sharpe de 200 carteiras aleatórias no mesmo universo e com os mesmos custos",
                 color=TEXTO, loc="left", pad=14, fontsize=17)
    ax.set_xlabel("Sharpe geométrico · In-Sample 2011–2018")
    ax.set_ylabel("nº de simulações")
    ax.text(0.5, -0.235,
            f"O Nexus supera {(1 - p_value) * 100:.1f}% do acaso  ·  p-value = {p_value:.1%}",
            transform=ax.transAxes, ha="center", color=TEXTO, fontsize=16, fontweight="bold")
    salvar(fig, "rel_03_montecarlo.png")


# =============================================================================
# 4. Sensibilidade a custos
# =============================================================================
def grafico_custos():
    df = pd.read_csv(config.RESULTADOS / "sensibilidade_custos_transacao.csv")

    fig, ax = plt.subplots(figsize=(12.5, 6.0))
    ax.axhline(0, color=TEXTO2, lw=1.2, alpha=0.7)

    ax.plot(df["custo_bps_perna"], df["sharpe_mom_geom"], color=ACENTO, lw=3.4,
            marker="o", ms=7, label="Nexus · Momentum SMA 150")
    ax.plot(df["custo_bps_perna"], df["sharpe_cascata_geom"], color=ROXO, lw=2.2,
            marker="o", ms=6, label="Cascata com ML")

    # Zona de operação institucional realista (4 a 8 bps por perna)
    ax.axvspan(4, 8, color=ACENTO, alpha=0.09)
    ax.text(6, ax.get_ylim()[1] * 0.92, "custo real\n4–8 bps", color=ACENTO,
            fontsize=13.5, ha="center", va="top")

    ax.axvline(16.0, color=ALERTA, ls=":", lw=2.2)
    ax.annotate("break-even\n16 bps/perna", xy=(16.0, 0), xytext=(10, 26),
                textcoords="offset points", color=ALERTA, fontsize=14)

    ax.set_title("Quanto de atrito a estratégia aguenta antes de perder do CDI",
                 color=TEXTO, loc="left", pad=14, fontsize=17)
    ax.set_xlabel("custo de transação (bps por perna)")
    ax.set_ylabel("Sharpe geométrico")
    ax.legend(loc="lower left", fontsize=14, labelcolor=TEXTO2)
    salvar(fig, "rel_04_custos.png")


# =============================================================================
# 5. Alocação Ações vs. CDI — o CAP de 10% em ação
# =============================================================================
def grafico_alocacao():
    # As colunas pct_* já vêm gravadas em pontos percentuais (0–100).
    mom = _carregar_batalha("Momentum_Puro")

    fig, ax = plt.subplots(figsize=(12.5, 5.0))
    ax.fill_between(mom.index, 0, mom["pct_acoes"], color=ACENTO, alpha=0.80,
                    label="ações periféricas em tendência", linewidth=0)
    ax.fill_between(mom.index, mom["pct_acoes"], 100, color="#2E4260",
                    label="CDI · colchão automático do CAP de 10%", linewidth=0)

    ax.set_ylim(0, 100)
    ax.set_title(
        f"Quando falta tendência, o capital recua sozinho para o CDI "
        f"— média de {mom['pct_cdi'].mean():.1f}%",
        color=TEXTO, loc="left", pad=14, fontsize=17,
    )
    ax.set_ylabel("% do patrimônio")
    ax.legend(loc="lower left", fontsize=13.5, labelcolor=TEXTO2, ncols=2)
    ax.grid(visible=False)
    salvar(fig, "rel_06_alocacao.png")


# =============================================================================
# 6. Drawdown: o preço de não ter filtro direcional
# =============================================================================
def _drawdown(retornos: pd.Series) -> pd.Series:
    equity = (1 + retornos).cumprod()
    return equity / equity.cummax() - 1


def grafico_drawdown():
    mom = _carregar_batalha("Momentum_Puro")
    mvp = pd.read_parquet(config.RESULTADOS / "serie_retornos_nexus.parquet")
    mvp = mvp.loc[mvp.index <= mom.index.max()]

    curvas = [
        ("Nexus · MST + Momentum + CAP", _drawdown(mom["retorno_total"]), ACENTO, 3.2),
        ("MVP topológico puro (sem filtro direcional)", _drawdown(mvp["retorno_liquido"]), PERIGO, 2.2),
        ("Ibovespa", _drawdown(mvp["retorno_ibov"]), TEXTO2, 1.8),
    ]

    fig, ax = plt.subplots(figsize=(12.5, 5.6))
    for rotulo, dd, cor, lw in curvas:
        ax.fill_between(dd.index, dd.values * 100, 0, color=cor, alpha=0.13, linewidth=0)
        ax.plot(dd.index, dd.values * 100, color=cor, lw=lw,
                label=f"{rotulo}   ({dd.min() * 100:.1f}%)")

    ax.set_title("Profundidade das perdas — In-Sample 2011–2018",
                 color=TEXTO, loc="left", pad=14, fontsize=17)
    ax.set_ylabel("drawdown (%)")
    ax.legend(loc="lower left", fontsize=13.5, labelcolor=TEXTO2)
    ax.grid(axis="x", visible=False)
    salvar(fig, "rel_05_drawdown.png")


def main():
    aplicar_estilo()
    print("=== GRÁFICOS DO RELATÓRIO FINAL ===")
    grafico_mst_comparativa()
    grafico_equity()
    grafico_custos()
    grafico_drawdown()
    grafico_alocacao()
    grafico_montecarlo()
    print("\nConcluído.")


if __name__ == "__main__":
    main()
