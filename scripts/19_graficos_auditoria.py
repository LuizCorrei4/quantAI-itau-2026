"""
Gráficos da Auditoria Metodológica — Robô Nexus

Versões de apresentação (identidade visual do deck) das figuras produzidas pelos
scripts 14 a 18. Os originais em `images/` seguem no estilo padrão do matplotlib
para consumo interno; aqui geramos as peças que entram no PDF de 5 páginas.

Saídas em `images/relatorio/`:
    rel_07_ablacao_variantes.png  Sharpe por variante V0-V6 vs. mediana do nulo
    rel_08_nulo_pareado.png       Distribuição do nulo pareado, V3 no percentil 23
    rel_09_oos_equity.png         Teste cego 2019-2026: a degradação
    rel_10_regime_drawdown.png    Filtro de regime: o que ele corta de drawdown
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Mesmos tokens do deck (oklch convertido para hex).
FUNDO = "#08121F"
CARTAO = "#111D2E"
TEXTO = "#EDEFF1"
TEXTO2 = "#81878D"
ACENTO = "#3DFFA0"
ALERTA = "#FFD447"
PERIGO = "#FF6B6B"
ROXO = "#B18CFF"
NEUTRO = "#5A6472"

ABL = Path("dados/resultados/ablacao")
OOS = Path("dados/resultados/out_of_sample")
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


def sharpe_geometrico(retornos: pd.Series, cdi: pd.Series) -> float:
    """CAGR em excesso sobre o CDI, dividido pela volatilidade anualizada."""
    n = len(retornos)
    cagr = (1 + retornos).prod() ** (12 / n) - 1
    cagr_cdi = (1 + cdi).prod() ** (12 / n) - 1
    vol = retornos.std(ddof=1) * np.sqrt(12)
    return (cagr - cagr_cdi) / vol


def drawdown(retornos: pd.Series) -> pd.Series:
    patrimonio = (1 + retornos).cumprod()
    return patrimonio / patrimonio.cummax() - 1


# =============================================================================
# 1. Ablação: o Sharpe de cada variante contra o nulo
# =============================================================================
def grafico_ablacao() -> None:
    """A leitura mais dura do projeto: a variante sem grafo vence a com grafo.

    As barras saem dos parquets, não da tabela do markdown, para que o gráfico
    não possa divergir do que o script de ablação apurou.
    """
    variantes = [
        ("V1", "MST sozinha\nsem momentum", "V1_mst_sem_momentum"),
        ("V0", "Universo 80\nsem filtro algum", "V0_universo80"),
        ("V2", "MST + momentum\nsem cap", "V2_mst_momentum_sem_cap"),
        ("V6", "Menor beta\n+ momentum + cap", "V6_menor_beta"),
        ("V3", "NEXUS OFICIAL\nMST + momentum + cap", "V3_oficial"),
        ("V5", "Menor correlação\n+ momentum + cap", "V5_menor_correlacao"),
    ]

    rotulos, valores, cores = [], [], []
    for sigla, descricao, arquivo in variantes:
        d = pd.read_parquet(ABL / f"{arquivo}.parquet")
        s = sharpe_geometrico(d["retorno_total"], d["retorno_cdi"])
        rotulos.append(f"{sigla} · {descricao}")
        valores.append(s)
        if sigla == "V3":
            cores.append(ACENTO)
        elif sigla == "V5":
            cores.append(ALERTA)
        else:
            cores.append(NEUTRO)

    nulo = pd.read_parquet(ABL / "V4_nulo_pareado.parquet")["sharpe_geometrico"]
    mediana_nulo = float(nulo.median())

    ordem = np.argsort(valores)
    rotulos = [rotulos[i] for i in ordem]
    valores = [valores[i] for i in ordem]
    cores = [cores[i] for i in ordem]

    fig, ax = plt.subplots(figsize=(11.4, 6.2))
    y = np.arange(len(valores))
    ax.barh(y, valores, color=cores, height=0.66, zorder=3)

    ax.axvline(0, color="#2A3444", lw=1.4, zorder=2)
    ax.axvline(
        mediana_nulo,
        color=PERIGO,
        lw=2.2,
        ls="--",
        zorder=4,
        label=f"Mediana do nulo pareado: {mediana_nulo:+.3f}",
    )

    for i, v in enumerate(valores):
        deslocamento = 0.012 if v >= 0 else -0.012
        ax.text(
            v + deslocamento,
            i,
            f"{v:+.3f}",
            va="center",
            ha="left" if v >= 0 else "right",
            fontsize=15,
            fontweight="bold",
            color=TEXTO,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(rotulos, fontsize=13.5, color=TEXTO)
    ax.set_xlabel("Sharpe geométrico — In-Sample 2011–2018")
    ax.set_title(
        "Cada camada isolada: de onde vem (e de onde não vem) o resultado",
        pad=16,
        loc="left",
    )
    ax.set_xlim(min(valores) - 0.09, max(max(valores), mediana_nulo) + 0.09)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="upper left", fontsize=13.5, labelcolor=TEXTO)

    fig.text(
        0.012,
        -0.035,
        "Sortear 20 ações e aplicar os mesmos filtros (linha vermelha) supera a seleção pela MST.",
        fontsize=13.5,
        color=TEXTO2,
    )
    salvar(fig, "rel_07_ablacao_variantes.png")


# =============================================================================
# 2. Nulo pareado: onde o Nexus cai na distribuição
# =============================================================================
def grafico_nulo_pareado() -> None:
    nulo = pd.read_parquet(ABL / "V4_nulo_pareado.parquet")["sharpe_geometrico"]
    v3 = pd.read_parquet(ABL / "V3_oficial.parquet")
    sharpe_v3 = sharpe_geometrico(v3["retorno_total"], v3["retorno_cdi"])
    percentil = float((nulo < sharpe_v3).mean() * 100)

    fig, ax = plt.subplots(figsize=(11.4, 5.6))
    ax.hist(nulo, bins=26, color="#26374D", edgecolor="#3A4E68", linewidth=0.8, zorder=3)

    ax.axvline(
        float(nulo.median()),
        color=TEXTO2,
        lw=2.0,
        ls="--",
        zorder=5,
        label=f"Mediana dos sorteios: {nulo.median():+.3f}",
    )
    ax.axvline(
        float(nulo.quantile(0.95)),
        color=ALERTA,
        lw=2.0,
        ls=":",
        zorder=5,
        label=f"Percentil 95: {nulo.quantile(0.95):+.3f}",
    )
    ax.axvline(
        sharpe_v3,
        color=ACENTO,
        lw=3.2,
        zorder=6,
        label=f"Nexus (MST): {sharpe_v3:+.3f} — percentil {percentil:.0f}%",
    )

    ax.set_xlabel("Sharpe geométrico — In-Sample 2011–2018")
    ax.set_ylabel("Nº de sorteios")
    ax.set_title(
        "A MST agrega sobre um pool aleatório?",
        pad=44,
        loc="left",
    )
    ax.text(
        0.0,
        1.022,
        "200 pools sorteados do mesmo universo, com o mesmo momentum e o mesmo cap — só a origem do pool muda",
        transform=ax.transAxes,
        fontsize=13.5,
        color=TEXTO2,
    )
    ax.legend(loc="upper left", fontsize=13.5, labelcolor=TEXTO)
    salvar(fig, "rel_08_nulo_pareado.png")


# =============================================================================
# 3. Out-of-sample: a degradação no teste cego
# =============================================================================
def grafico_oos() -> None:
    oficial = pd.read_parquet(OOS / "oos_oficial.parquet").set_index("data")
    regime_v3 = pd.read_parquet(OOS / "oos_oficial_com_regime.parquet").set_index("data")
    v5 = pd.read_parquet(OOS / "oos_menor_correlacao.parquet").set_index("data")
    v5_reg = pd.read_parquet(OOS / "oos_menor_correlacao_com_regime.parquet").set_index("data")
    mercado = pd.read_parquet("dados/resultados/serie_retornos_nexus.parquet")
    bova = mercado["retorno_bova11"].reindex(oficial.index)

    fig, ax = plt.subplots(figsize=(12.0, 6.2))

    series = [
        ((1 + v5_reg["retorno_total"]).cumprod() * 100, "Nexus V5 + Regime MST", "#2CA02C", 3.0, "-"),
        ((1 + v5["retorno_total"]).cumprod() * 100, "Nexus V5 (Menor Corr)", "#1F77B4", 2.2, "--"),
        ((1 + oficial["retorno_cdi"]).cumprod() * 100, "CDI (Benchmark)", ALERTA, 2.4, "--"),
        ((1 + bova.fillna(0)).cumprod() * 100, "BOVA11 (ETF)", NEUTRO, 2.0, "-"),
        ((1 + oficial["retorno_total"]).cumprod() * 100, "Nexus V3 (MST Oficial)", ACENTO, 1.8, "-."),
    ]
    for serie, nome, cor, lw, ls in series:
        ax.plot(serie.index, serie.values, color=cor, lw=lw, ls=ls,
                label=f"{nome} · R$ {serie.iloc[-1]:.0f}", zorder=4)

    ax.set_ylabel("Patrimônio (R$ 100 investidos)")
    ax.set_title(
        "Teste cego 2019–2026: Nexus V5 (Micro-Macro) vs. Nexus V3 vs. Benchmarks",
        pad=16,
        loc="left",
    )
    ax.legend(loc="upper left", fontsize=12.5, labelcolor=TEXTO, ncol=2)

    sharpe_v5_reg = sharpe_geometrico(v5_reg["retorno_total"], v5_reg["retorno_cdi"])
    ax.text(
        0.985,
        0.06,
        f"V5+Regime: Sharpe {sharpe_v5_reg:+.3f} | Vol 19.5%",
        transform=ax.transAxes,
        ha="right",
        fontsize=14.5,
        fontweight="bold",
        color="#2CA02C",
    )
    salvar(fig, "rel_09_oos_equity.png")


# =============================================================================
# 4. Filtro de regime: o que ele entrega é drawdown, não retorno
# =============================================================================
def grafico_regime() -> None:
    v3 = pd.read_parquet(ABL / "V3_oficial.parquet").set_index("data")
    p10 = pd.read_parquet(ABL / "regime_p10_com_cap.parquet").set_index("data")

    dd_v3 = drawdown(v3["retorno_total"]) * 100
    dd_p10 = drawdown(p10["retorno_total"]) * 100

    fig, ax = plt.subplots(figsize=(11.4, 5.2))
    ax.fill_between(dd_v3.index, dd_v3.values, 0, color=PERIGO, alpha=0.30, zorder=3)
    ax.plot(dd_v3.index, dd_v3.values, color=PERIGO, lw=2.2, zorder=4,
            label=f"Sem filtro de regime · mínimo {dd_v3.min():.1f}%")
    ax.plot(dd_p10.index, dd_p10.values, color=ACENTO, lw=2.6, zorder=5,
            label=f"Com filtro de regime (p10) · mínimo {dd_p10.min():.1f}%")

    acionado = p10.index[p10["mult_regime"] < 1.0]
    for i, data in enumerate(acionado):
        ax.axvline(data, color=ALERTA, lw=1.6, alpha=0.55, zorder=2,
                   label="Meses em que o filtro acionou" if i == 0 else None)

    ax.set_ylabel("Drawdown (%)")
    ax.set_title(
        "O filtro de regime é instrumento de risco, não de retorno",
        pad=16,
        loc="left",
    )
    # A curva cruza a região da legenda; um fundo sólido evita ler número sobre linha.
    legenda = ax.legend(loc="lower left", fontsize=13.5, labelcolor=TEXTO, frameon=True)
    legenda.get_frame().set_facecolor(FUNDO)
    legenda.get_frame().set_edgecolor("#2A3444")
    legenda.get_frame().set_alpha(0.94)
    salvar(fig, "rel_10_regime_drawdown.png")


def main() -> None:
    aplicar_estilo()
    grafico_ablacao()
    grafico_nulo_pareado()
    grafico_oos()
    grafico_regime()
    print("\nGráficos da auditoria gerados em images/relatorio/")


if __name__ == "__main__":
    main()
