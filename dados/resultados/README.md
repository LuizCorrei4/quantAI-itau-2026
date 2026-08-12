# Resultados dos Experimentos (Artefatos de Saída)

Esta pasta abriga os subprodutos das execuções de simulação, servindo de base de prova matemática para os gráficos contidos no relatório oficial (`docs/`).

## Conteúdo Raiz
* **`farness_completa.parquet`**: O log contínuo gerado pelo orquestrador indicando o valor de centralidade (Farness) de todos os ativos analisados mensalmente via Minimum Spanning Tree (MST). Ativos com o menor Farness são os mais periféricos (descorrelacionados sistemicamente).
* **`pesos_historicos.parquet`**: Histórico da alocação de capital oficial mês a mês.
* Subdiretórios específicos (como `cv_temporal/`) contêm detalhamentos por tese/experimento.
