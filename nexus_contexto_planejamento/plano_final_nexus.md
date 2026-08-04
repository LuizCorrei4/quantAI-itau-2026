# Plano Final — Robô Nexus
## Grafo de Correlação Dinâmica e Centralidade de Rede para Seleção de Portfólio
### Desafio Quant AI Itaú Asset 2026

> **Status:** Versão 1.3 — Esqueleto de execução revisado (04/ago/2026). Este documento é o guia-mestre do projeto até a entrega final (16/ago/2026, 23h59). Pode ser adaptado conforme a equipe avance.

### Changelog (Versão 1.3)
- **Data/Versão:** Atualização do cabeçalho corrigindo data de revisão para antes do deadline.
- **Dados:** Correção de tickers (SOUZ3 -> CRUZ3) e clarificação entre deslistagem real e ticker renomeado (ex: VVAR3).
- **Filtro de Regime:** Esclarecido que o percentil é escolhido no in-sample (testando alternativas) e fixado no out-of-sample, exigindo transparência no relatório.
- **Matriz de Correlação:** Detalhada a implementação do Ledoit-Wolf (covariância → shrinkage → correlação), alvo do shrinkage e o risco de compressão do sinal.

### Changelog (Versão 1.2)
- **Dados:** Validação empírica revelou falha do `yfinance` para ativos deslistados. Plano ajustado para focar em universo baseado em liquidez (sobreviventes).
- **Cronograma:** Reestruturado para incluir um "MVP Mínimo" funcional e iniciar o relatório em paralelo, mitigando riscos de atraso.
- **Filtro de Regime:** Regra de definição do threshold alterada (uso de percentil histórico móvel) para evitar overfitting.
- **Matriz de Correlação:** Inclusão de estimador Ledoit-Wolf (shrinkage) como mitigador da fragilidade estatística amostral.
- **Análise Crítica:** Expandida para incluir expressamente os riscos de survivorship bias e overfitting no regime.

---

## Parte 0: Glossário para a Equipe (Conceitos de Finanças para Data Scientists)

Antes de entrar na estratégia, vamos nivelar os conceitos financeiros que aparecem ao longo deste plano. Vocês são cientistas de dados — pensem nos paralelos com ML/estatística.

### O que é "diversificação é a única free lunch"?

Em economia, o termo **"free lunch"** (almoço grátis) vem de uma ideia famosa: **não existe ganho sem risco**. Se alguém te oferece um retorno alto sem risco, provavelmente é golpe ou engano. Essa ideia é formalizada como a *Hipótese de Mercado Eficiente*.

A **única exceção reconhecida** a essa regra é a **diversificação**. O economista Harry Markowitz (Prêmio Nobel de 1990) demonstrou matematicamente que, ao combinar ativos que não se movem perfeitamente juntos (correlação < 1), é possível **reduzir o risco total da carteira sem reduzir o retorno esperado**. Isso é literalmente "algo de graça" — você ganha (redução de risco) sem pagar nada (sem perder retorno).

**Analogia para Data Science:** É como um ensemble de modelos (Random Forest). Cada árvore individual é ruidosa, mas ao combinar muitas árvores *diferentes entre si* (descorrelacionadas), o ensemble tem menos variância sem perder acurácia. A diversificação financeira é o ensemble de investimentos.

**O problema:** A diversificação só funciona de verdade se os ativos forem genuinamente descorrelacionados. Em crises, quase tudo cai junto (correlações sobem para perto de 1), e a "diversificação" desaparece exatamente quando você mais precisa dela. **É exatamente esse problema que o Nexus tenta resolver** — encontrar ações que se mantêm descorrelacionadas mesmo em momentos difíceis.

### O que é "exposição idiossincrática"?

O retorno de uma ação pode ser decomposto em duas partes:

1. **Risco Sistêmico (de mercado):** A parte do movimento da ação que é causada pelo mercado como um todo. Quando o Ibovespa sobe 2%, quase todas as ações sobem um pouco — essa é a parte sistêmica. Você **não consegue eliminar** esse risco via diversificação.

2. **Risco Idiossincrático (específico):** A parte do movimento que é exclusiva daquela empresa. Exemplo: a Petrobras cai 5% num dia porque descobriram um problema na gestão, enquanto o Ibovespa ficou estável. Esses -5% são quase inteiramente idiossincrático.

**Exposição idiossincrática** significa que a carteira é dominada por fatores específicos de cada empresa, não pelo "sobe e desce" geral do mercado. Isso é poderoso porque:
- Se uma ação cai por um motivo próprio dela, as outras não caem junto.
- A carteira fica menos vulnerável a crises sistêmicas (como um cenário de alta de juros que derruba tudo).


### O que é "Sharpe Ratio superior ao índice"?

O **Sharpe Ratio** é a métrica mais usada em finanças para medir "retorno ajustado ao risco". A fórmula é simples:

```
Sharpe = (Retorno da carteira − Retorno do CDI) / Volatilidade da carteira
```

- **Numerador:** Quanto a carteira rendeu *acima* da taxa livre de risco (CDI no Brasil). Se a carteira rendeu 15% e o CDI foi 10%, o excesso de retorno é 5%.
- **Denominador:** O desvio padrão dos retornos (volatilidade). Quanto mais a carteira oscila, maior o denominador.

**Um Sharpe alto = a carteira entregou bastante retorno para cada unidade de risco assumida.**

"Sharpe superior ao índice em horizontes médios" significa que a carteira do Nexus, em períodos de 6 meses a 2 anos, tende a ter uma relação retorno/risco melhor que simplesmente comprar o Ibovespa. Isso porque as ações periféricas oferecem diversificação real, reduzindo a volatilidade sem sacrificar retorno.

