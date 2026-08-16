"""
===============================================================================
PROJETO NEXUS - DESAFIO ITAÚ ASSET QUANT AI 2026
TICKET-C03 - Tabela de Atribuição por Camada (Ablação)
Arquivo: scripts/14_ablacao_atribuicao.py
===============================================================================

A PERGUNTA QUE ESTE SCRIPT RESPONDE:
------------------------------------
O Sharpe de +0.122 do Robô Nexus vem da topologia da MST, do filtro de momentum,
ou do colchão de caixa criado pelo cap de 10%? As três camadas foram introduzidas
juntas e medidas juntas — nunca separadas.

O plano-mestre (Parte 2.5.4) classifica este teste como "o teste mais importante
do projeto para o critério de Conceito (20%)":

    "Esta é a pergunta que a banca vai fazer: por que precisa de grafo? Se um
     cálculo trivial produzir a mesma carteira, a MST é enfeite."

AS 7 VARIANTES (todas in-sample, parâmetros idênticos):
-------------------------------------------------------
  V0  universo 80, sem momentum, sem cap    -> piso de mercado
  V1  MST top-20, sem momentum, cap 10%     -> topologia pura
  V2  MST top-20, momentum, SEM cap         -> momentum sem colchão de caixa
  V3  MST top-20, momentum, cap 10%         -> VARIANTE OFICIAL
  V4  20 aleatórias x 200 sorteios, mom+cap -> NULO PAREADO (contribuição da MST)
  V5  menor correlação média, mom+cap       -> controle sem grafo
  V6  menor |beta| vs IBOV, mom+cap         -> controle sem grafo

AS TRÊS LEITURAS:
-----------------
  V3 - V4  =  contribuição da MST          (o teste central)
  V3 - V2  =  contribuição do colchão de caixa
  V3 - V1  =  contribuição do momentum

SAÍDAS:
-------
  dados/resultados/ablacao/*.parquet
  images/08_ablacao_distribuicao_nulo.png
  images/09_ablacao_equity_variantes.png
  docs/12_ablacao_e_atribuicao.md
===============================================================================
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.nexus import config, motor
from src.nexus.portfolio import calcular_metricas_institucionais

# ---------------------------------------------------------------------------
# Parâmetros travados (idênticos aos da variante oficial)
# ---------------------------------------------------------------------------
POOL_SIZE = 20
L_MOMENTUM = 150
CAP = config.CAP_POR_ATIVO
N_SORTEIOS_NULO = 200
FIM_IN_SAMPLE = "2018-12-31"

IMG_DIR = Path("images")
OUT_DIR = Path("dados/resultados/ablacao")
IMG_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)


def metricas_de(df: pd.DataFrame) -> dict:
    """Métricas institucionais + estatísticas operacionais de uma variante."""
    m = calcular_metricas_institucionais(motor.serie_retornos(df), motor.serie_cdi(df))
    m["turnover_medio"] = float(df["turnover"].mean())
    m["pct_cdi_medio"] = float(df["pct_cdi"].mean())
    m["n_acoes_medio"] = float(df["n_acoes"].mean())
    return m


def linha_tabela(nome: str, descricao: str, m: dict) -> str:
    return (
        f"| **{nome}** | {descricao} | {m['ret_anual_cagr']*100:.1f}% | "
        f"{m['vol_anual']*100:.1f}% | **{m['sharpe_geometrico']:+.3f}** | "
        f"{m['sharpe_classico']:+.3f} | {m['max_drawdown']*100:.1f}% | "
        f"{m['n_acoes_medio']:.1f} | {m['pct_cdi_medio']:.1f}% | "
        f"{m['turnover_medio']*100:.1f}% |\n"
    )


def main() -> None:
    print("=" * 78)
    print("  TICKET-C03 - ABLAÇÃO POR CAMADA (IN-SAMPLE)")
    print("=" * 78)

    # -----------------------------------------------------------------------
    # 1. Contextos mensais (MST calculada uma única vez por mês)
    # -----------------------------------------------------------------------
    print("\n[1/5] Carregando bases e construindo contextos mensais...")
    bases = motor.carregar_bases()
    datas = motor.datas_do_periodo(bases.universo, fim=FIM_IN_SAMPLE)
    contextos = motor.construir_contextos(bases, datas, max_L=L_MOMENTUM)

    n_meses = len(contextos)
    print(f" -> {n_meses} meses de retorno "
          f"({contextos[0].data.strftime('%Y-%m')} a {contextos[-1].data.strftime('%Y-%m')})")

    # -----------------------------------------------------------------------
    # 2. Variantes determinísticas
    # -----------------------------------------------------------------------
    print("\n[2/5] Simulando variantes determinísticas (V0, V1, V2, V3, V5, V6)...")

    variantes = {
        "V0_universo80": dict(
            seletor=motor.pool_universo(), aplicar_momentum=False, cap=None,
            descricao="Universo 80, equal-weight, sem filtros"),
        "V1_mst_sem_momentum": dict(
            seletor=motor.pool_mst(POOL_SIZE), aplicar_momentum=False, cap=CAP,
            descricao="MST top-20, sem momentum, cap 10%"),
        "V2_mst_momentum_sem_cap": dict(
            seletor=motor.pool_mst(POOL_SIZE), aplicar_momentum=True, cap=None,
            descricao="MST top-20 + SMA150, **sem** cap (100% investido)"),
        "V3_oficial": dict(
            seletor=motor.pool_mst(POOL_SIZE), aplicar_momentum=True, cap=CAP,
            descricao="MST top-20 + SMA150 + cap 10% — **oficial**"),
        "V5_menor_correlacao": dict(
            seletor=motor.pool_menor_correlacao(POOL_SIZE), aplicar_momentum=True, cap=CAP,
            descricao="Menor correlação média + SMA150 + cap 10%"),
        "V6_menor_beta": dict(
            seletor=motor.pool_menor_beta(POOL_SIZE), aplicar_momentum=True, cap=CAP,
            descricao="Menor \\|beta\\| vs. IBOV + SMA150 + cap 10%"),
    }

    resultados, metricas, descricoes = {}, {}, {}
    for nome, cfg in variantes.items():
        df = motor.simular(
            contextos, bases.precos,
            seletor=cfg["seletor"],
            aplicar_momentum=cfg["aplicar_momentum"],
            L=L_MOMENTUM,
            cap=cfg["cap"],
        )
        resultados[nome] = df
        metricas[nome] = metricas_de(df)
        descricoes[nome] = cfg["descricao"]
        df.to_parquet(OUT_DIR / f"{nome}.parquet", index=False)
        print(f" -> {nome:26s} Sharpe geom = {metricas[nome]['sharpe_geometrico']:+.3f}")

    # -----------------------------------------------------------------------
    # 3. V4 — nulo pareado (pool aleatório, mesmo momentum, mesmo cap)
    # -----------------------------------------------------------------------
    print(f"\n[3/5] Simulando o nulo pareado V4 ({N_SORTEIOS_NULO} sorteios)...")
    print("      (pool aleatório de 20 + SMA150 + cap 10% — difere do V3 SÓ no pool)")

    sharpes_nulo, cagr_nulo, dd_nulo = [], [], []
    for k in range(N_SORTEIOS_NULO):
        rng = np.random.default_rng(1000 + k)
        df_k = motor.simular(
            contextos, bases.precos,
            seletor=motor.pool_aleatorio(POOL_SIZE, rng),
            aplicar_momentum=True, L=L_MOMENTUM, cap=CAP,
        )
        m_k = calcular_metricas_institucionais(
            motor.serie_retornos(df_k), motor.serie_cdi(df_k)
        )
        sharpes_nulo.append(m_k["sharpe_geometrico"])
        cagr_nulo.append(m_k["ret_anual_cagr"])
        dd_nulo.append(m_k["max_drawdown"])

        if (k + 1) % 50 == 0:
            print(f"      {k + 1}/{N_SORTEIOS_NULO} sorteios")

    sharpes_nulo = np.array(sharpes_nulo)
    pd.DataFrame({
        "sorteio": np.arange(N_SORTEIOS_NULO),
        "sharpe_geometrico": sharpes_nulo,
        "cagr": cagr_nulo,
        "max_drawdown": dd_nulo,
    }).to_parquet(OUT_DIR / "V4_nulo_pareado.parquet", index=False)

    # -----------------------------------------------------------------------
    # 4. As três leituras da atribuição
    # -----------------------------------------------------------------------
    s_v1 = metricas["V1_mst_sem_momentum"]["sharpe_geometrico"]
    s_v2 = metricas["V2_mst_momentum_sem_cap"]["sharpe_geometrico"]
    s_v3 = metricas["V3_oficial"]["sharpe_geometrico"]
    s_v5 = metricas["V5_menor_correlacao"]["sharpe_geometrico"]
    s_v6 = metricas["V6_menor_beta"]["sharpe_geometrico"]

    nulo_mediana = float(np.median(sharpes_nulo))
    nulo_p95 = float(np.percentile(sharpes_nulo, 95))
    percentil_v3 = float((sharpes_nulo < s_v3).mean() * 100.0)
    p_value_mst = float((sharpes_nulo >= s_v3).mean())

    contrib_mst = s_v3 - nulo_mediana
    contrib_caixa = s_v3 - s_v2
    contrib_momentum = s_v3 - s_v1

    print("\n[4/5] Atribuição:")
    print(f" -> V3 (oficial)              : {s_v3:+.3f}")
    print(f" -> V4 mediana do nulo pareado: {nulo_mediana:+.3f}  (p95 = {nulo_p95:+.3f})")
    print(f" -> Percentil do V3 no nulo   : {percentil_v3:.1f}%   (p-value = {p_value_mst:.1%})")
    print(f" -> Contribuição da MST       : {contrib_mst:+.3f}")
    print(f" -> Contribuição do caixa     : {contrib_caixa:+.3f}")
    print(f" -> Contribuição do momentum  : {contrib_momentum:+.3f}")

    # -----------------------------------------------------------------------
    # 5. Gráficos
    # -----------------------------------------------------------------------
    print("\n[5/5] Gerando gráficos e relatório...")

    plt.figure(figsize=(11, 6))
    plt.hist(sharpes_nulo, bins=30, color="lightgray", edgecolor="black", alpha=0.8,
             label=f"V4 — nulo pareado ({N_SORTEIOS_NULO} pools aleatórios + SMA150 + cap)")
    plt.axvline(nulo_mediana, color="black", linestyle="--", linewidth=2,
                label=f"Mediana do nulo: {nulo_mediana:+.3f}")
    plt.axvline(nulo_p95, color="orange", linestyle=":", linewidth=2,
                label=f"Percentil 95 do nulo: {nulo_p95:+.3f}")
    plt.axvline(s_v3, color="purple", linestyle="-", linewidth=3,
                label=f"V3 Nexus (MST): {s_v3:+.3f} — percentil {percentil_v3:.0f}%")
    plt.axvline(s_v5, color="green", linestyle="-.", linewidth=2,
                label=f"V5 menor correlação: {s_v5:+.3f}")
    plt.axvline(s_v6, color="brown", linestyle="-.", linewidth=2,
                label=f"V6 menor beta: {s_v6:+.3f}")

    plt.title("A MST agrega sobre um pool aleatório?\n"
              "Nulo pareado: mesmo momentum, mesmo cap, mesmo universo — só o pool muda",
              fontsize=12, fontweight="bold")
    plt.xlabel("Sharpe Geométrico (In-Sample)", fontsize=11)
    plt.ylabel("Frequência", fontsize=11)
    plt.legend(loc="upper left", fontsize=9)
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(IMG_DIR / "08_ablacao_distribuicao_nulo.png", dpi=180)
    plt.close()

    plt.figure(figsize=(12, 6))
    datas_plot = resultados["V3_oficial"]["data"]
    for nome, cor in [("V0_universo80", "#999999"), ("V1_mst_sem_momentum", "#d62728"),
                      ("V2_mst_momentum_sem_cap", "#ff7f0e"), ("V3_oficial", "#9467bd"),
                      ("V5_menor_correlacao", "#2ca02c"), ("V6_menor_beta", "#8c564b")]:
        curva = 100.0 * (1.0 + resultados[nome]["retorno_total"]).cumprod()
        plt.plot(datas_plot, curva, label=f"{nome} | R$ {curva.iloc[-1]:.0f}",
                 color=cor, linewidth=2.0)
    curva_cdi = 100.0 * (1.0 + resultados["V3_oficial"]["retorno_cdi"]).cumprod()
    plt.plot(datas_plot, curva_cdi, label=f"CDI | R$ {curva_cdi.iloc[-1]:.0f}",
             color="black", linestyle="--", linewidth=2.2)

    plt.title("Ablação por camada — evolução de R$ 100 (In-Sample)",
              fontsize=13, fontweight="bold")
    plt.ylabel("Patrimônio (R$)")
    plt.xlabel("Ano")
    plt.legend(loc="upper left", fontsize=9)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(IMG_DIR / "09_ablacao_equity_variantes.png", dpi=180)
    plt.close()

    # -----------------------------------------------------------------------
    # 6. Veredito condicional — o texto segue o resultado, não o contrário
    # -----------------------------------------------------------------------
    if percentil_v3 >= 95.0:
        veredito_mst = (
            f"A seleção topológica **agrega**. O V3 ficou no percentil "
            f"{percentil_v3:.1f}% da distribuição de pools aleatórios submetidos ao "
            f"mesmo momentum e ao mesmo cap (p-value = {p_value_mst:.1%}). A diferença "
            f"não é atribuível ao filtro direcional nem ao colchão de caixa, porque "
            f"ambos estão presentes nos dois lados da comparação."
        )
    elif percentil_v3 >= 75.0:
        veredito_mst = (
            f"A seleção topológica mostra **vantagem fraca e não conclusiva**. O V3 caiu "
            f"no percentil {percentil_v3:.1f}% do nulo pareado (p-value = {p_value_mst:.1%}), "
            f"acima da mediana mas sem atingir significância a 5%. Com {n_meses} meses de "
            f"amostra, este resultado é compatível tanto com um efeito real pequeno quanto "
            f"com ruído. **Não deve ser apresentado como alpha comprovado.**"
        )
    else:
        veredito_mst = (
            f"A seleção topológica **não agrega** sobre um pool aleatório. O V3 caiu no "
            f"percentil {percentil_v3:.1f}% do nulo pareado — dentro do que se obtém "
            f"sorteando 20 ações do mesmo universo e aplicando os mesmos filtros. "
            f"O Sharpe do Robô Nexus vem do momentum e do colchão de caixa, **não da "
            f"posição das ações na MST**. Este é um resultado negativo legítimo e deve "
            f"ser reportado como tal."
        )

    maior_contrib = max(
        [("MST", contrib_mst), ("colchão de caixa", contrib_caixa), ("momentum", contrib_momentum)],
        key=lambda x: x[1],
    )

    # -----------------------------------------------------------------------
    # 7. Relatório
    # -----------------------------------------------------------------------
    tabela = ""
    ordem = ["V0_universo80", "V1_mst_sem_momentum", "V2_mst_momentum_sem_cap",
             "V3_oficial", "V5_menor_correlacao", "V6_menor_beta"]
    for nome in ordem:
        tabela += linha_tabela(nome.split("_")[0], descricoes[nome], metricas[nome])

    md = f"""# Ablação e Atribuição por Camada (TICKET-C03)

