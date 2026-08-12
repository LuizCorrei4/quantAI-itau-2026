# Validação Cruzada Temporal e Batalha dos Filtros

Este diretório contém os resultados (Evolução Patrimonial e Retornos Totais) de cada uma das teses e hiperparâmetros que testamos na fase *In-Sample* (2011-2018).
Eles provam para a banca que o nosso processo de seleção não sofre de *cherry-picking* ou sobreajuste.

## Artefatos Gerados
1. **Calibração do Momentum (`serie_retornos_momentum_L_*_Pool20.parquet`)**: O Grid Search (script 10) testa múltiplos comprimentos de médias móveis para achar o teto de rentabilidade linear (L=150 provou ser ótimo).
2. **A Batalha dos Filtros (`serie_retornos_batalha_*.parquet`)**: O resultado final simulando:
   * **Momentum_Puro**: Apenas ações em tendência de alta.
   * **ML_Puro**: Regressão Logística operando sozinha.
   * **Cascata**: Momentum servindo de filtro grosso, e Machine Learning selecionando a dedo os ativos restantes. O vencedor indiscutível com Sharpe 0.481!

Esses arquivos são a espinha dorsal de evidências que geram os relatórios Markdowns em `docs/05_...` até `docs/08_...`.
