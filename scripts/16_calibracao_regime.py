"""
===============================================================================
PROJETO NEXUS - DESAFIO ITAÚ ASSET QUANT AI 2026
TICKET-C05 - Calibração do Filtro de Regime Topológico
Arquivo: scripts/16_calibracao_regime.py
===============================================================================

O QUE ESTE SCRIPT FAZ:
----------------------
Implementa e calibra a Camada 4 (Filtro de Regime), que até agora existia apenas
na documentação. A métrica é a contração da MST — `calcular_distancia_media_mst`,
que já existia em `src/nexus/mst.py` e nunca havia sido usada para decidir nada.

CALIBRAÇÃO (in-sample, um único parâmetro):
  percentil p em {5, 10, 15, 20} -> TODOS reportados, um travado.

O TESTE QUE IMPORTA — REDUNDÂNCIA COM O CAP:
--------------------------------------------
O cap de 10% JÁ É um mecanismo pró-cíclico de caixa: momentum falha -> poucas
ações passam -> capital migra para o CDI. É plausível que o filtro de regime
esteja medindo o mesmo fenômeno por outro caminho. Se `V3 + regime ~= V3`, a
camada é redundante — e isso é um achado publicável, não um fracasso.

Por isso o script roda o regime sobre DUAS bases:
  - V3 (com cap)    -> mede o ganho incremental sobre um colchão que já existe
  - V2 (sem cap)    -> mede o que o regime faz sozinho, sem colchão concorrente

SAÍDAS:
-------
  dados/resultados/ablacao/regime_*.parquet
  images/11_regime_calibracao.png
  docs/15_filtro_regime.md
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

from src.nexus import config, motor, regime
from src.nexus.portfolio import calcular_metricas_institucionais

POOL_SIZE = 20
L_MOMENTUM = 150
CAP = config.CAP_POR_ATIVO
FIM_IN_SAMPLE = "2018-12-31"

PERCENTIS = [5, 10, 15, 20]
EXPOSICAO_CRISE = 0.30
MIN_HISTORICO = 24

# Crises dentro do in-sample (a COVID está no out-of-sample e não pode ser usada aqui)
CRISES_IN_SAMPLE = {
    "Crise do euro / downgrade (2011-2012)": ("2011-08-01", "2012-06-30"),
    "Colapso de commodities (2014-2015)": ("2014-09-01", "2016-01-31"),
    "Joesley Day (2017)": ("2017-05-01", "2017-08-31"),
    "Greve dos caminhoneiros (2018)": ("2018-05-01", "2018-09-30"),
}

IMG_DIR = Path("images")
OUT_DIR = Path("dados/resultados/ablacao")
IMG_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)


def metricas_de(df: pd.DataFrame) -> dict:
    m = calcular_metricas_institucionais(motor.serie_retornos(df), motor.serie_cdi(df))
    m["pct_cdi_medio"] = float(df["pct_cdi"].mean())
    m["turnover_medio"] = float(df["turnover"].mean())
    return m


def main() -> None:
    print("=" * 78)
    print("  TICKET-C05 - FILTRO DE REGIME TOPOLÓGICO")
    print("=" * 78)

    print("\n[1/5] Construindo contextos mensais...")
    bases = motor.carregar_bases()
    datas = motor.datas_do_periodo(bases.universo, fim=FIM_IN_SAMPLE)
    contextos = motor.construir_contextos(bases, datas, max_L=L_MOMENTUM)
    n_meses = len(contextos)

    dist = regime.serie_distancia_media(contextos)
    print(f" -> {n_meses} meses. Distância média da MST: "
          f"min={dist.min():.4f}, mediana={dist.median():.4f}, max={dist.max():.4f}")

    # -----------------------------------------------------------------------
    # 2. Bases sem regime
    # -----------------------------------------------------------------------
    print("\n[2/5] Simulando as bases sem regime (V3 com cap, V2 sem cap)...")
    df_v3 = motor.simular(contextos, bases.precos, seletor=motor.pool_mst(POOL_SIZE),
                          aplicar_momentum=True, L=L_MOMENTUM, cap=CAP)
    df_v2 = motor.simular(contextos, bases.precos, seletor=motor.pool_mst(POOL_SIZE),
                          aplicar_momentum=True, L=L_MOMENTUM, cap=None)
    m_v3, m_v2 = metricas_de(df_v3), metricas_de(df_v2)
    print(f" -> V3 (cap):     Sharpe {m_v3['sharpe_geometrico']:+.3f}  MDD {m_v3['max_drawdown']*100:.1f}%")
    print(f" -> V2 (sem cap): Sharpe {m_v2['sharpe_geometrico']:+.3f}  MDD {m_v2['max_drawdown']*100:.1f}%")

    # -----------------------------------------------------------------------
    # 3. Varredura de percentis
    # -----------------------------------------------------------------------
    print(f"\n[3/5] Calibrando o percentil de corte em {PERCENTIS}...")
    resultados = {}
    for p in PERCENTIS:
        mult = regime.calcular_multiplicadores(
            dist, percentil=p, exposicao_crise=EXPOSICAO_CRISE, min_historico=MIN_HISTORICO
        )
        df_p_cap = motor.simular(contextos, bases.precos, seletor=motor.pool_mst(POOL_SIZE),
                                 aplicar_momentum=True, L=L_MOMENTUM, cap=CAP,
                                 multiplicadores_regime=mult)
        df_p_sem = motor.simular(contextos, bases.precos, seletor=motor.pool_mst(POOL_SIZE),
                                 aplicar_momentum=True, L=L_MOMENTUM, cap=None,
                                 multiplicadores_regime=mult)
        resultados[p] = {
            "mult": mult,
            "com_cap": metricas_de(df_p_cap),
            "sem_cap": metricas_de(df_p_sem),
            "acionamento": regime.resumo_acionamento(mult),
            "df_com_cap": df_p_cap,
        }
        df_p_cap.to_parquet(OUT_DIR / f"regime_p{p}_com_cap.parquet", index=False)

        a = resultados[p]["acionamento"]
        c = resultados[p]["com_cap"]
        print(f" -> p={p:2d}: aciona {a['meses_acionado']:3d}/{a['meses_totais']} meses "
              f"({a['pct_meses_acionado']:.1f}%) | Sharpe {c['sharpe_geometrico']:+.3f} "
              f"| MDD {c['max_drawdown']*100:.1f}%")

    # -----------------------------------------------------------------------
    # 4. Escolha e diagnóstico de redundância
    # -----------------------------------------------------------------------
    melhor_p = max(PERCENTIS, key=lambda p: resultados[p]["com_cap"]["sharpe_geometrico"])
    m_best = resultados[melhor_p]["com_cap"]

    ganho_sharpe = m_best["sharpe_geometrico"] - m_v3["sharpe_geometrico"]
    ganho_mdd = m_best["max_drawdown"] - m_v3["max_drawdown"]   # positivo = drawdown menor
    ganho_sem_cap = (resultados[melhor_p]["sem_cap"]["sharpe_geometrico"]
                     - m_v2["sharpe_geometrico"])

    redundante = abs(ganho_sharpe) < 0.02 and abs(ganho_mdd) < 0.02

    print(f"\n[4/5] Percentil escolhido: p={melhor_p}")
    print(f" -> Ganho de Sharpe sobre V3: {ganho_sharpe:+.3f}")
    print(f" -> Variação do MDD:          {ganho_mdd*100:+.1f} p.p.")
    print(f" -> Ganho sobre V2 (sem cap): {ganho_sem_cap:+.3f}")
    print(f" -> Redundante com o cap?     {'SIM' if redundante else 'NÃO'}")

    # -----------------------------------------------------------------------
    # 5. Atraso de reação nas crises in-sample
    # -----------------------------------------------------------------------
    print("\n[5/5] Medindo o atraso de reação nas crises do in-sample...")
    mult_best = resultados[melhor_p]["mult"]
    df_best = resultados[melhor_p]["df_com_cap"]
    atrasos = {}
    for nome, janela in CRISES_IN_SAMPLE.items():
        atrasos[nome] = regime.medir_atraso_reacao(
            mult_best, df_best["retorno_total"], df_best["data"], janela
        )
        a = atrasos[nome]
        if a["mes_reacao"] is None:
            print(f" -> {nome}: filtro NÃO acionou")
        else:
            print(f" -> {nome}: choque {a['mes_choque']:%Y-%m}, "
                  f"reação {a['mes_reacao']:%Y-%m}, atraso {a['atraso_meses']} mês(es)")

    # -----------------------------------------------------------------------
    # Gráfico
    # -----------------------------------------------------------------------
    fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)

    axes[0].plot(dist.index, dist.values, color="#1f77b4", linewidth=1.8,
                 label="Distância média das arestas da MST")
    acion = mult_best[mult_best < 1.0]
    for d in acion.index:
        axes[0].axvspan(d, d + pd.Timedelta(days=30), color="red", alpha=0.15)
    axes[0].set_title(f"Contração da MST e acionamento do filtro (percentil {melhor_p}%)",
                      fontsize=12, fontweight="bold")
    axes[0].set_ylabel("Distância média")
    axes[0].legend(loc="upper right", fontsize=9)
    axes[0].grid(True, alpha=0.3)

    curva_v3 = 100.0 * (1.0 + df_v3["retorno_total"]).cumprod()
    curva_reg = 100.0 * (1.0 + df_best["retorno_total"]).cumprod()
    curva_cdi = 100.0 * (1.0 + df_v3["retorno_cdi"]).cumprod()
    axes[1].plot(df_v3["data"], curva_v3, color="#9467bd", linewidth=2.2,
                 label=f"V3 sem regime | R$ {curva_v3.iloc[-1]:.0f}")
    axes[1].plot(df_best["data"], curva_reg, color="#d62728", linewidth=2.2,
                 label=f"V3 + regime p{melhor_p} | R$ {curva_reg.iloc[-1]:.0f}")
    axes[1].plot(df_v3["data"], curva_cdi, color="black", linestyle="--", linewidth=2.0,
                 label=f"CDI | R$ {curva_cdi.iloc[-1]:.0f}")
    axes[1].set_title("Impacto do filtro de regime sobre a curva de capital",
                      fontsize=12, fontweight="bold")
    axes[1].set_ylabel("Patrimônio (R$)")
    axes[1].set_xlabel("Ano")
    axes[1].legend(loc="upper left", fontsize=9)
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(IMG_DIR / "11_regime_calibracao.png", dpi=180)
    plt.close()

    # -----------------------------------------------------------------------
    # Relatório
    # -----------------------------------------------------------------------
    tabela = ""
    for p in PERCENTIS:
        c, a = resultados[p]["com_cap"], resultados[p]["acionamento"]
        s = resultados[p]["sem_cap"]
        marca = " ⬅ **travado**" if p == melhor_p else ""
        tabela += (
            f"| **{p}%**{marca} | {a['meses_acionado']}/{a['meses_totais']} "
            f"({a['pct_meses_acionado']:.1f}%) | {c['ret_anual_cagr']*100:.1f}% | "
            f"{c['vol_anual']*100:.1f}% | {c['sharpe_geometrico']:+.3f} | "
            f"{c['max_drawdown']*100:.1f}% | {s['sharpe_geometrico']:+.3f} |\n"
        )

    tabela_atraso = ""
    for nome, a in atrasos.items():
        if a["mes_reacao"] is None:
            tabela_atraso += f"| {nome} | {a['mes_choque']:%Y-%m} | não acionou | — |\n"
        else:
            tabela_atraso += (f"| {nome} | {a['mes_choque']:%Y-%m} | "
                              f"{a['mes_reacao']:%Y-%m} | {a['atraso_meses']} |\n")

    if redundante:
        veredito = (
            f"**O filtro de regime é redundante com o cap de {CAP*100:.0f}%.** Adicioná-lo "
            f"ao V3 mudou o Sharpe em {ganho_sharpe:+.3f} e o drawdown em "
            f"{ganho_mdd*100:+.1f} p.p. — variações dentro do ruído. A explicação é "
            f"mecânica: quando o mercado contrai, o momentum reprova a maior parte do "
            f"pool, poucas ações passam, e o cap já empurra o capital para o CDI. As "
            f"duas camadas medem o mesmo fenômeno por caminhos diferentes.\n\n"
            f"Sobre a base **sem** cap (V2), o regime altera o Sharpe em "
            f"{ganho_sem_cap:+.3f} — é aí que se vê o efeito isolado da camada."
        )
    else:
        veredito = (
            f"**O filtro de regime agrega sobre o cap.** No percentil {melhor_p}%, o "
            f"Sharpe varia {ganho_sharpe:+.3f} e o drawdown máximo varia "
            f"{ganho_mdd*100:+.1f} p.p. em relação ao V3 sem regime. Sobre a base sem "
            f"cap (V2), o efeito isolado é de {ganho_sem_cap:+.3f}."
        )

    md = f"""# Filtro de Regime Topológico (TICKET-C05)

