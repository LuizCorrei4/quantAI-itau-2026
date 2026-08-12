# Dicionário de Dados do Projeto Nexus

Esta pasta central armazena a espinha dorsal de dados da nossa estratégia quantitativa. Seguindo as boas práticas de engenharia de dados e reprodutibilidade, a arquitetura é estritamente dividida em camadas, evitando contaminação de dados e facilitando auditoria para a banca avaliadora.

## Estrutura de Diretórios

1. **`brutos/`**: A "Zona Quarentena". Contém os dados primários exatamente como extraídos da fonte (B3/BCB/Yahoo Finance). Esses arquivos são imutáveis; nenhum script deve alterá-los.
2. **`processados/`**: A "Zona de Feature Engineering". Contém os dados padronizados (ex: retornos logarítmicos, universo de ativos mensal) e a base de variáveis independentes prontas para alimentar o modelo de Machine Learning (`features_ml.parquet`).
3. **`resultados/`**: A "Zona de Saída". Armazena os artefatos gerados pelos backtests e pela Validação Cruzada (séries de retorno, alocações, grafos da MST).

Para entender detalhadamente o que cada pasta contém, leia o arquivo `README.md` dentro de cada subdiretório.
