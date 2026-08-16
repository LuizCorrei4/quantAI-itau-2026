"""
===============================================================================
PROJETO NEXUS - DESAFIO ITAÚ ASSET QUANT AI 2026
TICKET-C06 - Teste Cego Out-of-Sample (EXECUÇÃO ÚNICA)
Arquivo: scripts/17_out_of_sample.py
===============================================================================

ESTE SCRIPT SÓ PODE SER RODADO UMA VEZ.

Todo número publicado pelo projeto até aqui — o Sharpe de +0.122, o p-value, a
sensibilidade a custos, a batalha dos filtros — é IN-SAMPLE. O out-of-sample
(jan/2019 a jul/2026) nunca foi tocado, conforme o Pacto de Integridade
registrado no plano-mestre.

GUARDA-CORPO MECÂNICO:
----------------------
O script se RECUSA a rodar se `parametros_travados.json` não existir na raiz do
repositório. Esse arquivo precisa estar COMMITADO ANTES da execução — o timestamp
do commit é a prova, verificável por qualquer um, de que os parâmetros não foram
escolhidos depois de ver o resultado.

Transformar o pacto de integridade em código, em vez de deixá-lo como intenção,
é o que o diferencia de uma promessa.

REGRA INEGOCIÁVEL:
------------------
Nenhum ajuste de parâmetro depois de olhar o resultado. Se o Sharpe desabar, o
resultado ruim É a entrega. Uma queda de +0.122 in-sample para perto de zero
out-of-sample é o achado mais informativo que este projeto pode produzir, e é
exatamente o que a literatura prevê quando o sinal é fraco.

SAÍDAS:
-------
  dados/resultados/out_of_sample/*.parquet
  images/13_out_of_sample_equity.png
  images/14_out_of_sample_nulo.png
  docs/14_out_of_sample.md
===============================================================================
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.nexus import config, motor, regime
from src.nexus.portfolio import calcular_metricas_institucionais

RAIZ = Path(__file__).resolve().parents[1]
ARQ_PARAMS = RAIZ / "parametros_travados.json"

INICIO_OOS = "2019-01-01"
FIM_IN_SAMPLE = "2018-12-31"
N_SORTEIOS_NULO = 200

IMG_DIR = Path("images")
OUT_DIR = Path("dados/resultados/out_of_sample")

TEMPLATE = {
    "pool_size": 20,
    "L_momentum": 150,
    "cap_por_ativo": 0.10,
    "custo_por_perna": 0.0005,
    "regime_ativo": True,
    "regime_percentil": 10,
    "regime_exposicao_crise": 0.30,
    "regime_min_historico": 24,
    "origem": "grid in-sample (script 10) + CV temporal (script 18) + regime (script 16)",
    "travado_em": "AAAA-MM-DD",
}


def carregar_parametros() -> dict:
    """Aborta se os parâmetros não estiverem travados e commitados."""
    if not ARQ_PARAMS.exists():
        print("=" * 78)
        print("  EXECUÇÃO BLOQUEADA — parâmetros não travados")
        print("=" * 78)
        print(f"\n{ARQ_PARAMS} não existe.\n")
        print("O out-of-sample só pode rodar depois que os parâmetros forem")
        print("congelados e COMMITADOS. Crie o arquivo com o conteúdo abaixo,")
        print("ajuste os valores, faça o commit e só então rode este script.\n")
        print(json.dumps(TEMPLATE, indent=2, ensure_ascii=False))
        print("\n  git add parametros_travados.json")
        print('  git commit -m "chore: trava parametros antes do out-of-sample"\n')
        sys.exit(1)

    params = json.loads(ARQ_PARAMS.read_text(encoding="utf-8"))
    faltando = [k for k in TEMPLATE if k not in params]
    if faltando:
        print(f"[ERRO] Chaves ausentes em {ARQ_PARAMS.name}: {faltando}")
        sys.exit(1)
    return params


def metricas_de(df: pd.DataFrame) -> dict:
    m = calcular_metricas_institucionais(motor.serie_retornos(df), motor.serie_cdi(df))
    m["pct_cdi_medio"] = float(df["pct_cdi"].mean())
    m["turnover_medio"] = float(df["turnover"].mean())
    m["n_acoes_medio"] = float(df["n_acoes"].mean())
    return m


def retorno_benchmark(bench: pd.DataFrame, coluna: str, datas) -> pd.Series:
    """Retornos mensais de um benchmark nas datas de rebalanceamento."""
    serie = bench[coluna].reindex(bench.index)
    valores = []
    for i in range(len(datas) - 1):
        i0 = serie.index.get_indexer([datas[i]], method="pad")[0]
        i1 = serie.index.get_indexer([datas[i + 1]], method="pad")[0]
        valores.append(float(serie.iloc[i1] / serie.iloc[i0] - 1.0))
    return pd.Series(valores)


def main() -> None:
    params = carregar_parametros()
    carimbo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("=" * 78)
    print("  TICKET-C06 - OUT-OF-SAMPLE CEGO (EXECUÇÃO ÚNICA)")
    print(f"  Executado em: {carimbo}")
    print("=" * 78)
    print("\nParâmetros travados:")
    for k, v in params.items():
        print(f"  {k:26s} = {v}")

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pool_size = int(params["pool_size"])
    L = int(params["L_momentum"])
    cap = float(params["cap_por_ativo"])
    custo = float(params["custo_por_perna"])

    # -----------------------------------------------------------------------
    # 1. Contextos do período INTEIRO
    #    O percentil do regime precisa do histórico expansível desde 2011,
    #    senão o filtro começaria o OOS sem memória.
    # -----------------------------------------------------------------------
    print("\n[1/5] Construindo contextos de 2011 até o fim da amostra...")
    bases = motor.carregar_bases()
    datas_todas = motor.datas_do_periodo(bases.universo)
    contextos_todos = motor.construir_contextos(bases, datas_todas, max_L=L)

    ctx_in = [c for c in contextos_todos if c.data <= pd.Timestamp(FIM_IN_SAMPLE)]
    ctx_oos = [c for c in contextos_todos if c.data >= pd.Timestamp(INICIO_OOS)]
    print(f" -> in-sample: {len(ctx_in)} meses | out-of-sample: {len(ctx_oos)} meses "
          f"({ctx_oos[0].data:%Y-%m} a {ctx_oos[-1].data:%Y-%m})")

    # -----------------------------------------------------------------------
    # 2. Multiplicadores de regime (percentil expansível sobre TODA a série)
    # -----------------------------------------------------------------------
    mult = None
    if params["regime_ativo"]:
        dist_todas = regime.serie_distancia_media(contextos_todos)
        mult = regime.calcular_multiplicadores(
            dist_todas,
            percentil=float(params["regime_percentil"]),
            exposicao_crise=float(params["regime_exposicao_crise"]),
            min_historico=int(params["regime_min_historico"]),
        )
        r = regime.resumo_acionamento(mult[mult.index >= pd.Timestamp(INICIO_OOS)])
        print(f" -> regime acionou em {r['meses_acionado']}/{r['meses_totais']} "
              f"meses do OOS ({r['pct_meses_acionado']:.1f}%)")

    # -----------------------------------------------------------------------
    # 3. Variantes oficiais, in-sample e out-of-sample
    # -----------------------------------------------------------------------
    print("\n[2/5] Simulando a variante oficial nos dois períodos...")

    def roda(ctx, com_regime: bool):
        return motor.simular(
            ctx, bases.precos, seletor=motor.pool_mst(pool_size),
            aplicar_momentum=True, L=L, cap=cap, custo_por_perna=custo,
            multiplicadores_regime=mult if com_regime else None,
        )

    df_in = roda(ctx_in, com_regime=False)
    df_oos = roda(ctx_oos, com_regime=False)
    m_in, m_oos = metricas_de(df_in), metricas_de(df_oos)

    df_in_reg = df_oos_reg = None
    m_in_reg = m_oos_reg = None
    if params["regime_ativo"]:
        df_in_reg = roda(ctx_in, com_regime=True)
        df_oos_reg = roda(ctx_oos, com_regime=True)
        m_in_reg, m_oos_reg = metricas_de(df_in_reg), metricas_de(df_oos_reg)

    df_oos.to_parquet(OUT_DIR / "oos_oficial.parquet", index=False)
    if df_oos_reg is not None:
        df_oos_reg.to_parquet(OUT_DIR / "oos_oficial_com_regime.parquet", index=False)

    print(f" -> IN  : Sharpe {m_in['sharpe_geometrico']:+.3f} | CAGR {m_in['ret_anual_cagr']*100:.1f}%")
    print(f" -> OOS : Sharpe {m_oos['sharpe_geometrico']:+.3f} | CAGR {m_oos['ret_anual_cagr']*100:.1f}%")

    # -----------------------------------------------------------------------
    # 4. Nulo pareado no OOS
    # -----------------------------------------------------------------------
    print(f"\n[3/5] Nulo pareado no OOS ({N_SORTEIOS_NULO} sorteios)...")
    nulo = []
    for k in range(N_SORTEIOS_NULO):
        rng = np.random.default_rng(5000 + k)
        df_k = motor.simular(
            ctx_oos, bases.precos, seletor=motor.pool_aleatorio(pool_size, rng),
            aplicar_momentum=True, L=L, cap=cap, custo_por_perna=custo,
        )
        mk = calcular_metricas_institucionais(motor.serie_retornos(df_k),
                                              motor.serie_cdi(df_k))
        nulo.append(float(mk["sharpe_geometrico"]))
        if (k + 1) % 50 == 0:
            print(f"      {k + 1}/{N_SORTEIOS_NULO}")
    nulo = np.array(nulo)
    pd.DataFrame({"sharpe_geometrico": nulo}).to_parquet(
        OUT_DIR / "oos_nulo_pareado.parquet", index=False)

    s_oos = m_oos["sharpe_geometrico"]
    percentil_oos = float((nulo < s_oos).mean() * 100.0)
    p_oos = float((nulo >= s_oos).mean())
    print(f" -> percentil do Nexus no nulo OOS: {percentil_oos:.1f}% (p={p_oos:.1%})")

    # -----------------------------------------------------------------------
    # 5. Benchmarks
    # -----------------------------------------------------------------------
    print("\n[4/5] Apurando benchmarks no OOS...")
    datas_oos = [c.data for c in ctx_oos] + [ctx_oos[-1].data_prox]
    ret_ibov = retorno_benchmark(bases.benchmarks, "ibov", datas_oos)
    ret_bova = retorno_benchmark(bases.benchmarks, "bova11", datas_oos)
    cdi_oos = motor.serie_cdi(df_oos)

    m_ibov = calcular_metricas_institucionais(ret_ibov, cdi_oos)
    m_bova = calcular_metricas_institucionais(ret_bova, cdi_oos)
    m_cdi = calcular_metricas_institucionais(cdi_oos, cdi_oos)

    # -----------------------------------------------------------------------
    # 6. Gráficos
    # -----------------------------------------------------------------------
    print("\n[5/5] Gerando gráficos e relatório...")

    plt.figure(figsize=(12, 6))
    d = df_oos["data"]
    plt.plot(d, 100 * (1 + df_oos["retorno_total"]).cumprod(), color="#9467bd",
             linewidth=2.4, label=f"Nexus V3 | R$ {100*(1+df_oos['retorno_total']).cumprod().iloc[-1]:.0f}")
    if df_oos_reg is not None:
        plt.plot(d, 100 * (1 + df_oos_reg["retorno_total"]).cumprod(), color="#d62728",
                 linewidth=2.0, label=f"Nexus V3 + regime | R$ {100*(1+df_oos_reg['retorno_total']).cumprod().iloc[-1]:.0f}")
    plt.plot(d, 100 * (1 + cdi_oos).cumprod(), color="black", linestyle="--",
             linewidth=2.2, label=f"CDI | R$ {100*(1+cdi_oos).cumprod().iloc[-1]:.0f}")
    plt.plot(d, 100 * (1 + ret_bova).cumprod(), color="#7f7f7f", linewidth=1.8,
             label=f"BOVA11 | R$ {100*(1+ret_bova).cumprod().iloc[-1]:.0f}")
    plt.title("Out-of-Sample cego (2019–2026): evolução de R$ 100",
              fontsize=13, fontweight="bold")
    plt.ylabel("Patrimônio (R$)")
    plt.xlabel("Ano")
    plt.legend(loc="upper left", fontsize=9)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(IMG_DIR / "13_out_of_sample_equity.png", dpi=180)
    plt.close()

    plt.figure(figsize=(11, 5.5))
    plt.hist(nulo, bins=30, color="lightgray", edgecolor="black", alpha=0.8,
             label=f"Nulo pareado no OOS ({N_SORTEIOS_NULO} pools aleatórios)")
    plt.axvline(float(np.median(nulo)), color="black", linestyle="--", linewidth=2,
                label=f"Mediana: {np.median(nulo):+.3f}")
    plt.axvline(s_oos, color="purple", linewidth=3,
                label=f"Nexus V3 (MST): {s_oos:+.3f} — percentil {percentil_oos:.0f}%")
    plt.title("A vantagem da MST sobrevive ao teste cego?", fontsize=12, fontweight="bold")
    plt.xlabel("Sharpe Geométrico (Out-of-Sample)")
    plt.ylabel("Frequência")
    plt.legend(loc="upper left", fontsize=9)
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(IMG_DIR / "14_out_of_sample_nulo.png", dpi=180)
    plt.close()

    # -----------------------------------------------------------------------
    # 7. Relatório
    # -----------------------------------------------------------------------
    degradacao = m_oos["sharpe_geometrico"] - m_in["sharpe_geometrico"]

    if m_oos["sharpe_geometrico"] > 0 and percentil_oos >= 95:
        veredito = (
            f"A estratégia **sobreviveu ao teste cego**: Sharpe {s_oos:+.3f} no OOS, "
            f"percentil {percentil_oos:.1f}% do nulo pareado (p={p_oos:.1%}). A "
            f"degradação em relação ao in-sample foi de {degradacao:+.3f}."
        )
    elif m_oos["sharpe_geometrico"] > 0:
        veredito = (
            f"A estratégia manteve Sharpe positivo no OOS ({s_oos:+.3f}), mas **sem "
            f"significância** contra o nulo pareado (percentil {percentil_oos:.1f}%, "
            f"p={p_oos:.1%}). Ou seja: o resultado é compatível com o que se obtém "
            f"sorteando o pool. A degradação em relação ao in-sample foi de {degradacao:+.3f}."
        )
    else:
        veredito = (
            f"A estratégia **não sobreviveu ao teste cego**: Sharpe {s_oos:+.3f} no OOS "
            f"contra {m_in['sharpe_geometrico']:+.3f} in-sample — degradação de "
            f"{degradacao:+.3f}. Esse é o padrão clássico de um sinal calibrado dentro "
            f"da amostra que não generaliza. Reportar isso é a entrega; maquiar seria "
            f"o único erro irrecuperável."
        )

    # Extraído do f-string para evitar aninhamento de aspas dentro da expressão
    desc_regime = (
        f"percentil {params['regime_percentil']}%"
        if params["regime_ativo"] else "desligado"
    )

    linha_reg_in = linha_reg_oos = ""
    if m_in_reg is not None:
        linha_reg_in = (f"| Nexus V3 + regime | {m_in_reg['ret_anual_cagr']*100:.1f}% | "
                        f"{m_in_reg['vol_anual']*100:.1f}% | {m_in_reg['sharpe_geometrico']:+.3f} | "
                        f"{m_in_reg['max_drawdown']*100:.1f}% | {m_in_reg['pct_cdi_medio']:.1f}% |\n")
        linha_reg_oos = (f"| Nexus V3 + regime | {m_oos_reg['ret_anual_cagr']*100:.1f}% | "
                         f"{m_oos_reg['vol_anual']*100:.1f}% | {m_oos_reg['sharpe_geometrico']:+.3f} | "
                         f"{m_oos_reg['max_drawdown']*100:.1f}% | {m_oos_reg['pct_cdi_medio']:.1f}% |\n")

    md = f"""# Teste Cego Out-of-Sample (TICKET-C06)

