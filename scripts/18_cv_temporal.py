"""
===============================================================================
PROJETO NEXUS - DESAFIO ITAÚ ASSET QUANT AI 2026
TICKET-C04 - Validação Cruzada Temporal Reprodutível
Arquivo: scripts/18_cv_temporal.py
===============================================================================

POR QUE ESTE SCRIPT EXISTE:
---------------------------
`docs/05_calibracao_momentum_cv.md` publica uma tabela de 3 folds que NENHUM
script gera, e cujos números não fecham: dois folds a +0.62 e +0.68, um a -0.05,
e um total in-sample de +0.122. Uma média ponderada por duração daria algo perto
de +0.37. A tabela também usa sub-períodos contíguos, não os folds com janela
expansível que o plano-mestre especifica na Parte 3.1.1.

Este script substitui aquela tabela por uma gerada de verdade.

O QUE "TREINAR" SIGNIFICA AQUI:
-------------------------------
O filtro de momentum não tem parâmetros ajustados por otimização — é uma regra
binária (preço > SMA). "Treinar" significa apenas ESCOLHER (Pool, L). Portanto a
pergunta que a CV responde é:

    O par vencedor é o mesmo nos três folds, ou muda conforme o sub-período?

O critério do plano-mestre é explícito:
    "Se cada fold elege um L diferente -> o sinal é fraco e deve ser reportado
     honestamente."

FOLDS (Parte 3.1.1 do plano-mestre):
------------------------------------
  Fold 1: treino 2011-2014  ->  validação 2015-2016
  Fold 2: treino 2011-2015  ->  validação 2016-2017
  Fold 3: treino 2011-2016  ->  validação 2017-2018

SAÍDAS:
-------
  dados/resultados/ablacao/cv_temporal.parquet
  images/12_cv_temporal_estabilidade.png
  docs/05_calibracao_momentum_cv.md  (SOBRESCRITO com números reproduzíveis)
===============================================================================
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.nexus import config, motor
from src.nexus.portfolio import calcular_metricas_institucionais

POOL_GRID = [10, 15, 20, 25]
L_GRID = [50, 100, 150, 200]
CAP = config.CAP_POR_ATIVO

FOLDS = [
    ("Fold 1", ("2011-01-01", "2014-12-31"), ("2015-01-01", "2016-12-31")),
    ("Fold 2", ("2011-01-01", "2015-12-31"), ("2016-01-01", "2017-12-31")),
    ("Fold 3", ("2011-01-01", "2016-12-31"), ("2017-01-01", "2018-12-31")),
]

IMG_DIR = Path("images")
OUT_DIR = Path("dados/resultados/ablacao")
IMG_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)


def sharpe_janela(contextos, precos, pool, L, inicio, fim) -> float:
    """Sharpe geométrico de uma configuração restrita a uma janela de datas."""
    sub = [c for c in contextos
           if pd.Timestamp(inicio) <= c.data <= pd.Timestamp(fim)]
    if len(sub) < 6:
        return float("nan")
    df = motor.simular(sub, precos, seletor=motor.pool_mst(pool),
                       aplicar_momentum=True, L=L, cap=CAP)
    m = calcular_metricas_institucionais(motor.serie_retornos(df), motor.serie_cdi(df))
    return float(m["sharpe_geometrico"])


def main() -> None:
    print("=" * 78)
    print("  TICKET-C04 - VALIDAÇÃO CRUZADA TEMPORAL")
    print("=" * 78)

    print("\n[1/3] Construindo contextos mensais (in-sample completo)...")
    bases = motor.carregar_bases()
    datas = motor.datas_do_periodo(bases.universo, fim="2018-12-31")
    contextos = motor.construir_contextos(bases, datas, max_L=max(L_GRID))
    print(f" -> {len(contextos)} meses")

    print("\n[2/3] Rodando o grid em cada fold...")
    registros = []
    resumo_folds = []

    for nome, (tr_ini, tr_fim), (va_ini, va_fim) in FOLDS:
        print(f"\n  {nome}: treino {tr_ini[:4]}-{tr_fim[:4]} | "
              f"validação {va_ini[:4]}-{va_fim[:4]}")

        grid_treino, grid_valida = {}, {}
        for p in POOL_GRID:
            for L in L_GRID:
                s_tr = sharpe_janela(contextos, bases.precos, p, L, tr_ini, tr_fim)
                s_va = sharpe_janela(contextos, bases.precos, p, L, va_ini, va_fim)
                grid_treino[(p, L)] = s_tr
                grid_valida[(p, L)] = s_va
                registros.append({"fold": nome, "pool": p, "L": L,
                                  "sharpe_treino": s_tr, "sharpe_validacao": s_va})

        melhor_treino = max(grid_treino, key=lambda k: (grid_treino[k]
                            if not np.isnan(grid_treino[k]) else -np.inf))
        melhor_valida = max(grid_valida, key=lambda k: (grid_valida[k]
                            if not np.isnan(grid_valida[k]) else -np.inf))

        resumo_folds.append({
            "fold": nome,
            "melhor_treino": melhor_treino,
            "sharpe_treino": grid_treino[melhor_treino],
            "sharpe_validacao_do_escolhido": grid_valida[melhor_treino],
            "melhor_validacao": melhor_valida,
            "sharpe_melhor_validacao": grid_valida[melhor_valida],
        })

        print(f"    melhor no treino     : Pool={melhor_treino[0]}, SMA={melhor_treino[1]} "
              f"(Sharpe {grid_treino[melhor_treino]:+.3f})")
        print(f"    esse par na validação: Sharpe {grid_valida[melhor_treino]:+.3f}")
        print(f"    melhor na validação  : Pool={melhor_valida[0]}, SMA={melhor_valida[1]} "
              f"(Sharpe {grid_valida[melhor_valida]:+.3f})")

    df_reg = pd.DataFrame(registros)
    df_reg.to_parquet(OUT_DIR / "cv_temporal.parquet", index=False)

    # -----------------------------------------------------------------------
    # 3. Estabilidade
    # -----------------------------------------------------------------------
    escolhidos_treino = [r["melhor_treino"] for r in resumo_folds]
    escolhidos_valida = [r["melhor_validacao"] for r in resumo_folds]
    estavel_treino = len(set(escolhidos_treino)) == 1
    estavel_valida = len(set(escolhidos_valida)) == 1

    # Sharpe in-sample completo da configuração oficial (Pool=20, SMA=150)
    s_oficial = sharpe_janela(contextos, bases.precos, 20, 150, "2011-01-01", "2018-12-31")

    print(f"\n[3/3] Estabilidade:")
    print(f" -> vencedores por treino   : {escolhidos_treino} -> "
          f"{'ESTÁVEL' if estavel_treino else 'INSTÁVEL'}")
    print(f" -> vencedores por validação: {escolhidos_valida} -> "
          f"{'ESTÁVEL' if estavel_valida else 'INSTÁVEL'}")
    print(f" -> Sharpe in-sample completo de (Pool=20, SMA=150): {s_oficial:+.3f}")

    # Heatmap de validação por fold
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.6))
    for ax, (nome, _, _) in zip(axes, FOLDS):
        sub = df_reg[df_reg["fold"] == nome]
        pivot = sub.pivot(index="pool", columns="L", values="sharpe_validacao")
        sns.heatmap(pivot, annot=True, fmt=".2f", cmap="RdYlGn", center=0,
                    ax=ax, cbar=False, linewidths=0.5)
        ax.set_title(f"{nome} — Sharpe na validação", fontweight="bold", fontsize=10)
        ax.set_xlabel("SMA (L)")
        ax.set_ylabel("Pool (Top N)")
    plt.suptitle("Estabilidade do par (Pool, SMA) entre folds temporais",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(IMG_DIR / "12_cv_temporal_estabilidade.png", dpi=180)
    plt.close()

    # -----------------------------------------------------------------------
    # Relatório
    # -----------------------------------------------------------------------
    tabela = ""
    for r in resumo_folds:
        tabela += (
            f"| {r['fold']} | Pool={r['melhor_treino'][0]}, SMA={r['melhor_treino'][1]} | "
            f"{r['sharpe_treino']:+.3f} | {r['sharpe_validacao_do_escolhido']:+.3f} | "
            f"Pool={r['melhor_validacao'][0]}, SMA={r['melhor_validacao'][1]} | "
            f"{r['sharpe_melhor_validacao']:+.3f} |\n"
        )

    tabela_l150 = ""
    for r in resumo_folds:
        sub = df_reg[(df_reg["fold"] == r["fold"]) & (df_reg["pool"] == 20)]
        linha = f"| {r['fold']} |"
        for L in L_GRID:
            v = sub[sub["L"] == L]["sharpe_validacao"]
            linha += f" {float(v.iloc[0]):+.3f} |" if len(v) else " — |"
        tabela_l150 += linha + "\n"

    if estavel_valida:
        veredito = (
            f"O par vencedor é **o mesmo nos três folds de validação** "
            f"(Pool={escolhidos_valida[0][0]}, SMA={escolhidos_valida[0][1]}). "
            f"Isso é evidência de que a escolha não depende de um sub-período específico."
        )
    else:
        veredito = (
            f"**O par vencedor muda a cada fold**: {escolhidos_valida[0]}, "
            f"{escolhidos_valida[1]} e {escolhidos_valida[2]}. Pelo critério do próprio "
            f"plano-mestre (Parte 3.1.1), isso significa que **o sinal é fraco** e a "
            f"escolha de (Pool=20, SMA=150) reflete o desempenho médio no in-sample "
            f"inteiro, não uma regularidade estável no tempo. Deve ser reportado assim."
        )

    md = f"""# Calibração Temporal do Filtro de Momentum (TICKET-C04)