**Script:** `scripts/14_ablacao_atribuicao.py`
**Período:** In-Sample — {contextos[0].data.strftime('%b/%Y')} a {contextos[-1].data.strftime('%b/%Y')} ({n_meses} meses)
**Parâmetros travados:** Pool = {POOL_SIZE}, SMA = {L_MOMENTUM}, Cap = {CAP*100:.0f}%, custo = {config.CUSTO_POR_OPERACAO*1e4:.1f} bps/perna

---

## 1. A pergunta

O Sharpe de +0.122 publicado pelo projeto foi produzido por três camadas
introduzidas simultaneamente: seleção topológica (MST), filtro direcional
(momentum) e colchão de caixa (cap de 10%). **Nenhum teste anterior separou as
três.** O teste de Monte Carlo original compara a combinação inteira contra
carteiras aleatórias 100% investidas, e atribui toda a diferença à MST.

Este documento isola cada camada mantendo as demais constantes.

## 2. Resultados das variantes

| Variante | Composição | CAGR | Vol. | Sharpe Geom. | Sharpe Clás. | MDD | Nº médio ações | % médio CDI | Turnover |
|---|---|---|---|---|---|---|---|---|---|
{tabela}
### V4 — Nulo pareado ({N_SORTEIOS_NULO} sorteios)

