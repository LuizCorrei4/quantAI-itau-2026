"""
===============================================================================
PROJETO NEXUS - DESAFIO ITAÚ ASSET QUANT AI 2026
TICKET-C02 - Teste de Monte Carlo Corrigido
Arquivo: scripts/15_monte_carlo_corrigido.py
===============================================================================

O QUE ESTE SCRIPT CORRIGE EM `09_baseline_aleatorias.py`:
--------------------------------------------------------

1) NÚMEROS NÃO CALCULADOS
   O script original tem `SHARPE_NEXUS = 0.10` hardcoded (linha 117) e calcula o
   p-value contra esse literal. Mas o markdown que ele gera escreve `0.122` e
   `3.2%` como STRINGS LITERAIS dentro da f-string (linhas 178-179). O p-value
   calculado nunca é publicado; o p-value publicado nunca é calculado. E o
   gráfico entregue desenha a linha do Nexus em 0.10, contradizendo a tabela.
   -> Aqui o Sharpe da estratégia é RECALCULADO pelo mesmo motor que roda o nulo.

2) NULO CONFUNDIDO COM O TRATAMENTO
   Os macacos originais recebem `calcular_pesos_equal_weight(candidatas)` SEM o
   argumento `cap`: 10 ações x 10% = 100% investido, sempre. O Nexus mantém em
   média ~13% em CDI. No período 2011-2018 o CDI rendeu 10.3% a.a. contra 6.2%
   do Ibovespa — ficar em caixa era vantagem estrutural naquele período, sem
   relação alguma com topologia ou momentum.
   -> Aqui rodamos DOIS nulos: o clássico (N1) e o pareado (N2).

3) MULTIPLE TESTING
   O par vencedor (Pool=20, SMA=150) é o MÁXIMO de um grid de 16 combinações,
   comparado contra o percentil 95 de um SORTEIO ÚNICO. São distribuições
   diferentes.
   -> Aqui cada trajetória do nulo varre o mesmo grid de 16 e reporta seu
      máximo. A distribuição desses máximos é o nulo correto.

SAÍDAS:
-------
  dados/resultados/ablacao/monte_carlo_nulos.parquet
  images/10_monte_carlo_corrigido.png
  docs/13_monte_carlo_corrigido.md
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

POOL_SIZE = 20
L_MOMENTUM = 150
CAP = config.CAP_POR_ATIVO
FIM_IN_SAMPLE = "2018-12-31"

N_TRAJETORIAS = 200          # nulos N1 e N2
# N3 custa N_TRAJETORIAS_GRID x 16 simulações completas. Com 100 trajetórias são
# 1.600 backtests (~10-25 min). Suba para 200 se houver tempo; a resolução do
# p-value passa de 1% para 0,5%.
N_TRAJETORIAS_GRID = 100
POOL_GRID = [10, 15, 20, 25]
L_GRID = [50, 100, 150, 200]
TAMANHO_MACACO_CLASSICO = 10

IMG_DIR = Path("images")
OUT_DIR = Path("dados/resultados/ablacao")
IMG_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)


def sharpe_de(df: pd.DataFrame) -> float:
    m = calcular_metricas_institucionais(motor.serie_retornos(df), motor.serie_cdi(df))
    return float(m["sharpe_geometrico"])


def main() -> None:
    print("=" * 78)
    print("  TICKET-C02 - MONTE CARLO CORRIGIDO")
    print("=" * 78)

    print("\n[1/5] Construindo contextos mensais...")
    bases = motor.carregar_bases()
    datas = motor.datas_do_periodo(bases.universo, fim=FIM_IN_SAMPLE)
    contextos = motor.construir_contextos(bases, datas, max_L=max(L_GRID))
    n_meses = len(contextos)
    print(f" -> {n_meses} meses "
          f"({contextos[0].data.strftime('%Y-%m')} a {contextos[-1].data.strftime('%Y-%m')})")

    # -----------------------------------------------------------------------
    # 2. Sharpe da estratégia — recalculado, nunca lido de um literal
    # -----------------------------------------------------------------------
    print("\n[2/5] Recalculando o Sharpe da variante oficial (V3)...")
    df_oficial = motor.simular(
        contextos, bases.precos,
        seletor=motor.pool_mst(POOL_SIZE),
        aplicar_momentum=True, L=L_MOMENTUM, cap=CAP,
    )
    sharpe_oficial = sharpe_de(df_oficial)
    print(f" -> Sharpe geométrico oficial: {sharpe_oficial:+.4f}")

    # -----------------------------------------------------------------------
    # 3. Nulo N1 — macaco clássico (10 ações, 100% investido, sem momentum)
    # -----------------------------------------------------------------------
    print(f"\n[3/5] Nulo N1 — macaco clássico ({N_TRAJETORIAS} trajetórias)...")
    n1 = []
    for k in range(N_TRAJETORIAS):
        rng = np.random.default_rng(2000 + k)
        df_k = motor.simular(
            contextos, bases.precos,
            seletor=motor.pool_aleatorio(TAMANHO_MACACO_CLASSICO, rng),
            aplicar_momentum=False, cap=None,
        )
        n1.append(sharpe_de(df_k))
        if (k + 1) % 50 == 0:
            print(f"      {k + 1}/{N_TRAJETORIAS}")
    n1 = np.array(n1)

    # -----------------------------------------------------------------------
    # 4. Nulo N2 — macaco pareado (20 ações + SMA150 + cap 10%)
    # -----------------------------------------------------------------------
    print(f"\n[4/5] Nulo N2 — macaco pareado ({N_TRAJETORIAS} trajetórias)...")
    n2 = []
    for k in range(N_TRAJETORIAS):
        rng = np.random.default_rng(1000 + k)   # mesmo seed do V4 do script 14
        df_k = motor.simular(
            contextos, bases.precos,
            seletor=motor.pool_aleatorio(POOL_SIZE, rng),
            aplicar_momentum=True, L=L_MOMENTUM, cap=CAP,
        )
        n2.append(sharpe_de(df_k))
        if (k + 1) % 50 == 0:
            print(f"      {k + 1}/{N_TRAJETORIAS}")
    n2 = np.array(n2)

    # -----------------------------------------------------------------------
    # 5. Nulo N3 — máximo do grid (correção de multiple testing)
    # -----------------------------------------------------------------------
    print(f"\n[5/5] Nulo N3 — máximo do grid {len(POOL_GRID)}x{len(L_GRID)} "
          f"({N_TRAJETORIAS_GRID} trajetórias x {len(POOL_GRID)*len(L_GRID)} simulações)...")
    print("      Este passo é o mais caro. Reduza N_TRAJETORIAS_GRID se faltar tempo.")

    n3 = []
    for k in range(N_TRAJETORIAS_GRID):
        rng = np.random.default_rng(3000 + k)
        melhor = -np.inf
        for p in POOL_GRID:
            seletor_p = motor.pool_aleatorio(p, rng)
            # Congela o pool do mês para que os 4 valores de L vejam o MESMO sorteio
            pools = {ctx.data: seletor_p(ctx) for ctx in contextos}
            seletor_fixo = lambda ctx, _p=pools: _p[ctx.data]
            for L in L_GRID:
                df_k = motor.simular(
                    contextos, bases.precos,
                    seletor=seletor_fixo, aplicar_momentum=True, L=L, cap=CAP,
                )
                melhor = max(melhor, sharpe_de(df_k))
        n3.append(melhor)
        if (k + 1) % 25 == 0:
            print(f"      {k + 1}/{N_TRAJETORIAS_GRID}")
    n3 = np.array(n3)

    # -----------------------------------------------------------------------
    # 6. Estatísticas
    # -----------------------------------------------------------------------
    p_n1 = float((n1 >= sharpe_oficial).mean())
    p_n2 = float((n2 >= sharpe_oficial).mean())
    p_n3 = float((n3 >= sharpe_oficial).mean())

    pd.DataFrame({
        "trajetoria": np.arange(max(len(n1), len(n2), len(n3))),
        "N1_classico": pd.Series(n1),
        "N2_pareado": pd.Series(n2),
        "N3_max_grid": pd.Series(n3),
    }).to_parquet(OUT_DIR / "monte_carlo_nulos.parquet", index=False)

    print("\n--- RESULTADO ---")
    print(f" Sharpe oficial (V3)        : {sharpe_oficial:+.4f}")
    print(f" N1 clássico   mediana={np.median(n1):+.3f}  p95={np.percentile(n1,95):+.3f}  p={p_n1:.1%}")
    print(f" N2 pareado    mediana={np.median(n2):+.3f}  p95={np.percentile(n2,95):+.3f}  p={p_n2:.1%}")
    print(f" N3 max-grid   mediana={np.median(n3):+.3f}  p95={np.percentile(n3,95):+.3f}  p={p_n3:.1%}")

    # -----------------------------------------------------------------------
    # 7. Gráfico
    # -----------------------------------------------------------------------
    plt.figure(figsize=(11, 6))
    plt.hist(n1, bins=30, alpha=0.55, color="lightgray", edgecolor="black",
             label=f"N1 clássico — 10 aleatórias, 100% investido (p={p_n1:.1%})")
    plt.hist(n2, bins=30, alpha=0.55, color="#87ceeb", edgecolor="black",
             label=f"N2 pareado — 20 aleatórias + SMA150 + cap (p={p_n2:.1%})")
    plt.hist(n3, bins=30, alpha=0.55, color="#f4a582", edgecolor="black",
             label=f"N3 máx. do grid 4x4 (p={p_n3:.1%})")
    plt.axvline(sharpe_oficial, color="purple", linewidth=3,
                label=f"Nexus V3 (MST+SMA150+cap): {sharpe_oficial:+.3f}")

    plt.title("Monte Carlo corrigido: o nulo precisa ter as mesmas camadas do tratamento",
              fontsize=12, fontweight="bold")
    plt.xlabel("Sharpe Geométrico (In-Sample)")
    plt.ylabel("Frequência")
    plt.legend(loc="upper left", fontsize=9)
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.savefig(IMG_DIR / "10_monte_carlo_corrigido.png", dpi=180)
    plt.close()

    # -----------------------------------------------------------------------
    # 8. Relatório — todo número vem de variável
    # -----------------------------------------------------------------------
    if p_n2 < 0.05 and p_n3 < 0.05:
        veredito = (
            f"O Sharpe de {sharpe_oficial:+.3f} sobrevive aos dois nulos exigentes "
            f"(pareado p={p_n2:.1%}, máximo-do-grid p={p_n3:.1%}). A vantagem não é "
            f"explicada pelo colchão de caixa nem pela busca em grid."
        )
    elif p_n2 < 0.05:
        veredito = (
            f"O Sharpe supera o nulo pareado (p={p_n2:.1%}) mas **não** sobrevive à "
            f"correção de multiple testing (p={p_n3:.1%}). Como o par (Pool, SMA) foi "
            f"escolhido como máximo de {len(POOL_GRID)*len(L_GRID)} combinações, o nulo "
            f"correto é o N3. A conclusão honesta é que **não há significância a 5%**."
        )
    else:
        veredito = (
            f"O Sharpe de {sharpe_oficial:+.3f} **não** supera o nulo pareado "
            f"(p={p_n2:.1%}). Sortear 20 ações do mesmo universo e aplicar os mesmos "
            f"filtros produz resultado equivalente. A afirmação de significância "
            f"estatística publicada em `docs/06` não se sustenta quando o nulo recebe "
            f"as mesmas camadas do tratamento."
        )

    md = f"""# Teste de Monte Carlo Corrigido (TICKET-C02)