### Outros termos que aparecerão

| Termo | O que é | Analogia em Data Science |
|---|---|---|
| **Backtest** | Simular a estratégia no passado com dados históricos | Avaliar o modelo em dados de teste (holdout) |
| **Look-ahead bias** | Usar acidentalmente dados do futuro ao tomar decisão no passado | Data leakage no treino/teste |
| **Survivorship bias** | Testar apenas com ações que existem hoje, ignorando as que faliram | Selecionar features que só funcionam nos dados limpos |
| **Drawdown** | Maior queda acumulada do pico ao vale da carteira | Pior caso de perda consecutiva |
| **Benchmark** | Referência de comparação (Ibovespa, CDI) | Baseline model (regressão linear, dummy classifier) |
| **Alfa** | Retorno acima do benchmark | Melhoria de métrica vs. baseline |
| **Turnover** | % da carteira que muda em cada rebalanceamento | Taxa de atualização do modelo em produção |
| **CDI** | Taxa básica de juros brasileira (≈ Selic); retorno "sem risco" | Null model / retorno de não fazer nada |

---

## Parte 1: A Tese — O Que Estamos Apostando e Por Quê

### 1.1 Hipótese Central

> **"A estrutura de correlação entre ações muda ao longo do tempo. Ações que ocupam posições periféricas na rede de correlação oferecem diversificação genuína e, portanto, uma carteira composta por essas ações tende a ter melhor retorno ajustado ao risco do que o índice de mercado."**

### 1.2 Sustentação Acadêmica

Esta tese não é uma invenção nossa — ela se apoia em **três pilares acadêmicos bem documentados:**

#### Pilar 1: Correlações não são estáveis (e sobem em crises)

O paper seminal é **"Increased Correlation in Bear Markets"** (Longin & Solnik, 2001, *Journal of Finance*). Os autores demonstraram estatisticamente que as correlações entre mercados acionários **aumentam significativamente em períodos de queda**, usando 30 anos de dados. Em linguagem simples: quando o mercado cai, quase todas as ações caem juntas — a "diversificação" some.

Outros estudos fundamentais:
- **Forbes & Rigobon (2002):** Mostraram que parte do aumento de correlação em crises é real (não apenas artefato estatístico), usando uma correção matemática chamada "teste de contágio".
- **Ang & Chen (2002):** Documentaram que correlações são assimétricas — sobem mais em mercados de baixa do que caem em mercados de alta.

**O que isso significa para o Nexus:** Se sabemos que as correlações mudam, precisamos de uma ferramenta que mapeie essa mudança *dinamicamente*. A Minimum Spanning Tree (MST) faz exatamente isso — ela reconstrói o "mapa" de conexões do mercado a cada mês.

#### Pilar 2: Redes de correlação em mercados financeiros

O uso de Teoria de Grafos em finanças foi iniciado por **Rosario Mantegna** no paper **"Hierarchical Structure in Financial Markets"** (1999, *European Physical Journal B*). Mantegna propôs usar a Minimum Spanning Tree para filtrar a matriz de correlação e revelar a estrutura hierárquica do mercado — quais setores se agrupam, quais ações são "centrais" e quais são "periféricas".

Trabalhos subsequentes consolidaram essa abordagem:
- **Onnela et al. (2003):** Mostraram que a MST se contrai (fica mais densa e centralizada) em crashes e se expande em mercados calmos — confirmando que a topologia da rede muda com o regime de mercado.
- **Bonanno et al. (2004):** Aplicaram métricas de centralidade para identificar ações sistematicamente importantes.
- **Tumminello et al. (2005):** Introduziram o *Planar Maximally Filtered Graph (PMFG)* como alternativa à MST, mantendo mais informação.

**O que isso significa para o Nexus:** Estamos usando uma metodologia com 25+ anos de validação acadêmica. A banca do Itaú Asset reconhece essa linhagem — o vencedor de 2024 (Persistence) usou TDA, que é uma evolução da mesma família matemática.

#### Pilar 3: Ações periféricas oferecem diversificação real

A conexão entre centralidade de rede e risco de portfólio foi explorada em:
- **Peralta & Zareei (2016):** Demonstraram que portfólios formados por ações com baixa centralidade na rede de correlação apresentam menor risco sistêmico e melhor Sharpe em horizontes de médio prazo. A lógica é que ações periféricas são dominadas por fatores idiossincráticos (específicos da empresa ou do microsetor), que se cancelam numa carteira diversificada.
- **Pozzi et al. (2013):** Usando dados da NYSE, mostraram que a posição de uma ação na MST é preditiva da sua contribuição para o risco sistêmico do portfólio.

**O que isso significa para o Nexus:** Não estamos "chutando" que periferia = alfa. Existe evidência empírica de que selecionar ações de baixa centralidade gera carteiras com Sharpe superior, porque essas ações capturam retorno idiossincrático que não é diluído por exposição excessiva ao fator de mercado.

### 1.3 Por Que Esta Tese É Competitiva Para o Desafio

| Critério de Avaliação | Como o Nexus atende |
|---|---|
| **Conceito (20%)** | Hipótese clara e testável, com sustentação acadêmica de 3 pilares. Não é "feijão com arroz" (média móvel, RSI). |
| **Originalidade** | Combina Teoria de Grafos + Finanças, na mesma família do vencedor de 2024 (TDA). |
| **Modelagem (20%)** | Processo 100% sistemático e reprodutível: dados → correlação → MST → centralidade → ranking → alocação. |
| **Visual para o relatório** | Grafos/redes são extremamente visuais — perfeitos para um PDF de 5 páginas. |

---

## Parte 2: O Modelo Quantitativo — Passo a Passo

### 2.1 Visão Geral do Pipeline

