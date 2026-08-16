# Tickets de Correção — Auditoria Metodológica do Robô Nexus

**Criado em:** 15/ago/2026
**Origem:** auditoria independente do código e dos documentos `docs/01` a `docs/11`
**Deadline do desafio:** 17/ago/2026

---

## Por que estes tickets existem

A auditoria encontrou seis problemas que, se chegarem ao PDF final como estão,
custam nota exatamente nos critérios de maior peso (Conceito 20%, Modelagem 20%,
Backtest 15%, Análise 15%). Nenhum deles é bug de sintaxe — todos são erros de
**inferência**: o código roda, produz números, e os números não sustentam a
conclusão que os documentos tiram deles.

O problema central em uma frase:

> **A contribuição da MST nunca foi medida.** O teste de Monte Carlo compara
> "MST + Momentum + colchão de caixa" contra "10 ações aleatórias 100% investidas",
> e atribui toda a diferença à MST. As três camadas nunca foram separadas.

---

## Ordem de execução

```
C01 (congelar snapshot)
  │
  ├─→ C02 (Monte Carlo corrigido) ──┐
  ├─→ C03 (tabela de atribuição) ───┤
  ├─→ C04 (CV temporal reprodutível)┤
  └─→ C05 (filtro de regime mínimo) ┘
                                     │
                                     └─→ C06 (out-of-sample cego) ─→ C07 (consolidação)
```

`C01` bloqueia tudo. `C02` a `C05` são paralelizáveis entre pessoas.
**`C06` só pode rodar uma vez, e só depois de C02–C05 fecharem.**

---

## Índice

| # | Ticket | Prioridade | Critério afetado | Bloqueia |
|---|---|---|---|---|
| C01 | [Congelar snapshot de dados](TICKET-C01-congelar-snapshot-dados.md) | 🔴 Crítica | Backtest (15%) | todos |
| C02 | [Corrigir o teste de Monte Carlo](TICKET-C02-corrigir-monte-carlo.md) | 🔴 Crítica | Backtest (15%) | C06, C07 |
| C03 | [Tabela de atribuição (ablação)](TICKET-C03-tabela-atribuicao.md) | 🔴 Crítica | **Conceito (20%)** | C06, C07 |
| C04 | [CV temporal reprodutível](TICKET-C04-cv-temporal-reprodutivel.md) | 🟡 Importante | Backtest (15%) | C07 |
| C05 | [Filtro de regime mínimo](TICKET-C05-filtro-regime-minimo.md) | 🟡 Importante | Modelagem (20%) | C06, C07 |
| C06 | [Out-of-sample cego](TICKET-C06-out-of-sample-cego.md) | 🔴 Crítica | Backtest + Análise (30%) | C07 |
| C07 | [Consolidação dos documentos](TICKET-C07-consolidacao-documentos.md) | 🔴 Crítica | Análise + Conclusão (25%) | — |

> 📋 **[ACHADOS_DA_AUDITORIA.md](ACHADOS_DA_AUDITORIA.md)** — evidência completa de
> cada achado, defeitos novos encontrados durante a implementação, e o estado exato
> do que foi codificado vs. o que ainda precisa ser executado.

---

## Estado da implementação (15/ago/2026)

| Ticket | Código | Execução |
|---|---|---|
| C01 | — (usa scripts 01-05 existentes) | ⏳ pendente |
| C02 | ✅ `scripts/15_monte_carlo_corrigido.py` | ⏳ pendente |
| C03 | ✅ `scripts/14_ablacao_atribuicao.py` | ⏳ pendente |
| C04 | ✅ `scripts/18_cv_temporal.py` | ⏳ pendente |
| C05 | ✅ `src/nexus/regime.py` + `scripts/16_calibracao_regime.py` | ⏳ pendente |
| C06 | ✅ `scripts/17_out_of_sample.py` | ⏳ pendente |
| C07 | 🔶 parcial — farness e banner do script 09 corrigidos | ⏳ resto depende dos números |

Infraestrutura comum: [`src/nexus/motor.py`](../src/nexus/motor.py) — motor de
simulação único, para que tratamento e nulo passem pelo mesmo caminho de código.

**Nenhum script foi executado.** Ver a ressalva de escopo em
[ACHADOS_DA_AUDITORIA.md](ACHADOS_DA_AUDITORIA.md).

---

## Princípio que atravessa todos os tickets

> **Nenhum número em `docs/` pode existir sem um script que o gere.**

O modo de falha que esta auditoria encontrou não foi look-ahead bias — foi
**número órfão**: valor escrito à mão dentro de um relatório, sem código por trás,
que depois vira premissa de outra conclusão. Três casos concretos:

| Onde | Número órfão | Consequência |
|---|---|---|
| `09_baseline_aleatorias.py:178-179` | `0.122` e `3.2%` são strings literais dentro da f-string | O p-value do projeto nunca foi calculado |
| `09_baseline_aleatorias.py:117` | `SHARPE_NEXUS = 0.10` hardcoded | O gráfico entregue mostra 0,10; o texto afirma 0,122 |
| `docs/05_calibracao_momentum_cv.md` | Tabela de 3 folds | Nenhum script gera esse arquivo |

Ao fechar cada ticket, a pergunta de aceite é sempre a mesma: *se a banca pedir
para regerar este número do zero, o comando existe?*
