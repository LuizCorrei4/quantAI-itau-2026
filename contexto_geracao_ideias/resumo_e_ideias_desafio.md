# Resumo do Desafio Quant AI 2026 para Ideação de Estratégias

Este documento sintetiza os requisitos do Desafio Itaú Asset Quant AI 2026. O objetivo principal deste resumo é servir como contexto base (junto com análises de vencedores passados e outros materiais) para o desenvolvimento de ideias de estratégias quantitativas consistentes.

## 1. Visão Geral do Desafio
O desafio simula a rotina de pesquisa de uma gestora quantitativa, focando em:
- **Tese:** Propor uma estratégia sistemática com hipótese e racional claro.
- **Modelagem e Backtest:** Coletar dados, criar regras de entrada/saída (sinais/pesos) e rodar testes de simulação históricos transparentes e implementados pela equipe (não em formato black-box).
- **Análise e Relatório:** Desenvolver visão crítica sobre riscos, cenários de falha e apresentar tudo num documento executivo PDF de até 5 páginas (estilo apresentação).
- **IA Generativa:** O uso prático de IA (como Gemini/Claude) para apoiar alguma fase (ideação, código, revisão, branding) é estritamente obrigatório e avaliado.

## 2. Princípios de Avaliação (O que gera pontuação)
- **Conceito da Estratégia (20%):** Originalidade, lógica econômica testável, e não apenas complexidade pela complexidade.
- **Modelagem (20%):** Clareza nos dados de entrada, nas regras de processamento (que devem ser reprodutíveis) e nas saídas do modelo (trades, alocações).
- **Backtest (15%):** Rigor metodológico. Demonstração de que a equipe mitiga vieses como *look-ahead* (usar dados do futuro no passado) e sobre-otimização. Justificar o período de testes e, se possível, incluir benchmark.
- **Análise dos Resultados (15%):** A banca quer ver interpretação real, risco vs retorno, identificação sincera das falhas do modelo, e não apenas uma "estratégia mágica que sempre ganha".
- **Conclusão e Próximos Passos (10%):** Postura madura sobre limites e sugestões realistas de melhoria.
- **Uso de IA Generativa (15%):** Como a IA agregou valor ao trabalho de forma transparente.
- **Apresentação do Robô (5%):** Identidade, nome e coerência visual para a estratégia sugerida.

## 3. Elementos Técnicos para Estruturar a Ideação
Ao gerar ideias, as propostas devem possuir os seguintes componentes:
1. **Ativos:** Livre escolha (Equities, Câmbio, Juros, Crypto, Commodities, etc.).
2. **Dados:** Definir de forma realista quais dados a estratégia consome (preços, indicadores macro, sentimento, etc.) e onde obtê-los, já que os organizadores não os fornecem.
3. **Formato de Saída (Decisões):** Trade direcional, ranking *long/short*, alocação de carteira (pesos) ou regras de rebalanceamento.
4. **Complexidade Algorítmica:** O modelo quantitativo em si *não precisa* usar Machine Learning. Abordagens baseadas em estatística tradicional, análise fatorial ou regras diretas são válidas e podem vencer se bem justificadas.

> **Importante:** A excelência do trabalho não está em achar a estratégia com a maior rentabilidade histórica, mas sim a mais bem estruturada, justificada, testada com rigor e perfeitamente comunicada dentro das limitações estritas (5 páginas visuais e anônimas).
