# Resultados dos Experimentos (Artefatos de Saída)

Esta pasta abriga os subprodutos das execuções de simulação, servindo de base de prova matemática para os gráficos contidos no relatório oficial (`docs/`).

## Conteúdo Raiz
* **`farness_completa.parquet`**: O log contínuo gerado pelo orquestrador indicando o valor de centralidade (Farness) de todos os ativos analisados mensalmente via Minimum Spanning Tree (MST). Ativos com o **maior** Farness são os mais periféricos (descorrelacionados sistemicamente), porque a Farness é a **soma das distâncias** do nó até todos os demais: quanto maior a soma, mais afastado do miolo da rede. Ativos com **menor** Farness são os centrais (blue chips sistêmicas).

  > **Correção (15/ago/2026 — TICKET-C07):** esta descrição estava invertida. O código sempre esteve correto — [`selecionar_top_n`](../../src/nexus/portfolio.py) ordena com `ascending=False` e pega o topo. Era o README que contradizia a tese; se a frase antiga tivesse chegado ao relatório final, inverteria a estratégia inteira.
* **`pesos_historicos.parquet`**: Histórico da alocação de capital oficial mês a mês.
* Subdiretórios específicos (como `cv_temporal/`) contêm detalhamentos por tese/experimento.
