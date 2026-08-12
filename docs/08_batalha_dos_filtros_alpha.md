# Batalha dos Filtros de Alpha (O Veredito Final)

Este documento registra a decisão da equipe quantitativa sobre a inclusão ou não de Machine Learning na camada de direção do portfólio. 
A métrica a ser batida para provar validade estatística (p-value < 5%) foi extraída no teste de Monte Carlo: **Sharpe 0.107**.

## Lutadores
1. **Momentum Puro**: Top 20 ações periféricas filtradas por SMA 150.
2. **ML Puro**: Top 20 ações periféricas filtradas por Regressão Logística.
3. **Cascata**: Top 20 ações periféricas filtradas por SMA 150, e o que sobra filtrado pelo ML.

## Resultados do Período In-Sample (2011-2018)
| Estratégia | Retorno Anualizado | Volatilidade | Sharpe Ratio | Bateu os Macacos? (>0.107) |
|---|---|---|---|---|
| **Momentum Puro** | 12.0% | 16.7% | **0.100** | ❌ NÃO |
| **ML Puro** | 10.9% | 6.0% | **0.100** | ❌ NÃO |
| **Cascata** | 15.5% | 10.9% | **0.481** | ✅ SIM |

## O Veredito de Occam
> O modelo em Cascata (Momentum + ML) conseguiu transcender a barreira do acaso imposta pelo mercado! A Regressão Logística agregou Alpha direcional real em cima do Momentum simples. A **Navalha de Occam aprova** a complexidade, pois ela se pagou com significância estatística. O Filtro em Cascata será o oficial no teste Out-of-Sample.