**Script:** `scripts/17_out_of_sample.py`
**Executado em:** {carimbo}
**Parâmetros:** travados em `parametros_travados.json`, commitado antes desta execução

| Parâmetro | Valor |
|---|---|
| Pool (Top N farness) | {pool_size} |
| SMA (L) | {L} |
| Cap por ativo | {cap*100:.0f}% |
| Custo por perna | {custo*1e4:.1f} bps |
| Filtro de regime | {desc_regime} |

---

## 1. In-sample vs. Out-of-sample

### In-sample ({ctx_in[0].data:%b/%Y} – {ctx_in[-1].data:%b/%Y}, {len(ctx_in)} meses)

| Estratégia | CAGR | Vol. | Sharpe Geom. | MDD | % médio CDI |
|---|---|---|---|---|---|
| Nexus V3 | {m_in['ret_anual_cagr']*100:.1f}% | {m_in['vol_anual']*100:.1f}% | **{m_in['sharpe_geometrico']:+.3f}** | {m_in['max_drawdown']*100:.1f}% | {m_in['pct_cdi_medio']:.1f}% |
{linha_reg_in}
### Out-of-sample ({ctx_oos[0].data:%b/%Y} – {ctx_oos[-1].data:%b/%Y}, {len(ctx_oos)} meses)

