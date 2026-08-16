# TICKET-C02 — Corrigir o teste de Monte Carlo

**Prioridade:** 🔴 Crítica
**Estimativa:** 2h
**Critério afetado:** Backtest (15%)
**Entregável:** `scripts/15_monte_carlo_corrigido.py`, `docs/13_monte_carlo_corrigido.md`

---

## Contexto

O teste dos macacos é o argumento estatístico central do projeto. Hoje ele tem
três defeitos independentes, e cada um sozinho já derruba a conclusão.

### Defeito 1 — os números do relatório não são calculados

Em [`09_baseline_aleatorias.py:117`](../scripts/09_baseline_aleatorias.py#L117):

```python
SHARPE_NEXUS = 0.10                                  # hardcoded
p_value = np.mean(sharpes_macacos >= SHARPE_NEXUS)   # calculado contra 0.10
```

Mas o markdown gerado escreve, como **strings literais** dentro da f-string
([linhas 178-179](../scripts/09_baseline_aleatorias.py#L178-L179)):

```python
*   **Sharpe do Nexus (Momentum L=150 + Cap 10%):** `0.122`
*   **P-Value:** `3.2%`
```

O `p_value` que o script calcula nunca é escrito no documento. O `3.2%` que o
documento publica nunca é calculado. E o gráfico entregue à banca
(`images/02_baseline_macacos_in_sample.png`) desenha a linha do Nexus em **0,10**,
contradizendo a tabela que afirma **0,122**.

> O número pode até estar certo. Mas não é auditável, e a figura contradiz o texto.

### Defeito 2 — o nulo está confundido com o tratamento

Os macacos recebem `calcular_pesos_equal_weight(candidatas_macaco)` **sem o argumento
`cap`** ([linha 86](../scripts/09_baseline_aleatorias.py#L86)). Logo: 10 ações × 10% =
**100% investido em bolsa, sempre**.

O Nexus, com o cap de 10%, manteve em média **12,9% em CDI**. No período 2011-2018 o
CDI rendeu **10,3% a.a.** contra **6,2%** do Ibovespa. Ficar parcialmente em caixa
*naquele período específico* aumenta retorno e corta volatilidade — sem nenhuma
relação com topologia ou momentum.

A diferença medida entre Nexus e macacos mistura três efeitos que ninguém separou:
seleção topológica, filtro de momentum e colchão de caixa.

### Defeito 3 — multiple testing

O par vencedor (Pool=20, SMA=150) é o **máximo de um grid de 16 combinações**
(`10_grid_search_alpha.py`). Esse máximo é comparado contra o percentil 95 de um
**sorteio único**. São distribuições diferentes: o máximo de 16 variantes
correlacionadas ultrapassa o p95 de um sorteio único com frequência muito maior que 5%.

---

## O que fazer

Escrever `scripts/15_monte_carlo_corrigido.py` que:

1. **Lê o Sharpe oficial do arquivo, nunca de um literal.** A série está em
   `dados/resultados/cv_temporal/serie_retornos_batalha_Momentum_Puro.parquet`
   (gerada pelo script `08`). Calcular o Sharpe com
   `calcular_metricas_institucionais` — a mesma função do resto do projeto.

2. **Roda dois nulos, não um:**

   | Nulo | Composição | Pergunta que responde |
   |---|---|---|
   | **N1 — macaco clássico** | 10 ações aleatórias, 100% investido | "o mercado aleatório bate o CDI?" |
   | **N2 — macaco pareado** | 20 ações aleatórias **+ SMA 150 + cap 10%** | "a MST agrega sobre um pool qualquer?" |

   N2 é o teste que importa. Ele difere do Nexus em **exatamente uma coisa**: o pool
   vem de sorteio em vez de vir da farness da MST.

3. **Correção de multiple testing.** Para cada uma das 200 trajetórias do nulo N2,
   varrer o mesmo grid de 16 combinações (Pool × SMA) e guardar o **máximo**. A
   distribuição desses máximos é o nulo correto para um Sharpe que também foi
   escolhido como máximo de um grid. Reportar os dois p-values lado a lado:
   - p bruto (contra a distribuição de sorteio único);
   - p corrigido (contra a distribuição dos máximos).

4. **Todo número no markdown vem de f-string com variável.** Zero literais.

5. **Marcar `09_baseline_aleatorias.py` como superseded** com um banner no topo,
   para ninguém rodá-lo por engano e sobrescrever `docs/06`.

## Critério de aceite

- [ ] Nenhum literal numérico no markdown gerado — `grep -nE "0\.1[0-9]{2}|3\.2%" scripts/15_*.py` retorna vazio
- [ ] O gráfico marca o Sharpe real, lido do parquet
- [ ] Os dois nulos (N1 e N2) aparecem no mesmo histograma
- [ ] p bruto **e** p corrigido reportados
- [ ] `09_baseline_aleatorias.py` com banner de superseded
- [ ] Se o p corrigido passar de 5%: **dizer isso no documento**, não esconder