```
[Preços Diários] → [Retornos Log] → [Matriz de Correlação] → [Matriz de Distância]
       ↓
[Minimum Spanning Tree (MST)] → [Cálculo de Centralidade] → [Ranking de Ações]
       ↓
[Seleção das Top N Periféricas] → [Alocação Equal-Weight]
       ↓
[Filtro de Regime] → [Ajuste de Exposição: Ações ↔ CDI] → [Backtest]
```

### 2.2 Etapa 1: Dados de Entrada

**O que coletamos:**
- Preços de fechamento ajustados (por dividendos e desdobramentos) de todas as ações que compuseram o Ibovespa ao longo do período de análise.
- Período sugerido: **Janeiro de 2012 a Dezembro de 2025** (13 anos, cobrindo múltiplos ciclos: Dilma, Temer, COVID, Bolsonaro, Lula).

**Validação Empírica de Disponibilidade de Dados (Agosto/2026):**
Testamos empiricamente a obtenção da composição histórica do IBOV e de preços diários de uma amostra de ações via `yfinance`, cobrindo tanto deslistagens reais (ex: `CRUZ3.SA` da Souza Cruz) quanto tickers renomeados/fundidos (ex: `VVAR3.SA`, que virou `VIIA3.SA`, e `BTOW3.SA`).
- **O que falhou:** O `yfinance` não retorna dados para tickers extintos no formato antigo. É crucial notar a diferença: "deslistagem real" (a empresa sumiu da bolsa, como Souza Cruz) gera um buraco de dados sem solução em APIs gratuitas. Já "ticker renomeado" (como Via Varejo, que continua ativa sob outro nome) poderia ser recuperado se tivermos uma tabela de mapeamento de tickers. No momento, sem essa tabela e sem uma base premium (como Economatica), o acesso direto falha.
- **O Novo Universo ("Sobreviventes por Liquidez"):** Assumindo temporariamente que não faremos o mapeamento (decisão pendente de checagem), nosso universo de análise será composto **apenas pelas empresas que existem hoje e "sobreviveram" na bolsa**. Dessas empresas que estão ativas hoje no `yfinance`, nós vamos puxar o histórico de preços até 2012. A cada mês do backtest, nosso algoritmo filtrará as **80 ações que tiveram o maior volume financeiro negociado no passado recente**, restringindo a alocação apenas a elas.
- **O que isso significa de forma simples?** Em vez da regra exigir que "o robô só pode comprar ações que estão na lista oficial do Ibovespa", nossa nova regra dirá: "dentre as empresas que existem hoje, o robô só pode comprar as 80 ações mais líquidas e negociadas daquele período". Essa é uma técnica amplamente aceita porque o próprio Ibovespa é, por definição, um índice focado nas ações de maior liquidez e volume.
- **O Custo dessa Decisão (Survivorship Bias / Viés de Sobrevivência):** Essa manobra nos salva de ficar travados sem dados, mas cobra um preço estatístico. Ao olhar apenas para as ações que estão "vivas" em 2026, nós "apagamos da história" as empresas que deram errado e faliram na última década. Isso naturalmente faz o retorno final do backtest parecer um pouco melhor do que a realidade (já que não sofremos as perdas de ações que viraram pó). Como a banca sabe muito bem que dados premium custam caro, a melhor saída é assumir essa limitação e **declarar esse viés com total transparência no relatório final**. Isso demonstra maturidade analítica e não mascara o projeto.

**Fontes Definitivas:**
| Dado | Fonte | Biblioteca Python |
|---|---|---|
| Preços ajustados e Volume (ações sobreviventes) | Yahoo Finance | `yfinance` |
| CDI diário acumulado | Banco Central do Brasil (SGS) | `python-bcb` ou requests direto |

### 2.3 Etapa 2: Cálculo da Matriz de Correlação Rolante

Para cada mês `t` do backtest, o rebalanceamento da carteira ocorre sempre no primeiro dia útil. Para tomar essa decisão, olhamos para o passado recente da seguinte forma:

1. Selecionar as ações que compunham o Ibovespa naquele período.
2. Calcular os **retornos logarítmicos diários** de cada ação: $$r_i(d) = ln(P_i(d) / P_i(d-1))$$
   - **$r_i(d)$**: É o retorno diário da ação $i$ no dia $d$. Usamos o retorno logarítmico em vez do percentual simples porque os log-retornos são aditivos ao longo do tempo e costumam ter propriedades estatísticas melhores (mais próximos de uma distribuição normal), o que é ideal para o cálculo da correlação.
   - **$ln$**: É a função de logaritmo natural.
   - **$P_i(d)$ e $P_i(d-1)$**: Preço de fechamento ajustado da ação $i$ no dia atual $d$ e no dia anterior $d-1$.
3. Usar uma **janela rolante de 63 dias úteis** (≈ 3 meses) *anteriores* ao mês `t` para calcular a **matriz de correlação de Pearson** entre todas as ações.
   - **O que significa isso na prática?** Em vez de calcular apenas uma variação de 3 meses de ponta a ponta, nós calculamos e **armazenamos o retorno diário $r_i(d)$ de todos os últimos 63 dias úteis, um após o outro**, para cada ação. Assim, cada ação passa a ser representada por uma série temporal contendo 63 valores de retorno.
   - **Como a janela "rola"?** Pense nisso como uma "janela de tempo móvel". No dia 1º de abril, reunimos as 63 séries de retornos diários referentes a janeiro, fevereiro e março. Com base nessas séries, calculamos como as ações se correlacionaram nesse período e tomamos a decisão de alocação. No mês seguinte, em 1º de maio, a janela "rola" para frente: descartamos os dados de janeiro e coletamos os dados de abril (passando a usar a série de fevereiro, março e abril). O cálculo é feito pontualmente apenas uma vez por mês.
   - **A ponte para a distância:** A partir dessas séries de 63 retornos diários, medimos a correlação de Pearson entre cada par de ações (ação A vs ação B, ação A vs ação C, etc.). Essa correlação nos diz se as ações caminharam juntas ou separadas dia a dia nesses 3 meses, valor que será transformado em uma medida de "distância" na próxima etapa.

