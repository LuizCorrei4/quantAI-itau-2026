# Limite Estrutural do Filtro de Momentum (Grid Search)

**Objetivo:** Aplicar o princípio da Navalha de Occam buscando a configuração mais simples (Média Móvel) capaz de extrair Alpha direcional estatisticamente significativo do nosso universo descorrelacionado (MST).

## 1. Metodologia (Otimização Sistemática)
Para provar que a escolha de parâmetros não sofre de *cherry-picking*, executamos um Grid Search massivo no período *In-Sample* (2011-2018).

*   **Tamanho do Pool (MST):** Testamos selecionar as Top `{10, 15, 20, 25}` candidatas periféricas.
*   **Filtro de Momentum (L):** Testamos Comprimentos de Média Móvel de `{50, 100, 150, 200}` dias úteis.

O algoritmo rodou 16 caminhos de carteiras paralelos, com as mesmas premissas operacionais do MVP original (Equal-Weight e custos escorregadios).

## 2. Matriz de Sensibilidade (Heatmap)
![Heatmap Pool vs SMA](../images/03_heatmap_alpha_cv.png)

## 3. O Veredito de Occam (O Teto de Vidro)
A matriz de calor nos traz uma constatação científica crítica sobre a natureza da nossa estratégia de ações descorrelacionadas:

1.  **A Configuração Ótima:** A configuração mais robusta (quente e estável) foi alocar na vizinhança de `Pool = 20` com `SMA = 150`, gerando um Sharpe *In-Sample* de **0.100**.
2.  **A Barreira Estatística:** Conforme aferido em testes de Monte Carlo paralelos, o limiar de 95% de confiança (p-value < 0.05) para rejeitar o acaso no período é um Sharpe de **0.107**.

> **Conclusão para a Banca:** O Filtro de Momentum exauriu seu teto estrutural. Eleva o nosso MVP de um Sharpe negativo para +0.100, provando que a premissa fundamental de convicção direcional é válida. No entanto, sua simplicidade linear o impede matematicamente de ultrapassar o limiar de 95% de significância estatística de Alpha. **A Navalha de Occam falhou.** Torna-se estatisticamente justificada (e necessária) a introdução de uma camada não-linear de **Machine Learning** na arquitetura em cascata.
