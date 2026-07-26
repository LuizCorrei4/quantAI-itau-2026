# Guia de Primeiros Passos e FAQ — Desafio Quant AI 2026

Material de orientação inicial elaborado pela **Itaú Asset Management** para auxiliar as equipes nos primeiros passos do **Desafio Quant AI 2026**.

> **Nota:** Este não é o documento definitivo da entrega final (cujas instruções detalhadas e prazos formais constam nos editais específicos), mas estabelece a base conceitual e técnica para o início dos trabalhos.

---

## 1. Visão Geral do Desafio

O desafio consiste em desenvolver uma **estratégia sistemática de investimento**, baseada em dados, e avaliar como ela teria se comportado ao longo do tempo.

Em termos práticos, espera-se que a equipe execute o seguinte fluxo:

1. **Definir uma tese ou hipótese de pesquisa:** Uma ideia de investimento simples ou sofisticada, desde que seja um processo objetivo.
2. **Transformar a ideia em um modelo quantitativo:** Construir um processo que receba dados, aplique uma lógica estruturada e gere decisões de investimento.
3. **Realizar um backtest:** Aplicar o modelo sobre dados históricos para simular seu desempenho passado.
4. **Analisar criticamente os resultados:** Avaliar riscos, limitações, consistência e comportamento do modelo (não apenas retorno financeiro).
5. **Utilizar Inteligência Artificial Generativa (GenAI):** Aplicar ferramentas de GenAI obrigatoriamente em ao menos uma etapa do desenvolvimento.

---

## 2. Estrutura Conceitual do Projeto

Todo projeto deve seguir o fluxo fundamental:

```
[Entrada de Dados] ──> [Processamento do Modelo] ──> [Geração da Decisão] ──> [Backtest Histórico]
```

### Formatos Válidos de Decisão (Outputs):
- Trade individual (ex.: ordens de compra/venda de um ativo)
- Ranking de ativos (classificação de melhores e piores)
- Alocação de portfólio (definição de pesos entre múltiplos ativos)
- Rebalanceamento periódico de carteira

---

## 3. Perguntas Frequentes (FAQ)

### Conceito do Modelo Quantitativo

#### O que é, na prática, um modelo quantitativo?
É um processo sistemático e reprodutível de tomada de decisão baseado em dados. Substitui a análise subjetiva por um conjunto objetivo de regras ou algoritmos. Se outra pessoa usar os mesmos dados e a mesma metodologia, deverá chegar exatamente aos mesmos resultados.

#### O modelo precisa de regras simples e explícitas?
Não necessariamente. 
- **Regras Diretas:** Médias móveis, estratégia fatorial, reversão à média ou múltiplos fundamentalistas (mais fáceis de interpretar).
- **Machine Learning / IA:** Algoritmos preditivos, árvores de decisão, classificadores ou redes neurais (onde não há regras simples do tipo "se X, compre Y", mas um algoritmo treinado).
*Ambos são aceitos, desde que tenham inputs/outputs claros, lógica sistemática e sejam replicáveis.*

#### O modelo quantitativo precisa usar IA na sua estrutura interna?
**Não.** O uso de IA/Machine Learning no núcleo do modelo é opcional. Estratégias fatoriais, médias móveis, filtros estatísticos ou heurísticas quantitativas sem Machine Learning são totalmente válidos.

---

### Uso Obrigatório de IA Generativa (GenAI)

#### O que é obrigatório quanto à Inteligência Artificial?
- **Machine Learning no modelo quantitativo:** *Opcional*
- **Uso de IA Generativa (GenAI) no projeto:** *Obrigatório*

#### O que conta como uso válido de GenAI?
- Utilização de LLMs (ChatGPT, Copilot, etc.) para organização de ideias ou estruturação de hipóteses.
- Apoio no desenvolvimento, tradução ou revisão de código.
- Auxílio na escrita e melhoria do relatório técnico.
- Interpretação de notícias, textos financeiros, sentimento ou dados não estruturados.
- Explicação de resultados, limitações e riscos.

#### A GenAI precisa estar integrada ao modelo?
Não. Ela pode ser usada em etapas complementares (ideação, código, revisão, gráficos, branding do robô). A integração direta (ex.: análise de sentimento de notícias) é permitida, mas não obrigatória.

---

### Execução Técnica, Dados e Backtest

#### O que o modelo deve entregar de output?
Uma saída clara e testável: sinais de compra/venda, pesos de carteira, rankings ou rebalanceamentos periódicos.

#### O que é um backtest?
É a simulação histórica da estratégia sobre dados passados. Responde à pergunta: *"Se esse modelo tivesse sido usado no passado, qual teria sido o resultado?"*

#### O período do backtest é fixo?
Não. A janela temporal é livre e deve ser justificada pela equipe (considerando disponibilidade de dados, ciclos de mercado, crises, etc.).

#### É obrigatório dividir em treino/teste (out-of-sample)?
Não é obrigatório. Métodos como validação fora da amostra ou *walk-forward* são bem-vindos, mas não exigidos.

#### Quais dados podem ser utilizados?
Preços, volumes, indicadores técnicos, múltiplos fundamentalistas, dados macroeconômicos, manchetes de notícias ou dados alternativos. Podem ser de fontes gratuitas ou pagas. Os dados **não serão fornecidos** pela organização.

#### O backtest pode ser feito por plataformas prontas?
**Não.** O backtest deve ser implementado pela equipe (via código Python, planilhas no Excel, etc.). Não é permitido delegar o teste a ferramentas automáticas de terceiros do tipo "black box".

#### Quais ferramentas/linguagens podem ser usadas?
Python, Excel, R, MATLAB, planilhas ou outras ferramentas. Não é necessário programar tudo do zero (é permitido usar bibliotecas prontas como `pandas`, `backtrader`, `scikit-learn`, etc.).

#### Qual classe de ativos escolher?
Livre escolha: Ações, Índices, Moedas, Taxa de Juros, Commodities, Criptomoedas, Derivativos ou carteiras multiativos.

---

### Avaliação e Desempenho

#### Uma estratégia simples perde pontos para uma complexa?
Não. O desafio valoriza a clareza do raciocínio, o rigor metodológico e a qualidade da execução. Modelos simples e bem executados pontuam melhor do que modelos complexos e mal fundamentados.

#### Um resultado/desempenho ruim no backtest elimina a equipe?
**Não.** Encontrar estratégias que não funcionam faz parte da pesquisa quantitativa. A avaliação foca na honestidade analítica, seriedade metodológica e capacidade de interpretação dos resultados.

#### É necessário considerar custos de transação/slippage?
Não é obrigatório, mas incluir custos de transação ou impacto de mercado adiciona realismo à análise.

#### É necessário utilizar um benchmark?
Sim, é altamente recomendável (ex.: Ibovespa, S&P 500, CDI, SOFR ou um benchmark customizado coerente com a estratégia).

---

## 4. Checklist para Início Rápido

Se a equipe está travada ou sem saber como começar, siga este roteiro:

1. **Comece simples:** Escolha uma ideia viável e um conjunto pequeno de ativos.
2. **Defina a lógica:** Mapeie os dados de entrada, o processamento e a decisão gerada.
3. **Colete os dados:** Obtenha sementes de dados históricas (gratuitas ou públicas).
4. **Rode a primeira versão do backtest:** Implemente um script ou planilha simples e observe o comportamento.
5. **Aplique GenAI:** Utilize IA generativa para auxiliar na codificação, insights ou análise.
6. **Itere e refine:** Melhore o modelo gradualmente com base em diagnósticos honestos do teste.
