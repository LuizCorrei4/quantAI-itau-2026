# Dados Processados (Silver / Gold Tier)

Esta camada contém os dados padronizados, limpos e enriquecidos pelos nossos algoritmos do diretório `src/nexus/`. 
É aqui que o "motor de ingestão" joga a informação estruturada para ser consumida pelos scripts de Backtest e Treinamento de ML.

## Artefatos Principais (Atualizados)

* **`precos_ajustados.parquet`**: Base matricial contendo apenas os fechamentos ajustados a proventos. Índice = Datetime, Colunas = Tickers. (Sem valores nulos interpolados erroneamente).
* **`retornos_log.parquet`**: Retornos logarítmicos ($ln(P_t/P_{t-1})$). Usado exclusivamente para a construção do grafo de distâncias topológicas da MST, dada sua melhor propriedade aditiva.
* **`universo_mensal.parquet`**: Mapeamento rigoroso de quais ativos tinham liquidez suficiente (Top 80) e compunham o IBOV em cada janela mensal. Garante zero sobrevivência ou look-ahead bias na seleção de candidatas.
* **`cdi_diario.parquet`**: Fator de rendimento para a parcela do portfólio não alocada em ações.
* **`features_ml.parquet`**: (Novo Missão 5) - O *dataset* oficial de variáveis independentes (RSI, Volatilidade 21d, Razões de SMA) e a variável alvo binária. Consumido primariamente pelo `12_train_ml.py` para ensinar a Regressão Logística a encontrar Alpha.