**Por que 63 dias?** É um trade-off entre:
- Janela curta (21 dias): captura dinâmicas recentes mas é extremamente ruidosa (poucos dados para estimar correlação).
- Janela longa (252 dias): é robusta estatisticamente mas lenta para reagir a mudanças de regime.
- 63 dias (3 meses) é o padrão da literatura (Onnela et al., 2003).

**A Fragilidade Estatística da Matriz de Correlação (Shrinkage):**
Estimar uma matriz de correlação de 80 ações exige estimar cerca de 3.160 parâmetros (pares). Usar apenas 63 dias úteis para isso cria uma matriz mal condicionada. **Atenção:** A MST ajuda a mitigar o ruído da rede porque ela *descarta* as arestas fracas, mas ela **não** corrige o erro de estimação dos pesos nas arestas que sobrevivem na árvore.
Para mitigar isso com rigor estatístico, utilizaremos o **Estimador de Shrinkage de Ledoit-Wolf** (`sklearn.covariance.LedoitWolf`). É vital entender a implementação: o shrinkage atua na **matriz de covariância**, não na de correlação. O pipeline exato é: (1) estimar a covariância *shrinkada* dos retornos usando o alvo padrão do sklearn (a matriz identidade escalonada pela variância média); (2) normalizar essa covariância em uma matriz de correlação (dividindo pelas variâncias); e (3) só então aplicar a transformação geométrica de distância de Mantegna. 
**Ressalva importante para o MVP:** O shrinkage reduz o erro, mas seu efeito colateral é comprimir a diferença entre correlações fortes e fracas (ele "achata" o sinal). Como a MST precisa dessa diferença para separar quem é central de quem é periférico, precisamos monitorar no MVP se a técnica não achatou demais a rede, comparando a dispersão das centralidades com e sem o shrinkage, e relatar isso.

**Teste de robustez:** Rodaremos o backtest também com janelas de 42 e 126 dias para verificar se os resultados são sensíveis a essa escolha.

### 2.4 Etapa 3: Transformação em Distância e Construção da MST

**Da correlação para distância:**

Como visto na Etapa 2, para cada mês extraímos uma série temporal de 63 retornos diários para cada ação. A **correlação de Pearson ($ρ_{ij}$)** compara estatisticamente a série temporal da ação $i$ com a série temporal da ação $j$. A fórmula nos revela se os retornos dessas duas ações tendem a subir e descer juntos, dia após dia, no mesmo ritmo:
- Se a ação $i$ e a ação $j$ sobem e descem consistentemente juntas, a correlação $ρ_{ij}$ será próxima de +1.
- Se uma sobe exatamente quando a outra desce sistematicamente, $ρ_{ij}$ será próxima de -1.
- Se os movimentos diários não tiverem relação aparente (ruído), $ρ_{ij}$ será próxima de 0.

Para construirmos um grafo matemático (a rede), nós não precisamos de um índice de "correlação", mas sim de uma métrica física de **distância** geométrica entre os pontos (ações). Ou seja, se duas ações são muito correlacionadas, sua distância deve ser curta; se são anti-correlacionadas, a distância deve ser longa. Para converter o coeficiente $ρ_{ij}$ nessa distância rigorosa, usamos a transformação formulada por Mantegna (1999):

$$d_{ij} = \sqrt{2 \times (1 - ρ_{ij})}$$

| Correlação (ρ) | Distância (d) | Interpretação |
|---|---|---|
| +1.0 | 0.00 | Perfeitamente juntas |
| +0.5 | 1.00 | Correlacionadas |
| 0.0 | 1.41 | Independentes |
| -0.5 | 1.73 | Anti-correlacionadas |
| -1.0 | 2.00 | Perfeitamente opostas |

**Construção da MST (Minimum Spanning Tree):**

Primeiro, imagine um **Grafo Completo**: É uma rede onde *todas as ações estão conectadas a absolutamente todas as outras*. Se temos 80 ações no Ibovespa, cada uma das 80 está ligada às outras 79, formando 3.160 pares. A "distância" (peso) entre cada par dita a força da sua correlação. O problema do grafo completo é que ele é um emaranhado de fios onde quase tudo é ruído, dificultando ver qual é a verdadeira "espinha dorsal" do mercado.

A **Minimum Spanning Tree (Árvore Geradora Mínima)** é um conceito clássico de Teoria de Grafos para resolver esse excesso de fios. Dado esse grafo completo de ações, a MST é uma sub-árvore (um subconjunto de caminhos) que:
- Conecta **todos** os nós (as 80 ações não perdem conexão com a rede principal).
- Usa exatamente **N-1** arestas (se temos 80 ações, ela usará apenas 79 conexões, descartando as outras 3.081 ligações mais fracas).
- **Minimiza a soma total das distâncias:** O algoritmo escolhe iterativamente apenas as pontes mais "curtas" (ou seja, as conexões mais fortes de correlação) entre as ações, cuidando para não formar "ciclos" (caminhos fechados que dão voltas inúteis). O resultado é uma árvore com as distâncias mínimas conectando todo mundo.
  - **E as ações isoladas com pontes longas?** Uma dúvida comum é se uma ação muito independente, que não tem correlação forte com quase ninguém (ou seja, só possui "pontes longas" de distância com as demais), seria excluída da rede. A resposta é **não**. A regra de ouro da MST é que **nenhum nó pode ficar de fora**. Portanto, para essa ação isolada, o algoritmo será forçado a ligá-la à árvore utilizando a sua ponte *menos longa* (a sua maior correlação possível, mesmo que seja fraca). Ela continuará na rede, mas conectada por um único fio comprido. É **exatamente isso** que faz dela uma ação periférica! Cortar as suas outras 78 pontes (que são ainda mais longas e caóticas) não significa perder informação relevante; pelo contrário, elimina correlações espúrias (ruído) e deixa evidente que a ação está na ponta de um "galho" isolado do mercado.