Pool de {POOL_SIZE} ações **sorteadas** do mesmo universo elegível, submetidas ao
**mesmo** filtro de momentum (SMA {L_MOMENTUM}) e ao **mesmo** cap de {CAP*100:.0f}%.
Difere do V3 em exatamente uma coisa: a origem do pool.

| Estatística | Sharpe Geométrico |
|---|---|
| Mediana do nulo | {nulo_mediana:+.3f} |
| Percentil 95 do nulo | {nulo_p95:+.3f} |
| **V3 (MST)** | **{s_v3:+.3f}** |
| **Percentil do V3 no nulo** | **{percentil_v3:.1f}%** |
| **p-value (unilateral)** | **{p_value_mst:.1%}** |

## 3. As três leituras

| Comparação | Diferença de Sharpe | Interpretação |
|---|---|---|
| **V3 − V4 (mediana)** | **{contrib_mst:+.3f}** | contribuição da **seleção topológica** |
| **V3 − V2** | **{contrib_caixa:+.3f}** | contribuição do **colchão de caixa** (cap) |
| **V3 − V1** | **{contrib_momentum:+.3f}** | contribuição do **filtro de momentum** |

A camada que mais contribuiu foi: **{maior_contrib[0]}** ({maior_contrib[1]:+.3f}).