| Estratégia | CAGR | Vol. | Sharpe Geom. | MDD | % médio CDI |
|---|---|---|---|---|---|
| **Nexus V3** | **{m_oos['ret_anual_cagr']*100:.1f}%** | {m_oos['vol_anual']*100:.1f}% | **{m_oos['sharpe_geometrico']:+.3f}** | {m_oos['max_drawdown']*100:.1f}% | {m_oos['pct_cdi_medio']:.1f}% |
{linha_reg_oos}| CDI | {m_cdi['ret_anual_cagr']*100:.1f}% | {m_cdi['vol_anual']*100:.1f}% | 0.000 | 0.0% | 100.0% |
| Ibovespa | {m_ibov['ret_anual_cagr']*100:.1f}% | {m_ibov['vol_anual']*100:.1f}% | {m_ibov['sharpe_geometrico']:+.3f} | {m_ibov['max_drawdown']*100:.1f}% | — |
| BOVA11 | {m_bova['ret_anual_cagr']*100:.1f}% | {m_bova['vol_anual']*100:.1f}% | {m_bova['sharpe_geometrico']:+.3f} | {m_bova['max_drawdown']*100:.1f}% | — |

**Degradação in → out: `{degradacao:+.3f}` de Sharpe geométrico.**

## 2. O nulo pareado sobrevive no OOS?