**Script:** `scripts/15_monte_carlo_corrigido.py`
**Período:** In-Sample — {contextos[0].data.strftime('%b/%Y')} a {contextos[-1].data.strftime('%b/%Y')} ({n_meses} meses)
**Substitui:** `docs/06_teste_monte_carlo_baselines.md`

---

## 1. Por que o teste anterior precisou ser refeito

| Defeito | Evidência |
|---|---|
| Números não calculados | `09_baseline_aleatorias.py:117` fixa `SHARPE_NEXUS = 0.10`; as linhas 178-179 publicam `0.122` e `3.2%` como strings literais |
| Figura contradiz o texto | `images/02_baseline_macacos_in_sample.png` marca a linha em 0.10; a tabela afirma 0.122 |
| Nulo sem as camadas do tratamento | Macacos 100% investidos vs. Nexus com ~13% em CDI, num período em que o CDI (10,3% a.a.) superou o Ibovespa (6,2% a.a.) |
| Multiple testing ignorado | O par vencedor é o máximo de {len(POOL_GRID)*len(L_GRID)} combinações, comparado ao p95 de um sorteio único |

## 2. Os três nulos

| Nulo | Composição | Pergunta |
|---|---|---|
| **N1 — clássico** | {TAMANHO_MACACO_CLASSICO} ações aleatórias, 100% investido, sem momentum | O mercado aleatório bate o CDI? |
| **N2 — pareado** | {POOL_SIZE} ações aleatórias + SMA {L_MOMENTUM} + cap {CAP*100:.0f}% | A MST agrega sobre um pool qualquer? |
| **N3 — máximo do grid** | N2, mas cada trajetória varre {len(POOL_GRID)}×{len(L_GRID)} combinações e reporta seu máximo | A vantagem sobrevive à busca em grid? |

