# Contexto de Transição: Refatoração da Camada de Machine Learning

**Data:** 14/ago/2026
**Status:** Alerta Crítico Levantado (Risco de Data Leakage)

## O Que Aconteceu
Nós construímos a arquitetura de "Cascata" (MST -> Momentum -> Machine Learning) e executamos o script `08_backtest_alpha.py` para comparar o Momentum Puro, ML Puro e Cascata no período In-Sample (2011-2018). A Cascata apresentou um Sharpe Ratio de **0.481**, esmagando o benchmark aleatório (0.107).

## O Problema (Apontamento Externo)
Uma revisão externa (amigo + IA) levantou dois questionamentos fundamentais que ameaçam a validade do Sharpe de 0.481:

### 1. Data Leakage (Viés de Olhar o Futuro) no ML
O script `12_train_ml.py` retreinou o modelo vencedor (Regressão Logística) usando **toda a base In-Sample (2011-2018)** e o salvou em `modelos/alpha_ml_vencedor.joblib`. 
Em seguida, o script `08_backtest_alpha.py` iterou mês a mês de 2011 a 2018 usando esse modelo para prever a direção do mercado. 
**Erro Crítico:** Quando o backtest estava em 2012, ele usou um modelo que já havia sido treinado com dados até 2018. O modelo "decorou o gabarito" do futuro. Isso invalida a métrica de Sharpe gerada no In-Sample.

### 2. O Mistério do ML Puro
Se o modelo "viu o futuro", era esperado que a estratégia "ML Puro" apresentasse resultados estratosféricos. No entanto, ela teve apenas 10.9% de retorno acumulado e Sharpe de 0.100. Por que um modelo com "gabarito" foi tão mal operando sozinho?
*Hipóteses a investigar na próxima sessão:*
- Como a Regressão Logística é linear e rígida, ela não consegue "decorar" cada linha (ao contrário de uma Random Forest sem limite de profundidade). Ela apenas traçou uma reta geral.
- A quantidade de ativos selecionados pelo ML Puro pode ter sido muito alta ou muito baixa.
- Pode haver um erro na aplicação do scaler ou nas colunas do dataset de features durante o backtest mensal.

## O Plano de Ataque (Para a Próxima IA/Sessão)

1. **Refatorar o Backtest com Walk-Forward / Expanding Window:**
   O `08_backtest_alpha.py` não pode simplesmente carregar um modelo estático de `.joblib`. Para ser quantitativamente rigoroso no In-Sample, o backtest precisa simular o treinamento ao longo do tempo. Por exemplo: em 2015, o modelo só pode ser treinado com os dados de 2011 a 2014. Isso garantirá que o Sharpe gerado seja honesto.

2. **Enriquecer o Relatório da Batalha dos Filtros (`docs/08_batalha_dos_filtros_alpha.md`):**
   O documento atual está muito "seco". Precisamos adicionar contexto profundo sobre as **condições de teste e a composição da carteira**, incluindo:
   - Quantas ações (em média e distribuição) passaram pelos filtros a cada rebalanceamento?
   - Quando as ações são rejeitadas, quanto de dinheiro fica alocado em CDI?
   - O CDI protegeu a carteira ou causou perda de custo de oportunidade?
   - Inserir **gráficos de alocação** (área empilhada mostrando % em Ações vs % em CDI ao longo do tempo) e gráficos do **tamanho da carteira** (ex: "Meses onde a Cascata aprovou apenas 2 ações").

3. **Reavaliar a Batalha dos Filtros de forma Honesta:**
   Após consertar o Data Leakage (Walk-forward training), precisaremos rodar a Batalha dos Filtros novamente. Se o ML perder o seu poder preditivo e a Cascata cair abaixo do Momentum Puro, devemos acionar a **Navalha de Occam** (prevista no `divisao_tarefas_10_a_16.md`) e descartar o ML do projeto final.
