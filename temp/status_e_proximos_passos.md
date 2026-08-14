# Status Atual e Próximos Passos do Robô Nexus

**Última Atualização:** 14/ago/2026

## ✅ O Que Já Foi Feito (Concluído)
1. **MVP Topológico:** Pipeline de dados, universo de ações, e filtro por Farness (MST) rodando de ponta a ponta (Sharpe de -0.21 In-Sample confirmou a necessidade de filtros direcionais).
2. **Filtro de Momentum:** Média Móvel Simples de 150 dias calibrada no In-Sample (melhor que 50 e 200).
3. **Machine Learning:** Features projetadas (RSI, Volatilidade) e algoritmos avaliados (Regressão Logística venceu).
4. **Arquitetura (V1):** Construímos a ideia de "Cascata" (MST -> Momentum -> ML) e escrevemos os scripts do backtest da "Batalha dos Filtros".

## 🚨 Status de Alerta (Onde Estamos Agora)
Foi descoberto um **Risco de Data Leakage (Olhar o Futuro)** no backtest da Batalha dos Filtros (`08_backtest_alpha.py`). O modelo de ML foi treinado com a totalidade do In-Sample (2011-2018) e testado contra ele mesmo.
Além disso, o comportamento do "ML Puro" foi misteriosamente baixo, levantando suspeitas de anomalias no código de predição durante o loop ou em como a Regressão Logística generalizou.

O desenvolvimento foi pausado para que esses problemas estruturais sejam sanados antes de avançarmos para o Filtro de Regime (Pessoa 2).

## ⏭️ Próximos Passos Inegociáveis (Para a Próxima Sessão)

1. **Investigar Anomalia no ML Puro:** Analisar por que a Regressão Logística treinada com "gabarito" performou mal. Verificar colunas, scaler e limites de probabilidade.
2. **Corrigir Data Leakage (Walk-Forward CV):** Alterar o código do ML para que o treinamento ocorra progressivamente dentro do loop do backtest (treinar com 2011-2014 para prever 2015, e assim por diante), garantindo validação estatisticamente rigorosa.
3. **Melhorar Documentação e Gráficos da Batalha:** Atualizar o script de backtest para gerar métricas e gráficos de **Composição de Carteira** (quantas ações o filtro aprova por mês e quanto % do portfólio acaba "escorrendo" para a segurança do CDI).
4. **Re-Veredito da Batalha dos Filtros:** Com o backtest corrigido, decidir se o ML realmente agrega Alpha ou se a Navalha de Occam cortará o ML, deixando apenas o Momentum como a Camada de Direção oficial.
5. **Avançar para Pessoa 2 (Regime Filter):** Só avançar para o Filtro de Regime Macroeconômico após os passos 1 a 4 estarem inquestionavelmente blindados contra críticas da banca.
