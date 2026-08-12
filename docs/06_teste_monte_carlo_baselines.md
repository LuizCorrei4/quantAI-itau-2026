# Teste de Robustez: Monte Carlo (Macacos Aleatórios)

**Objetivo:** Verificar se o Sharpe positivo obtido no *In-Sample* pelo Filtro de Momentum (L=150) possui significância estatística ou se é mero ruído de mercado.

## Parâmetros do Teste
*   **Período:** In-Sample (2011 a 2018)
*   **Simulações:** 200 caminhos de carteiras aleatórias.
*   **Composição:** 10 ações sorteadas do mesmo universo (80 ações) e com os mesmos custos operacionais.

## Resultados Estatísticos
*   **Sharpe Médio Aleatório (Ruído):** `-0.193` (Muito próximo do nosso MVP original, provando que a MST pura não gerou alpha direcional).
*   **Top 5% dos Macacos alcançaram Sharpe de:** `0.107`
*   **Sharpe do Nexus (Momentum L=150):** `0.100`
*   **P-Value:** `5.5%`

> **Diagnóstico para a Banca:** O Momentum simples conseguiu derrotar 94.5% das simulações aleatórias, ficando extremamente perto da significância estatística de 95% (p-value < 0.05). Isso justifica a necessidade de otimização dos parâmetros via Grid Search ou a introdução de uma camada de **Machine Learning** para extrair aquele Alpha adicional necessário para vencer definitivamente o acaso.

## Visualização da Distribuição
![Histograma de Monte Carlo](../images/02_baseline_macacos_in_sample.png)
