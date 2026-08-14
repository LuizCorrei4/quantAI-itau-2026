# Calibração Temporal do Filtro de Momentum (Pool = 20)

**Objetivo:** Avaliar a estabilidade intertemporal do Filtro de Momentum em diferentes janelas de Média Móvel Simples ($L \in \{50, 100, 150, 200\}$ dias úteis) sobre o pool de 20 ações periféricas da MST.

---

## 1. Desempenho por Folds Temporais In-Sample (2011–2018)

| Variante de Média Móvel | Sharpe (Fold 1: 2011–2014) | Sharpe (Fold 2: 2014–2016) | Sharpe (Fold 3: 2016–2018) | Sharpe In-Sample Total (Com Cap 10%) |
|---|---|---|---|---|
| **SMA 50 dias** | -0.18 | +0.45 | +0.18 | **-0.120** |
| **SMA 100 dias** | -0.12 | +0.58 | +0.42 | **-0.015** |
| **SMA 150 dias (Ótimo)** | **-0.05** | **+0.62** | **+0.68** | **+0.122** |
| **SMA 200 dias** | -0.15 | +0.39 | +0.51 | **+0.040** |

---

## 2. Conclusão Metodológica
A janela de **SMA = 150 dias úteis** demonstrou ser a mais estável e resiliente entre os diferentes ciclos de mercado brasileiros (crise de commodities de 2014-2015 e recuperação de 2016-2018), sendo eleita como a parametrização oficial para o Grid Search e para a Batalha dos Filtros.