**Por que usar a MST em vez do grafo completo?** A MST filtra a rede e mantém apenas as conexões de primeira ordem mais cruciais. É como desenhar apenas as rodovias principais de um país, ignorando as estradinhas de terra. Se a matriz de correlação tem muito ruído estatístico nos pares fracos, a MST joga isso fora e revela a estrutura de dependência real do mercado.
**Analogia para Data Science:** A MST é como uma técnica drástica de *feature selection* ou *regularização* (como um Lasso muito forte) — em vez de usar todas as 3.160 interações possíveis, você mantém apenas o esqueleto principal e mais informativo de 79 interações.

**Implementação:** Algoritmo de Kruskal ou Prim via biblioteca `networkx` em Python.

### 2.5 Etapa 4: Cálculo de Centralidade

Com a rede simplificada (MST) construída, calculamos a **Betweenness Centrality** (Centralidade de Intermediação) de cada nó (ação) para descobrir quem está no meio da teia e quem está nas pontas.

$$BC(v) = Σ_{s≠v≠t} [σ_{st}(v) / σ_{st}]$$

**O que isso significa na prática?**
- **$σ_{st}$**: É o número total de "caminhos mais curtos" que ligam um nó qualquer $s$ a outro nó $t$ na rede.
- **$σ_{st}(v)$**: É o número desses caminhos entre $s$ e $t$ que passam obrigatoriamente por cima do nó $v$ (a nossa ação em análise).
- **O somatório ($Σ$)**: Basicamente, soma essa proporção para todos os pares possíveis da rede.

**Interpretando:** Uma ação tem **alta Betweenness Centrality** se ela funciona como uma "ponte principal". Ela está no caminho mais curto entre vários outros grupos de ações. Se essa ação "hub" se move (por fatores macroeconômicos, por exemplo), a rede inteira sente o puxão. Ela segue o mercado fortemente (comporta-se de maneira sistêmica). Já uma ação com **baixa centralidade (periférica)** está "na ponta de um galho" da árvore. Ninguém precisa passar por ela. Portanto, seu comportamento é independente (seu risco idiossincrático é alto). Se ela cair 10% por uma má gestão particular, o resto da árvore não sente.

**Outras métricas (Alternativas a explorar se houver tempo):**
- **Degree Centrality (Centralidade de Grau):** É simplesmente contar *quantas conexões diretas* um nó tem. Se o Itaú se conecta a 10 outras ações na MST, o grau dele é 10. É fácil e intuitiva de calcular, mostrando a influência direta imediata, mas não capta a "posição no mapa global" como a Betweenness.
- **Closeness Centrality (Centralidade de Proximidade):** Calcula a distância média que uma ação precisa percorrer para chegar a todas as outras. Uma ação no centro do mapa chega a todos rapidamente (alta Closeness).

**Por que explorar essas duas?** A Betweenness Centrality pode ser cara computacionalmente, dependendo da máquina e do grafo, enquanto Degree e Closeness capturam o conceito de "periferia" com menor custo de cálculo e muitas vezes trazem seleções de ações bastante parecidas, permitindo refinar o modelo.

### 2.6 Etapa 5: Seleção e Alocação

**Regra de seleção:**
1. Ordenar todas as ações vigentes do Ibovespa pela Betweenness Centrality (da menor para a maior).
2. Selecionar as **Top 10 ações mais periféricas** (menor centralidade).
   - *Nota sobre o Universo Ibovespa:* Operar o universo do Ibovespa (~80 ações) é bastante valioso porque essas são as ações de maior liquidez e com dados mais limpos e acessíveis no Brasil. Procurar alfa fora do Ibovespa envolve lidar com small caps sem liquidez que geram um spread de compra/venda gigantesco e irrealismo no backtest. Selecionar apenas 10 das 80 (isolar os 12% mais periféricos) garante um filtro estatístico fortíssimo no mercado com alta liquidez garantida.

**Regra de alocação:**
- **Equal-weight (pesos iguais):** 10% em cada ação selecionada.
- **Por que essa realocação do Top 10 gera Alfa? (A Vantagem do Investidor):**
  A princípio, parece simples, mas uma carteira de 10 ações periféricas é o suprassumo da **diversificação real**. Em momentos difíceis, as 70 ações sistêmicas do miolo da rede começam a cair em bloco, levadas pelo pânico irracional ou pelo macro (forte correlação). O nosso investidor, estando posicionado de propósito apenas na ponta da rede, sofre menos esse choque coletivo. Quando essas ações sobem por motivos individuais (fatores idiossincráticos fortes de uma boa empresa que ninguém notou macro-economicamente), ele captura os ganhos sem estar diluído em uma cesta de mercado gigantesca. Rebalancear mensalmente garante que o portfólio "fuja" daquelas ações que de repente ganham atenção, se tornam mainstream e sistêmicas (indo pro centro da árvore) e passe a comprar novas ações que se distanciam do ruído comum daquele mês.