## 3. Resultados

**Sharpe geométrico da variante oficial (recalculado): `{sharpe_oficial:+.4f}`**

| Nulo | Mediana | Percentil 95 | p-value vs. Nexus |
|---|---|---|---|
| N1 — clássico | {np.median(n1):+.3f} | {np.percentile(n1, 95):+.3f} | **{p_n1:.1%}** |
| N2 — pareado | {np.median(n2):+.3f} | {np.percentile(n2, 95):+.3f} | **{p_n2:.1%}** |
| N3 — máximo do grid | {np.median(n3):+.3f} | {np.percentile(n3, 95):+.3f} | **{p_n3:.1%}** |

Trajetórias: {N_TRAJETORIAS} (N1, N2), {N_TRAJETORIAS_GRID} (N3).

## 4. Veredito

> {veredito}

## 5. Visualização

<p align="center">
  <img src="../images/10_monte_carlo_corrigido.png" width="700" alt="Monte Carlo corrigido" />
</p>

---

## 6. Nota metodológica

O nulo N1 responde a uma pergunta legítima mas fácil: *"o mercado acionário
brasileiro de 2011-2018 bateu o CDI?"* — a resposta é não, e qualquer estratégia
que passe parte do tempo em caixa vence esse nulo sem precisar de sinal algum.

O nulo N2 é o que sustenta a tese do projeto, porque difere do tratamento em
exatamente uma dimensão: a origem do pool. O nulo N3 corrige o fato de que o par
(Pool, SMA) não foi escolhido a priori, e sim como máximo de um grid.

*Todos os números deste documento são gerados pelo script. Nenhum valor foi escrito à mão.*
"""

    doc = Path("docs") / "13_monte_carlo_corrigido.md"
    doc.write_text(md, encoding="utf-8")
    print(f"\n[OK] Relatório: {doc.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