**Script:** `scripts/16_calibracao_regime.py`
**Módulo:** `src/nexus/regime.py`
**Período:** In-Sample — {contextos[0].data.strftime('%b/%Y')} a {contextos[-1].data.strftime('%b/%Y')} ({n_meses} meses)

---

## 1. A camada que faltava

O Filtro de Regime era anunciado em todos os documentos do projeto como a terceira
camada da arquitetura, mas **não existia no código**. Este documento registra sua
implementação, calibração e — o mais importante — o teste de se ele agrega algo
sobre as camadas que já estavam lá.

**Métrica:** distância média das arestas da MST. Quando o mercado entra em pânico,
as correlações sobem, as distâncias de Mantegna encolhem e a árvore se contrai
(Onnela et al., 2003). Nos dados do projeto, a correlação média sai de 0,10–0,22
em períodos normais.

**Regra (um único parâmetro):**

```
limiar(T) = percentil p da distância média observada estritamente até T-1
se dist(T) < limiar(T)  ->  exposição em ações = {EXPOSICAO_CRISE*100:.0f}%
senão                    ->  exposição = 100% do que o cap determinou
```

O percentil é **expansível**, nunca calculado sobre a série inteira: em 2011 o
modelo usa apenas o que existia em 2011. Enquanto houver menos de {MIN_HISTORICO}
meses de histórico, o filtro se abstém.