**Script:** `scripts/18_cv_temporal.py`
**Substitui:** a tabela anterior deste arquivo, que não era gerada por nenhum script
e cujos números não fechavam com o total in-sample.

---

## 1. Desenho da validação

O filtro de momentum não tem parâmetros ajustados por otimização — é uma regra
binária (preço > SMA). "Treinar" aqui significa apenas **escolher** o par
(Pool, SMA). A pergunta que a validação cruzada responde é de **estabilidade**:

> O par vencedor é o mesmo em todos os folds, ou muda conforme o sub-período?

Folds com janela expansível, conforme a Parte 3.1.1 do plano-mestre:

| Fold | Treino | Validação |
|---|---|---|
| Fold 1 | 2011–2014 | 2015–2016 |
| Fold 2 | 2011–2015 | 2016–2017 |
| Fold 3 | 2011–2016 | 2017–2018 |

## 2. Resultado por fold

| Fold | Melhor no treino | Sharpe (treino) | Esse par na **validação** | Melhor na validação | Sharpe |
|---|---|---|---|---|---|
{tabela}
A coluna que importa é a quarta: **o desempenho, fora da amostra de escolha, do par
que teria sido escolhido**. A diferença entre ela e a última coluna é o custo da
escolha de parâmetro.

## 3. Sensibilidade ao L (Pool = 20, Sharpe na validação)