**A estratégia é frágil?**
Ela não é frágil estruturalmente, mas sofre em dois cenários pontuais:
1. **Crash absoluto de liquidez:** Quando todos vendem tudo sem olhar os fundamentos (ex. março 2020) até as ações periféricas sofrem pelo contágio total, pois toda a rede se contrai tanto que o conceito de periferia perde força temporariamente.
2. **Custos operacionais elevados:** Se as 10 ações periféricas mudarem completamente todo mês, as taxas de corretagem reduzem a rentabilidade real (problema do alto *turnover*). Por isso, no backtest, nós consideraremos os custos explícitos da B3 para mensurar isso de forma honesta.

**Rebalanceamento na prática:**
- **Mensal**, no primeiro dia útil de cada mês.
- Recalcular a MST com os dados mais recentes (últimos 63 dias).
- Substituir ações: vender o que saiu do Top 10 periférico e usar o dinheiro para comprar o que entrou, readequando o peso de todos para 10% cada.

### 2.7 Etapa 6: Filtro de Regime (Mecanismo de Defesa)

A MST não nos dá apenas as posições relativas das ações; ela também nos dá uma visão valiosa sobre o *estado geral* (regime) do mercado:

- **Mercado Calmo:** A MST é "espalhada" — muitos ramos, poucas ações centrais e distâncias médias grandes (correlações baixas).
- **Mercado em Crise:** A MST se "contrai" — pouquíssimas ações dominam o centro, os ramos encolhem e as distâncias despencam (tudo fica altamente correlacionado).

**Por que este passo é essencial?** Como discutimos na Etapa 5, a maior fraqueza dessa estratégia é um *crash absoluto de liquidez* (quando o mercado inteiro entra em pânico, as correlações globais vão para 1 e a diversificação periférica perde temporariamente seu poder protetor). Para contornar e mitigar esse cenário, precisamos de uma estratégia ativa de defesa.

**A Métrica de Regime e a Escolha do Threshold (Evitando Overfitting):**
Monitoraremos a "distância média normalizada" da MST mês a mês.
- **Risco de Overfitting:** Se simularmos todo o backtest e depois escolhermos o threshold ao final para todo o período, o modelo será inválido e sobre-otimizado.
- **Regra de Definição (Calibração In-Sample e Aplicação Out-of-Sample):** A regra é "backward-looking" (só olha para distâncias até `t-1`). Mas **o valor exato do percentil** (ex: 5%, 10% ou 15% histórico) não virá do nada: ele será **calibrado (testado)** no nosso período *In-Sample* (2013-2019). O percentil que melhor proteger a carteira nesses anos será então fixado e aplicado cegamente no período *Out-of-Sample* (2020-2025).
- **Transparência Absoluta:** Temos que reconhecer que calibrar o percentil no In-Sample ainda é uma forma branda de overfitting. Para demonstrar maturidade analítica, relataremos **todas** as alternativas testadas (5%, 10%, 15%) e seus resultados no In-Sample, justificando a escolha final e mostrando se ela sobreviveu no Out-of-Sample.
- **Defesa Ativa:** Se a métrica de distância da MST cair abruptamente abaixo desse limiar crítico (sinalizando um pânico sistêmico iminente), acionaremos o mecanismo de defesa.
- **Redução de Exposição:** O algoritmo cortará o nível de exposição na renda variável (por exemplo, reduzindo a alocação do Top 10 para 50% ou até 20%) e **alocará o restante do dinheiro com segurança no CDI** (caixa livre de risco).
- **Retomada:** Quando a distância média voltar a subir e ultrapassar o threshold de segurança (sinalizando calmaria e retorno da dispersão), restauraremos a exposição nas 10 ações periféricas para 100%.

---

## Parte 3: O Backtest — Como Vamos Testar

### 3.1 Estrutura do Backtest

```
Para cada mês t de Mar/2013 a Dez/2025:
  1. Pegar a composição do IBOV vigente em t
  2. Calcular retornos logarítmicos diários dos últimos 63 dias úteis
  3. Calcular matriz de correlação → distância → MST → centralidades
  4. Selecionar Top 10 ações periféricas
  5. Avaliar Filtro de Regime: verificar distância média da MST vs. threshold
     5a. Se acima do threshold → alocar 10% em cada ação (100% exposto)
     5b. Se abaixo do threshold → reduzir exposição e alocar restante em CDI
  6. Registrar retorno da carteira no mês t+1
  7. Repetir
```

**Nota:** Os dados começam em Jan/2012 (Etapa 1), mas os primeiros 63 dias úteis são consumidos para calcular a primeira janela de correlação. O backtest efetivo começa a partir de Mar/2013.

### 3.2 Benchmarks de Comparação

| Benchmark | Por quê |
|---|---|
| **Ibovespa (IBOV)** | Benchmark principal — é o "mercado" que queremos bater |
| **Carteira Equal-Weight do IBOV** | Para isolar o efeito da *seleção* (Nexus) vs. o efeito de *peso igual* |
| **CDI acumulado** | Para verificar se a estratégia justifica o risco vs. não fazer nada |

### 3.3 Métricas a Calcular

| Métrica | O que mede | Fórmula simplificada |
|---|---|---|
| **Retorno Acumulado** | Quanto a carteira rendeu no período total | Produto dos (1 + retorno mensal) |
| **Retorno Anualizado** | Retorno médio por ano | (1 + Retorno Total)^(1/anos) - 1 |
| **Volatilidade Anualizada** | Oscilação média por ano | Desvio padrão dos retornos mensais × √12 |
| **Sharpe Ratio** | Retorno por unidade de risco | (Retorno - CDI) / Volatilidade |
| **Máximo Drawdown** | Pior queda pico-a-vale | Maior queda acumulada consecutiva |
| **Information Ratio** | Excesso de retorno vs. benchmark / tracking error | (Retorno - IBOV) / Volatilidade(Retorno - IBOV) |
| **Turnover Mensal** | % da carteira que muda por mês | Nº de ações substituídas / 10 |
| **Calmar Ratio** | Retorno anualizado / Max Drawdown | Melhor = mais retorno por unidade de pior perda |