### Controles sem grafo (plano-mestre, Parte 2.5.4)

| Controle | Sharpe | vs. V3 |
|---|---|---|
| V5 — menor correlação média | {s_v5:+.3f} | {s_v3 - s_v5:+.3f} |
| V6 — menor \\|beta\\| vs. IBOV | {s_v6:+.3f} | {s_v3 - s_v6:+.3f} |

Se um destes empata com o V3, a MST está reproduzindo um critério que se obtém
sem teoria de grafos — e a contribuição do grafo passa a ser interpretabilidade e
visualização, não alpha. O plano-mestre já registra essa possibilidade como
conclusão legítima.

## 4. Veredito

> {veredito_mst}

## 5. Visualizações

### 5.1 Distribuição do nulo pareado
<p align="center">
  <img src="../images/08_ablacao_distribuicao_nulo.png" width="700" alt="Distribuição do nulo pareado" />
</p>

### 5.2 Curvas de equity por variante
<p align="center">
  <img src="../images/09_ablacao_equity_variantes.png" width="700" alt="Equity das variantes" />
</p>

---

*Todos os números deste documento são gerados por `scripts/14_ablacao_atribuicao.py`.
Nenhum valor foi escrito à mão.*
"""

    doc = Path("docs") / "12_ablacao_e_atribuicao.md"
    doc.write_text(md, encoding="utf-8")
    print(f"\n[OK] Relatório: {doc.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