| Fold | SMA 50 | SMA 100 | SMA 150 | SMA 200 |
|---|---|---|---|---|
{tabela_l150}
## 4. Veredito

> {veredito}

**Sharpe in-sample completo de (Pool=20, SMA=150): `{s_oficial:+.3f}`**

### Ressalva sobre o Fold 1

Os quatro valores de L têm períodos de aquecimento diferentes: o filtro só opera
depois de acumular L pregões de histórico. Com dados começando em 03/01/2011, a
SMA 200 fica inativa (100% CDI) por cerca de quatro meses a mais que a SMA 50.
No Fold 1 — o mais próximo do início da amostra — isso favorece mecanicamente os
L curtos nos meses iniciais, porque os L longos ficam parados em CDI. A comparação
entre valores de L é limpa nos Folds 2 e 3, e deve ser lida com essa ressalva no
Fold 1.

## 5. Visualização

<p align="center">
  <img src="../images/12_cv_temporal_estabilidade.png" width="900" alt="Estabilidade entre folds" />
</p>

---

*Todos os números deste documento são gerados por `scripts/18_cv_temporal.py`.
Nenhum valor foi escrito à mão.*
"""

    doc = Path("docs") / "05_calibracao_momentum_cv.md"
    doc.write_text(md, encoding="utf-8")
    print(f"\n[OK] Relatório: {doc.resolve()}")
    print("=" * 78)


if __name__ == "__main__":
    main()