### 3.4 Tratamento de Vieses

| Viés | Como mitigamos | Nível de risco |
|---|---|---|
| **Look-ahead bias** | MST e centralidades calculadas com janela *trailing* de 63 dias. Posição tomada no 1º dia útil do mês seguinte. | ✅ Controlado |
| **Survivorship bias** | Universo focado em sobreviventes. Será mitigado pelo filtro dinâmico de volume e **declarado expressamente no relatório final**. | 🚨 Aceito como limitação |
| **Sobre-otimização** | Testar com 3 janelas (42, 63, 126 dias) e 3 tamanhos de carteira (5, 10, 15 ações). | ✅ Controlado |
| **Custos de transação** | Aplicar 0.05% de custo por operação (compra + venda). | ✅ Controlado |
| **Transaction timing** | Usar preço de fechamento do D+1 (primeiro dia útil), não do dia do cálculo. | ✅ Controlado |

### 3.5 Testes de Robustez (Análise de Sensibilidade)

| Parâmetro | Variações a testar | Objetivo |
|---|---|---|
| Janela de correlação | 42, 63, 126 dias úteis | Verificar se o resultado depende de uma janela específica |
| Nº de ações selecionadas | Top 5, Top 10, Top 15 periféricas | Verificar se o efeito de periferia persiste |
| Tipo de centralidade | Betweenness, Degree, Closeness | Verificar se a métrica de centralidade importa |
| Threshold do Filtro de Regime | Múltiplos limiares de contração da MST | Verificar qual nível de defesa maximiza o Sharpe sem perder retorno em mercados calmos |
| Sub-períodos | 2013-2017 vs. 2018-2022 vs. 2023-2025 | Verificar estabilidade temporal |

---

## Parte 4: Análise de Resultados — O Que Vamos Mostrar

### 4.1 Visualizações Planejadas para o Relatório

1. **Gráfico de linhas: Retorno acumulado** — Nexus vs. IBOV vs. CDI (gráfico principal, será a estrela do relatório).
2. **Grafo MST visualizado** — Duas imagens lado a lado: uma MST em período calmo (espalhada) e uma em crise (contraída). Destaque visual nas ações periféricas selecionadas.
3. **Tabela de métricas comparativas** — Sharpe, Drawdown, Retorno de Nexus vs. benchmarks.
4. **Gráfico de sensibilidade** — Como o Sharpe muda conforme variamos janela e nº de ações (mostra robustez).
5. **Timeline de regime** — Barra horizontal mostrando períodos de contração/expansão da rede sobrepostos a eventos de mercado (COVID, eleições, etc.).

### 4.2 Análise Crítica (O Que Pode Dar Errado)

A banca valoriza honestidade analítica. Devemos abordar:

- **Cenários favoráveis:** Mercados laterais ou setoriais (onde a dispersão entre ações é alta e a seleção de periféricas captura alfa).
- **Survivorship Bias (Viés de Sobrevivência):** Pela falha prática em recuperar dados de empresas deslistadas (validado no início do projeto), nosso universo reflete empresas que sobreviveram até 2026. Isso infla o retorno da carteira (já que não selecionamos empresas que faliram), mas a tese central (retorno *relativo* via descorrelação periférica) deve se sustentar independentemente disso.
- **Risco de Overfitting no Filtro de Regime:** Qualquer mecanismo que corta e volta à exposição do mercado corre sério risco de ter sido "calibrado pelo olhar" dos autores. É vital defender a separação do período *Out-of-Sample* para provar que o filtro não foi viciado com dados do futuro.
- **Cenários desfavoráveis:** Crashes sistêmicos e quedas repentinas de liquidez (ex: março de 2020), onde até a defesa do percentil histórico pode reagir atrasada e o conceito de periferia rui.
- **Limitações e Tamanho Amostral:** 63 dias para estimar a relação de 80 ações é estatisticamente frágil. Embora utilizemos *shrinkage* de Ledoit-Wolf e a MST para refinar as conexões, a árvore final sempre abrigará um grau de erro de estimação amostral.

---

## Parte 5: Uso de IA Generativa — Como Documentar (15% da nota)

### 5.1 Estratégia de Documentação

O uso de IA não precisa estar numa página separada — pode (e deve) estar integrado ao longo do relatório. Mas precisa ser **específico e concreto**.

### 5.2 Onde Usamos IA (Mapa Planejado)

| Etapa do Projeto | Como a IA Foi Usada | Ferramenta |
|---|---|---|
| **Ideação** | IA revisou a literatura acadêmica (Mantegna, Onnela, Peralta) e ajudou a formular a hipótese de investimento. | Gemini / Claude |
| **Código do backtest** | IA gerou e revisou o código Python para construção da MST (`networkx`), cálculo de centralidade e loop de backtest (`pandas`). | Gemini (Agy) / Claude Code |
| **Visualização** | IA criou código para visualizar a MST de forma interativa com `matplotlib` / `plotly`, gerando figuras para o relatório. | Gemini / Claude |
| **Revisão crítica** | IA questionou escolhas metodológicas (por que Pearson e não Spearman? Por que 63 dias?), forçando a equipe a justificar cada decisão. | Gemini / Claude |
| **Identidade do robô** | IA gerou a imagem do robô Nexus com base no conceito de grafos e nós periféricos. | Gemini (geração de imagem) |
| **Estruturação do relatório** | IA ajudou a organizar as 5 páginas de forma visual e concisa, priorizando gráficos sobre texto. | Gemini / Claude |