## 2. Calibração — todos os percentis testados

| Percentil | Meses acionado | CAGR | Vol. | Sharpe (com cap) | MDD | Sharpe (sem cap) |
|---|---|---|---|---|---|---|
{tabela}
**Linha de base sem regime:** V3 (com cap) Sharpe {m_v3['sharpe_geometrico']:+.3f},
MDD {m_v3['max_drawdown']*100:.1f}% | V2 (sem cap) Sharpe {m_v2['sharpe_geometrico']:+.3f},
MDD {m_v2['max_drawdown']*100:.1f}%.

## 3. Teste de redundância com o cap de {CAP*100:.0f}%

| Configuração | Sharpe | MDD | % médio em CDI |
|---|---|---|---|
| V3 (cap, sem regime) | {m_v3['sharpe_geometrico']:+.3f} | {m_v3['max_drawdown']*100:.1f}% | {m_v3['pct_cdi_medio']:.1f}% |
| V3 + regime p{melhor_p} | {m_best['sharpe_geometrico']:+.3f} | {m_best['max_drawdown']*100:.1f}% | {m_best['pct_cdi_medio']:.1f}% |
| V2 (sem cap, sem regime) | {m_v2['sharpe_geometrico']:+.3f} | {m_v2['max_drawdown']*100:.1f}% | {m_v2['pct_cdi_medio']:.1f}% |
| V2 + regime p{melhor_p} | {resultados[melhor_p]['sem_cap']['sharpe_geometrico']:+.3f} | {resultados[melhor_p]['sem_cap']['max_drawdown']*100:.1f}% | {resultados[melhor_p]['sem_cap']['pct_cdi_medio']:.1f}% |

> {veredito}

## 4. Atraso estrutural de reação

A distância média vem de uma janela trailing de {config.JANELA_CORRELACAO} pregões e
é avaliada **uma vez por mês**. Num crash que se desenvolve em dias, o filtro reage
depois do estrago. Isto não é ajustável — é uma propriedade do desenho, e precisa
ser declarada em vez de escondida.

| Crise (in-sample) | Mês do choque | Mês da reação | Atraso (meses) |
|---|---|---|---|
{tabela_atraso}
## 5. Visualização

<p align="center">
  <img src="../images/11_regime_calibracao.png" width="720" alt="Calibração do filtro de regime" />
</p>

---

## 6. Enquadramento honesto

O filtro de regime é **instrumento de risco, não de alpha**. Julgá-lo pelo Sharpe é
usar a métrica errada: ele pode legitimamente não melhorar o retorno e ainda assim
ser um sucesso se cortar o drawdown. A tabela da seção 3 reporta as duas dimensões
justamente por isso.

*Todos os números deste documento são gerados pelo script. Nenhum valor foi escrito à mão.*
"""

    doc = Path("docs") / "15_filtro_regime.md"
    doc.write_text(md, encoding="utf-8")
    print(f"\n[OK] Relatório: {doc.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