| Estatística | Valor |
|---|---|
| Mediana do nulo pareado | {np.median(nulo):+.3f} |
| Percentil 95 do nulo | {np.percentile(nulo, 95):+.3f} |
| **Nexus V3 (MST)** | **{s_oos:+.3f}** |
| **Percentil do Nexus** | **{percentil_oos:.1f}%** |
| **p-value** | **{p_oos:.1%}** |

## 3. Veredito

> {veredito}

## 4. Visualizações

<p align="center">
  <img src="../images/13_out_of_sample_equity.png" width="720" alt="Equity out-of-sample" />
</p>

<p align="center">
  <img src="../images/14_out_of_sample_nulo.png" width="700" alt="Nulo pareado no OOS" />
</p>

---

## 5. Como ler a degradação

Alguma degradação do in-sample para o out-of-sample é **esperada e saudável** — o
par (Pool, SMA) foi escolhido como máximo de um grid de 16 combinações dentro do
in-sample, e todo máximo de grid carrega uma parcela de sorte que não se repete.

O sinal preocupante seria o contrário: um out-of-sample que **supera** o in-sample
sem explicação estrutural sugere que algo do período de teste vazou para a
calibração.

*Todos os números deste documento são gerados pelo script. Nenhum valor foi escrito à mão.*
"""

    doc = Path("docs") / "14_out_of_sample.md"
    doc.write_text(md, encoding="utf-8")
    print(f"\n[OK] Relatório: {doc.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