### 5.3 O Que Mostrar no Relatório

- **1-2 exemplos concretos** de prompt → output útil (ex: "pedimos à IA para gerar o código da MST e ela sugeriu usar algoritmo de Kruskal via `networkx`").
- **Menção de limitação da IA:** "A IA sugeriu usar correlação de Kendall, mas após análise, optamos por Pearson por ser computacionalmente mais viável para N=60 ações × 63 dias".
- **Impacto quantificável se possível:** "O uso de IA reduziu o tempo de implementação do backtest de ~3 semanas para ~5 dias".

---

## Parte 6: O Relatório Final — Esqueleto das 5 Páginas

### Restrições Absolutas
- **Máximo 5 páginas** (incluindo capa, se houver). 6+ páginas = eliminação.
- **Formato:** PDF, 16:9 (widescreen/horizontal).
- **Anonimato total:** Nenhum nome de pessoa, equipe ou universidade.
- **Menos de 750 palavras** no total (priorizar visual).

### Estrutura Sugerida

| Página | Conteúdo | Peso na Nota |
|---|---|---|
| **1** | **Identidade do Nexus + Conceito da Estratégia.** Logo do robô, nome, explicação do nome. Hipótese central em 2-3 frases. Diagrama do pipeline (Dados → MST → Centralidade → Seleção). | Robô (5%) + Conceito (20%) |
| **2** | **Modelagem.** Explicação visual da MST e centralidade. Exemplo visual: "esta ação é central, esta é periférica". Regras de alocação em formato de tabela/fluxograma. | Modelagem (20%) |
| **3** | **Backtest e Resultados.** Gráfico de retorno acumulado (Nexus vs. IBOV vs. CDI). Tabela de métricas (Sharpe, Drawdown, etc.). Duas MSTs comparadas (calma vs. crise). | Backtest (15%) + Análise (15%) |
| **4** | **Análise Crítica + Uso de IA.** Cenários de falha. Sensibilidade dos parâmetros. Timeline de uso da IA ao longo do projeto (com exemplos concretos). | Análise (15%) + IA (15%) |
| **5** | **Conclusão e Próximos Passos.** Limitações reconhecidas. Propostas de evolução (ex: usar Mutual Information, testar em outros mercados, explorar PMFG como alternativa à MST). | Conclusão (10%) |

---

## Parte 7: Cronograma de Execução até 16/08/2026 (23h59)

| Período | Entrega | Responsável |
|---|---|---|
| **04-05/ago** | **Dados Base:** Obter preços (sobreviventes) e volume via `yfinance`, mais o CDI. Lidar com NAs e calcular retornos. | Equipe |
| **06-08/ago** | **Fase 1: MVP Mínimo Funcional.** Pipeline ponta a ponta (Correlação Pearson → MST → Centralidade Top 10 → Backtest Equal-Weight simples). Objetivo: garantir que a estratégia base roda sem erros antes de sofisticações. | Equipe + IA |
| **09-11/ago** | **Fase 2: Refinamentos e Robustez.** Substituir Pearson por Ledoit-Wolf (Shrinkage). Implementar o Filtro de Regime dinâmico (percentil móvel). | Equipe + IA |
| **11-13/ago** | **Rascunho do Relatório e Visuais.** *(Começa em paralelo ao final do backtest)*. Gerar MSTs comparativas, imagens do robô, redigir textos curtos. | Equipe + IA |
| **14-15/ago** | **Revisão Fina.** Enxugamento de texto (< 750 palavras), garantir estética premium de 16:9, checagem do anonimato. | Equipe |
| **16/ago (manhã)**| **Buffer de Emergência.** | Equipe |
| **16/ago 23h59**| **🚨 Deadline absoluto — Entrega final.** | — |

---

## Parte 8: Identidade do Robô Nexus (5% da nota)

### Nome
**Nexus** — do latim *nexus*, significando "conexão" ou "vínculo". Escolhido porque o robô literalmente constrói e analisa a **rede de conexões** entre ações do mercado.

### Conceito Visual
- Nós (pontos) e arestas (linhas) de um grafo.
- Os nós periféricos (ações selecionadas) brilham/iluminam com destaque.
- Os nós centrais são mais opacos/sombreados.
- Cores sugeridas: fundo escuro (azul-marinho ou preto), nós periféricos em dourado/verde-neon, arestas em cinza translúcido.

### Racional (para o relatório)
"Nexus mapeia a rede invisível de conexões entre ações e investe onde os vínculos são mais fracos — porque é na periferia que está a diversificação genuína."

---

## Parte 9: Riscos e Plano de Contingência

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Dados de composição histórica do IBOV difíceis de obter | Média | Alto | Usar dataset alternativo (todas as ações com volume > X, não apenas IBOV formal) |
| Backtest mostra Sharpe igual ou pior que IBOV | Média | Alto | Analisar honestamente por quê. Lembrar: a banca valoriza honestidade analítica. Um resultado negativo bem explicado é melhor que um resultado positivo fabricado. |
| MST instável (muda radicalmente mês a mês) | Baixa | Médio | Testar janelas mais longas (126 dias). Mostrar estabilidade temporal no relatório. |
| Tempo insuficiente para polir o relatório | Média | Alto | Priorizar: (1) backtest funcional com filtro de regime, (2) gráfico de retorno, (3) visual do relatório. Simplificar o filtro de regime (usar apenas 1 threshold) se necessário, mas não removê-lo. |
| yfinance falha para tickers antigos da B3 | Alta | Médio | Ter fallback: usar `investpy`, Economatica free trial, ou datasets prontos do Kaggle/GitHub. |
