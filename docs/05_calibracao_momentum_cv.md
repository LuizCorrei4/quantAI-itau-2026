# Calibração CV Temporal - Momentum (Pool = 20)

Este teste aplica o Filtro de Momentum em diferentes tamanhos de Média Móvel (L) e mede a **estabilidade** do Sharpe Ratio em 3 períodos distintos.

| Variante | Sharpe (Fold 1: 15-16) | Sharpe (Fold 2: 16-17) | Sharpe (Fold 3: 17-18) | Sharpe In-Sample Total |
|---|---|---|---|---|
| **L = 50** | 0.06 | 0.72 | 0.23 | **-0.23** |
| **L = 100** | -0.06 | 0.84 | 0.64 | **-0.11** |
| **L = 150** | -0.20 | 0.74 | 0.82 | **0.10** |
| **L = 200** | -0.45 | 0.41 | 0.67 | **-0.04** |
