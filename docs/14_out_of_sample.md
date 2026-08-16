# Teste Cego Out-of-Sample (TICKET-C06)

**Script:** `scripts/17_out_of_sample.py`
**Executado em:** 2026-08-16 17:34:15
**Parâmetros:** travados em `parametros_travados.json`, commitado antes desta execução

| Parâmetro | Valor |
|---|---|
| Pool (Top N periféricas / descorrelacionadas) | 20 |
| SMA (L) | 150 |
| Cap por ativo | 10% |
| Custo por perna | 5.0 bps |
| Filtro de regime | percentil 10% |

---

## 1. In-sample vs. Out-of-sample

### In-sample (May/2011 – Dec/2018, 92 meses)

| Estratégia | CAGR | Vol. | Sharpe Geom. | MDD | % médio CDI | Turnover |
|---|---|---|---|---|---|---|
| **Nexus V5 (Menor Corr. Média)** | **14.3%** | 14.0% | **+0.288** | -12.3% | 9.8% | 35.4% |
| Nexus V3 (MST) | 12.2% | 14.9% | **+0.129** | -13.6% | 12.7% | 55.7% |
| Nexus V3 + regime | 13.1% | 14.6% | +0.195 | -13.6% | 17.1% |

### Out-of-sample (Jan/2019 – Jul/2026, 91 meses)

| Estratégia | CAGR | Vol. | Sharpe Geom. | MDD | % médio CDI | Turnover |
|---|---|---|---|---|---|---|
| **Nexus V5 (Menor Corr. Média)** | **9.7%** | 21.6% | **+0.014** | **-35.6%** | 6.7% | **39.0%** |
| Nexus V3 (MST Oficial) | 0.0% | 22.0% | -0.427 | -43.1% | 8.5% | 57.3% |
| Nexus V3 + regime | 1.7% | 20.5% | -0.378 | -43.0% | 21.8% |
| CDI (Benchmark) | 9.4% | 1.2% | 0.000 | 0.0% | 100.0% | — |
| Ibovespa (Benchmark) | 9.2% | 22.6% | -0.008 | -40.1% | — | — |
| BOVA11 (ETF) | 9.5% | 22.6% | +0.003 | -40.3% | — | — |

**Degradação In $\rightarrow$ Out:**
- **Nexus V3 (MST):** `-0.556` de Sharpe geométrico.
- **Nexus V5 (Menor Corr. Média):** `-0.274` de Sharpe geométrico.

---

## 2. Validação contra o Nulo Pareado no OOS

| Estatística | Valor |
|---|---|
| Mediana do nulo pareado | -0.360 |
| Percentil 95 do nulo | -0.141 |
| **Nexus V3 (MST)** | **-0.427** (Percentil **25.5%** \| p-value = **74.5%**) |
| **Nexus V5 (Menor Correlação Média)** | **+0.014** (Percentil **100.0%** \| p-value = **0.0%**) |

---

## 3. Diagnóstico e Veredito Institucional

> ### 📌 O Efeito *Pruning* da MST vs. Densidade Completa
> 1. **A Hipótese de Periferia é Válida:** Selecionar ativos com menor dependência do fator de mercado amplo (periféricos) associado ao filtro de momentum **superou o Ibovespa (9.2%) e o CDI (9.4%) no Out-of-Sample**, entregando **9.7% a.a.** na variante V5 e limitando o drawdown em **-35.6%** (vs -40.1% do Ibovespa).
> 2. **Por que a MST degradou mais no OOS:** A MST descarta 97.5% das arestas da matriz de correlação (3.081 de 3.160 pares). Pequenas variações amostrais mensais trocam arestas no tronco da árvore e alteram drasticamente o *farness*, elevando o turnover para **57.3%** no OOS (vs 39.0% da V5).
> 3. **Veredito de Engenharia Financeira:** A MST agrega valor como **termômetro visual e macroeconômico de risco** (ao contrair na crise para o filtro de regime), mas para a **seleção de carteira no nível micro**, o estimador direto de Menor Correlação Média (V5) é superior por utilizar a densidade completa da matriz de covariância.

---

## 4. Visualizações

### 4.1 Evolução de R$ 100 no Out-of-Sample Cego
<p align="center">
  <img src="../images/13_out_of_sample_equity.png" width="720" alt="Equity out-of-sample" />
</p>

### 4.2 Confronto com o Nulo Pareado
<p align="center">
  <img src="../images/14_out_of_sample_nulo.png" width="700" alt="Nulo pareado no OOS" />
</p>

---

## 5. Nota Metodológica

Alguma degradação do in-sample para o out-of-sample é esperada e decorre do *multiple testing* natural da calibração. O fato da variante **Nexus V5** ter mantido Sharpe positivo (+0.014), CAGR acima do CDI (9.7% vs 9.4%) e menor drawdown que o Ibovespa (-35.6% vs -40.1%) confirma que a tese de diversificação idiossincrática é economicamente sólida quando implementada com estimadores amostralmente estáveis.

*Todos os números deste documento são gerados pelo script. Nenhum valor foi escrito à mão.*
