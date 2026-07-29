# Alternativas de Estratégias Quantitativas — Desafio Quant AI 2026

Este documento apresenta 5 ideias de estratégias quantitativas desenvolvidas para competir no Desafio Itaú Asset Quant AI 2026. Cada alternativa está estruturada para contemplar todos os critérios de avaliação (Conceito 20%, Modelagem 20%, Backtest 15%, Análise 15%, IA Generativa 15%, Conclusão 10%, Robô 5%) e incorpora as lições dos vencedores anteriores: multidisciplinaridade, originalidade conceitual, rigor metodológico e uso significativo de IA.

---

## Alternativa 1: Entropia Informacional como Preditor de Regime de Mercado

### Nome do Robô sugerido: *Entropos*

### 1.1 Tese Inicial (Hipótese de Investimento)

**Fenômeno a capturar:** Os mercados financeiros alternam entre regimes de baixa e alta incerteza. A distribuição dos retornos de um ativo não é estável — em momentos de transição de regime (de calma para crise, ou de crise para recuperação), a *entropia* da distribuição de retornos muda significativamente *antes* de os preços refletirem a mudança.

**Justificativa econômica:** A entropia de Shannon, aplicada à distribuição empírica de retornos intradiários, mede o grau de "desordem" ou "imprevisibilidade" do mercado. Quando a entropia sobe abruptamente, significa que os retornos estão se espalhando de forma mais uniforme (nenhuma direção domina) — sinal de que o mercado está perdendo sua tendência e entrando em incerteza. Quando a entropia cai, o mercado está se concentrando em um regime mais previsível (tendência definida).

**Por que é original:** Diferente de indicadores de volatilidade tradicionais (como desvio padrão ou VIX), a entropia captura a *forma* da distribuição, não apenas sua dispersão. Dois mercados com a mesma volatilidade podem ter entropias completamente diferentes — um com retornos concentrados em duas caudas (bimodal, crise) e outro com retornos normalmente distribuídos (regime calmo).

### 1.2 Modelo Quantitativo

**Dados de Entrada:**
- Retornos intradiários (5 minutos) do Ibovespa ou de um ETF (BOVA11) — últimos 8-10 anos.
- Alternativamente: retornos diários para simplificação (janela rolante de 21 dias úteis).

**Processamento:**
1. Para cada dia `t`, calcular a distribuição empírica dos retornos na janela rolante dos últimos `N` dias (ex: N=21).
2. Discretizar os retornos em `k` bins (ex: 20 bins equidistantes).
3. Calcular a Entropia de Shannon: `H(t) = -Σ p_i * log2(p_i)` para os bins com frequência > 0.
4. Calcular a variação da entropia: `ΔH(t) = H(t) - H(t-1)`.
5. Normalizar `H(t)` via z-score sobre janela de 252 dias úteis (1 ano) para obter um sinal comparável entre períodos.

**Classificação de Regime:**
- `Z_H > 1.5`: Regime de Alta Entropia → Mercado está em transição/desordem.
- `Z_H < -1.0`: Regime de Baixa Entropia → Mercado em tendência definida.
- `-1.0 ≤ Z_H ≤ 1.5`: Regime Neutro.

### 1.3 Sinais Gerados e Decisões

| Regime | Sinal | Alocação |
|---|---|---|
| Alta Entropia (desordem crescente) | Defensivo | 100% Renda Fixa (CDI/Tesouro Selic) |
| Baixa Entropia + Retorno Recente > 0 | Tendência de Alta | 100% BOVA11 (Ibovespa) |
| Baixa Entropia + Retorno Recente < 0 | Tendência de Baixa | 100% CDI ou Short Index (se permitido) |
| Neutro | Neutro | 50% BOVA11 / 50% CDI |

**Rebalanceamento:** Diário, no fechamento. A alocação muda apenas quando o regime muda.

### 1.4 Métricas de Avaliação do Backtest

- **Retorno acumulado** vs. Buy & Hold do Ibovespa e vs. CDI acumulado.
- **Sharpe Ratio** anualizado.
- **Máximo Drawdown** e duração do drawdown.
- **Taxa de acerto nos regimes:** % de vezes que o regime "Alta Entropia" de fato precedeu uma queda significativa.
- **Calmar Ratio** (retorno / drawdown máximo).
- **Hit Ratio por transição de regime:** Análise qualitativa dos momentos de crise (2008, 2015, 2020, 2022).

### 1.5 Dados Necessários e Fontes

| Dado | Fonte | Acesso |
|---|---|---|
| Preços diários/intradiários BOVA11 | Yahoo Finance / B3 (via `yfinance`) | Gratuito |
| CDI diário acumulado | Banco Central (SGS) | Gratuito |
| Taxa Selic | Banco Central (SGS) | Gratuito |

### 1.6 Tratamento de Vieses no Backtest

- **Look-ahead bias:** A entropia é calculada exclusivamente com dados passados (janela rolante *trailing*). Nenhuma informação futura é utilizada.
- **Survivorship bias:** Não aplicável diretamente (opera índice, não ações individuais).
- **Sobre-otimização:** Testar robustez variando `N` (janela) de 15 a 42 dias e `k` (bins) de 10 a 30. Se o sinal só funciona para uma combinação específica, é overfitting.
- **Custos de transação:** Incluir 0.03% de slippage por operação e corretagem (se aplicável).

### 1.7 Uso de IA Generativa

- **Ideação:** IA usada para explorar a literatura de Teoria da Informação aplicada a finanças e formular a hipótese.
- **Código:** IA auxiliou na implementação da discretização e cálculo de entropia em Python/pandas.
- **Análise crítica:** IA usada para gerar cenários de stress e questionar a robustez dos parâmetros escolhidos.

### 1.8 Pontos Fortes e Fracos

| Pontos Fortes | Pontos Fracos |
|---|---|
| Conceito original (entropia ≠ volatilidade) | Pode gerar sinais atrasados em crashes súbitos (flash crash) |
| Fundamentação teórica sólida (Teoria da Informação) | Sensível à escolha do número de bins `k` |
| Simples de implementar e explicar | Opera apenas 1 ativo (Ibovespa) — pouca diversificação |
| Baixo turnover (muda só na transição de regime) | Regime "Neutro" pode ter alocação subótima |

### 1.9 Identidade do Robô

**Entropos** — do grego *entropía* (transformação, desordem). O robô "lê" a desordem do mercado para se posicionar antes da mudança de regime. Identidade visual sugerida: formas geométricas fragmentadas que se reorganizam conforme o regime muda (calmo → fragmentado → reorganizado).

---

## Alternativa 2: Grafo de Correlação Dinâmica e Centralidade de Rede para Seleção de Portfólio

### Nome do Robô sugerido: *Nexus*

### 2.1 Tese Inicial (Hipótese de Investimento)

**Fenômeno a capturar:** A estrutura de correlação entre ações de um mesmo mercado não é estável — ela se contrai (todas as ações passam a se mover juntas) em momentos de crise e se expande (dispersão de comportamento) em momentos de oportunidade. Ações que ocupam posições "centrais" na rede de correlação (ou seja, que são fortemente conectadas a muitas outras) tendem a replicar o comportamento sistêmico do mercado, enquanto ações "periféricas" oferecem retornos mais idiossincráticos e diversificação genuína.

**Justificativa econômica:** Em finanças, a diversificação é a única "free lunch". Porém, a diversificação real depende de como as correlações mudam ao longo do tempo. A teoria de redes complexas permite mapear dinamicamente quais ações estão verdadeiramente descorrelacionadas e quais apenas *parecem* descorrelacionadas em janelas específicas. Investir nas ações periféricas da rede de correlação gera um portfólio com exposição idiossincrática, que tende a ter Sharpe superior ao índice em horizontes médios.

**Por que é original:** Combina Teoria de Grafos (área de matemática discreta) com finanças quantitativas, na linha do vencedor de 2024 (TDA/Persistence) que usou ferramentas de topologia. Redes de correlação são uma evolução natural dessa tendência multidisciplinar.

### 2.2 Modelo Quantitativo

**Dados de Entrada:**
- Retornos diários de todas as ações do Ibovespa (componentes atuais + históricos para evitar survivorship bias).
- Janela: últimos 8-10 anos.

**Processamento:**
1. **Construção do Grafo de Correlação:** Para cada mês `t`, calcular a matriz de correlação de Pearson dos retornos diários dos últimos 63 dias úteis (3 meses rolantes). Transformar em distância: `d_ij = √(2(1 - ρ_ij))`.
2. **Filtragem da Rede:** Construir a *Minimum Spanning Tree (MST)* da matriz de distâncias — mantém apenas as `N-1` conexões mais fortes (onde N = número de ações), eliminando ruído.
3. **Cálculo de Centralidade:** Para cada ação no grafo MST, calcular a *Betweenness Centrality* (quantas vezes o nó aparece no caminho mais curto entre outros pares de nós).
4. **Classificação:**
   - Ações com alta centralidade → **Ações Sistêmicas** (comportam-se como o mercado).
   - Ações com baixa centralidade (periféricas) → **Ações Idiossincráticas** (diversificação real).

**Regras de Alocação:**
- Selecionar as 10 ações de menor centralidade (mais periféricas na MST).
- Alocar pesos iguais (equal-weight) entre elas.
- Rebalancear mensalmente (recalcular MST e centralidades).

### 2.3 Sinais Gerados e Decisões

| Componente | Decisão |
|---|---|
| Ranking mensal de centralidade | Selecionar Top 10 ações mais periféricas |
| Alocação | Equal-weight (10% cada) |
| Rebalanceamento | Mensal, primeiro dia útil |
| Filtro de regime (opcional) | Se a densidade média do grafo sobe acima de um threshold (crise sistêmica), reduzir exposição a 50% e colocar o restante em CDI |

### 2.4 Métricas de Avaliação do Backtest

- **Retorno acumulado** vs. Ibovespa (IBOV) e vs. carteira Equal-Weight do Ibovespa.
- **Sharpe Ratio** e **Information Ratio** (excesso de retorno / tracking error vs. benchmark).
- **Máximo Drawdown** e comparação com drawdown do Ibovespa nos mesmos períodos.
- **Turnover mensal:** Quantas ações mudam por mês (avaliar custos).
- **Análise de atribuição:** Quanto do alfa vem da seleção (ações periféricas) vs. quanto vem do filtro de regime.
- **Teste de robustez:** Variar janela de correlação (42, 63, 126 dias) e número de ações selecionadas (5, 10, 15).

### 2.5 Dados Necessários e Fontes

| Dado | Fonte | Acesso |
|---|---|---|
| Preços ajustados diários (IBOV constituents) | Yahoo Finance / `yfinance` / Economatica | Gratuito (yfinance) |
| Composição histórica do Ibovespa | B3 (carteiras teóricas quadrimestrais) | Gratuito (site da B3) |
| CDI diário | Banco Central (SGS) | Gratuito |

### 2.6 Tratamento de Vieses no Backtest

- **Survivorship bias:** Usar composição histórica do Ibovespa em cada período (não a atual). Incluir ações que saíram do índice.
- **Look-ahead bias:** A MST e centralidades são calculadas com dados estritamente passados (janela trailing de 63 dias).
- **Custos de transação:** Incluir 0.05% de custo por operação (taxa B3 + emolumentos + slippage estimado). Calcular impacto do turnover mensal.
- **Sobre-otimização:** Testar com variações de parâmetros e verificar se o alfa persiste.

### 2.7 Uso de IA Generativa

- **Pesquisa bibliográfica:** IA utilizada para revisar a literatura acadêmica sobre redes de correlação em mercados financeiros (Mantegna, Bonanno, Onnela).
- **Implementação:** IA auxiliou na construção da MST via `networkx` em Python e no cálculo de métricas de centralidade.
- **Visualização:** IA gerou código para visualizar o grafo MST de forma interativa, criando figuras impactantes para o relatório.
- **Revisão crítica:** IA questionou se a correlação de Pearson é a melhor medida (alternativas: correlação de Spearman, Mutual Information).

### 2.8 Pontos Fortes e Fracos

| Pontos Fortes | Pontos Fracos |
|---|---|
| Altamente multidisciplinar (Grafos + Finanças) — alinhado com perfil vencedor | Necessidade de dados de composição histórica do índice (evitar survivorship) |
| Conceito intuitivo e visual (grafos são ótimos para o relatório de 5 páginas) | Correlação de Pearson pode não capturar dependências não-lineares |
| Baixo turnover se a estrutura da rede for estável | MST pode ser sensível a outliers em janelas curtas |
| Filtro de regime (densidade do grafo) adiciona camada de proteção | Potencial falta de justificativa econômica sólida para "periferia = alfa" |

### 2.9 Identidade do Robô

**Nexus** — do latim "conexão". O robô mapeia a rede invisível de conexões do mercado e investe onde as conexões são mais fracas, buscando diversificação genuína. Identidade visual: nós e arestas de um grafo, com destaque nos nós periféricos iluminados.

---

## Alternativa 3: Momentum Cross-Asset via Paridade de Risco Adaptativa

### Nome do Robô sugerido: *Equitas*

### 3.1 Tese Inicial (Hipótese de Investimento)

**Fenômeno a capturar:** O efeito *momentum* (ativos que tiveram bom desempenho recente tendem a continuar performando bem no curto/médio prazo) é uma das anomalias de mercado mais documentadas academicamente. Porém, aplicá-lo a uma única classe de ativo é arriscado (reversões bruscas). A inovação desta tese é aplicar momentum *cross-asset* (entre classes de ativos diferentes — ações, câmbio, juros, commodities) combinado com uma alocação de **paridade de risco adaptativa** que ajusta pesos dinamicamente conforme a volatilidade de cada classe muda.

**Justificativa econômica:** O momentum existe porque investidores reagem de forma gradual a novas informações (underreaction) e porque fluxos institucionais demoram a se realocar completamente. A paridade de risco garante que nenhuma classe domine o risco total do portfólio, evitando concentração excessiva em ativos voláteis (como ações) e subalocação em ativos menos voláteis (como renda fixa), corrigindo um erro comum da alocação por capitalização.

**Por que é original:** Combina dois conceitos bem fundamentados (momentum + risk parity) de forma cruzada entre classes de ativos brasileiros, algo que raramente é testado na B3/mercado local. A maioria das equipes focará em equity-only; esta abordagem multi-asset se diferencia naturalmente.

### 3.2 Modelo Quantitativo

**Dados de Entrada:**
- 4 classes de ativos representadas por proxies líquidos:
  - **Ações Brasil:** BOVA11 (ETF Ibovespa)
  - **Renda Fixa Longa:** IMA-B 5+ (ou IMAB11)
  - **Câmbio:** USDBRL (dólar)
  - **Commodities:** GOLD11 ou Ouro BM&F (OZ1D)

**Processamento:**
1. **Cálculo de Momentum:** Para cada ativo `i`, calcular o retorno acumulado dos últimos `L` meses (ex: L=6 meses), excluindo o último mês (para evitar efeito de reversão de curto prazo, conforme Jegadeesh & Titman 1993).
   - `MOM_i = Retorno(t-L, t-1)`
2. **Sinal de Momentum:** Se `MOM_i > 0`, o ativo recebe sinal positivo (incluir no portfólio). Se `MOM_i < 0`, o ativo é excluído e sua alocação vai para CDI.
3. **Paridade de Risco:** Entre os ativos com sinal positivo, alocar pesos inversamente proporcionais à sua volatilidade realizada dos últimos 63 dias:
   - `w_i = (1/σ_i) / Σ(1/σ_j)` para todos `j` com momentum positivo.
4. **Rebalanceamento:** Mensal.

### 3.3 Sinais Gerados e Decisões

| Cenário | Alocação |
|---|---|
| Todos os 4 ativos com momentum positivo | Risk Parity entre os 4 (pesos proporcionais ao inverso da vol) |
| Apenas Ações e Ouro com momentum positivo | Risk Parity entre Ações e Ouro; restante em CDI |
| Nenhum ativo com momentum positivo | 100% CDI (modo defensivo total) |

### 3.4 Métricas de Avaliação do Backtest

- **Retorno acumulado** vs. CDI (principal benchmark para multi-asset).
- **Sharpe Ratio** anualizado.
- **Máximo Drawdown** — espera-se que seja significativamente menor que buy & hold de ações.
- **Calmar Ratio** (retorno anualizado / max drawdown).
- **Contribuição por classe:** Decomposição de retorno e risco por ativo — mostrar que a diversificação cross-asset realmente funcionou.
- **Análise em sub-períodos:** Período de alta de juros (2021-2023) vs. período de queda (2016-2019) vs. crise (2020).
- **Teste de robustez:** Variar `L` (janela de momentum) de 3 a 12 meses.

### 3.5 Dados Necessários e Fontes

| Dado | Fonte | Acesso |
|---|---|---|
| Preços diários BOVA11, IMAB11, USDBRL, GOLD11 | Yahoo Finance / `yfinance` | Gratuito |
| CDI diário | Banco Central (SGS, série 12) | Gratuito |
| Dados de Ouro BM&F (OZ1D) | B3 / Investing.com | Gratuito |

### 3.6 Tratamento de Vieses no Backtest

- **Look-ahead bias:** O momentum usa retorno de `t-L` a `t-1`, nunca incluindo o mês corrente. A volatilidade é estritamente trailing.
- **Survivorship bias:** Não aplicável (opera ETFs/índices, não ações individuais).
- **Custos de transação:** Incluir 0.10% de custo total por rebalanceamento (corretagem ETFs + slippage). Como o rebalanceamento é mensal, o impacto é limitado.
- **Sobre-otimização:** Testar com múltiplas janelas de momentum (3, 6, 9, 12 meses) e verificar persistência do resultado. Incluir período *out-of-sample* (ex: treinar em 2012-2020, testar em 2021-2025).

### 3.7 Uso de IA Generativa

- **Ideação:** IA utilizada para revisar a literatura acadêmica de time-series momentum (Moskowitz, Ooi, Pedersen 2012) e identificar como adaptá-la ao mercado brasileiro.
- **Código:** IA gerou o pipeline de cálculo de momentum e risk parity, incluindo função de rebalanceamento mensal.
- **Visualização:** IA criou gráficos de alocação dinâmica ao longo do tempo (stacked area chart) para o relatório.
- **Análise adversarial:** IA foi usada para testar cenários de falha (whipsaw em mercados sem tendência clara).

### 3.8 Pontos Fortes e Fracos

| Pontos Fortes | Pontos Fracos |
|---|---|
| Fundamentação acadêmica robusta (momentum é anomalia bem documentada) | Momentum pode falhar em mercados laterais prolongados (whipsaw) |
| Multi-asset = diferencial natural vs. equipes equity-only | Janela de momentum de 6 meses pode ser lenta para reagir a crises abruptas |
| Risk parity evita concentração de risco | Operação de ETFs pode ter liquidez limitada (IMAB11, GOLD11) |
| Fácil de explicar e visualizar em 5 páginas | Conceito não é "de fronteira" como TDA/fractais — precisa de excelente execução |

### 3.9 Identidade do Robô

**Equitas** — do latim "equidade/equilíbrio". O robô distribui risco de forma justa entre classes de ativos, surfando tendências onde elas existem e se protegendo onde não existem. Identidade visual: uma balança estilizada com os 4 ativos equilibrados dinamicamente.

---

## Alternativa 4: Análise de Sentimento de Atas do COPOM via LLM para Posicionamento em Juros

### Nome do Robô sugerido: *Copérnico*

### 4.1 Tese Inicial (Hipótese de Investimento)

**Fenômeno a capturar:** As atas do Comitê de Política Monetária (COPOM) contêm sinais antecipados sobre a direção da taxa Selic. O mercado precifica expectativas de juros com base em leituras humanas dessas atas, que são subjetivas e ruidosas. Um modelo que processa sistematicamente o texto das atas via Large Language Model (LLM) para extrair um *score* de hawkishness/dovishness pode capturar nuances que a leitura humana média ignora, gerando um sinal de posicionamento em renda fixa.

**Justificativa econômica:** A curva de juros brasileira é extremamente sensível à comunicação do Banco Central. Estudos mostram que mudanças no tom das atas (mais hawkish = apertando, mais dovish = afrouxando) precedem movimentos na curva DI futura. Um modelo que quantifica essa mudança de tom de forma reprodutível e sistemática captura um prêmio de informação.

**Por que é original:** Integra diretamente a IA Generativa (LLM) *dentro* do modelo quantitativo, não apenas como ferramenta auxiliar. Isso demonstra um uso avançado e prático da IA no núcleo da estratégia — algo que a banca valoriza fortemente (15% da nota) e que se alinha com a menção dos vencedores ao uso de NLP. Além disso, o *Ringle* (dados alternativos do Spotify) mostrou que dados não-convencionais chamam a atenção da banca.

### 4.2 Modelo Quantitativo

**Dados de Entrada:**
- Textos completos das atas do COPOM (disponíveis no site do BCB — ~160 atas desde 2000, 8 por ano).
- Preços diários de contratos de DI futuro (DI1F) de diferentes vencimentos, ou do ETF IRFM11/IMA-B.

**Processamento:**
1. **Extração e Pré-processamento:** Download automatizado das atas do COPOM em PDF/HTML. Limpeza e segmentação em parágrafos relevantes (perspectivas econômicas, riscos, balanço de riscos).
2. **Scoring via LLM (IA Generativa):**
   - Para cada ata, enviar os parágrafos-chave a um LLM (Gemini/Claude/GPT) com um prompt estruturado:
     - *"Com base exclusivamente neste trecho da ata do COPOM, classifique o tom da comunicação em uma escala de -5 (extremamente dovish/afrouxamento) a +5 (extremamente hawkish/aperto). Justifique brevemente."*
   - Agregar os scores dos parágrafos em um score final da ata: `S_t ∈ [-5, +5]`.
3. **Sinal de Variação de Tom:**
   - `ΔS_t = S_t - S_{t-1}` (mudança de tom entre duas atas consecutivas).
   - Normalizar via z-score histórico.
4. **Validação cruzada do scoring:** Comparar o score do LLM com a decisão efetiva da Selic na reunião seguinte para calibrar a confiabilidade.

### 4.3 Sinais Gerados e Decisões

| Condição | Sinal | Posição |
|---|---|---|
| `ΔS_t < -1.0` (tom ficou significativamente mais dovish) | Compra de Renda Fixa Longa | 100% IMA-B 5+ (aposta na queda de juros / ganho de marcação a mercado) |
| `ΔS_t > +1.0` (tom ficou significativamente mais hawkish) | Venda / Defensivo | 100% Tesouro Selic (LFT) / CDI (proteção contra alta de juros) |
| `-1.0 ≤ ΔS_t ≤ +1.0` (tom estável) | Neutro | 50% IMA-B / 50% CDI |

**Frequência:** A cada reunião do COPOM (~8x/ano, a cada 45 dias). Baixíssimo turnover.

### 4.4 Métricas de Avaliação do Backtest

- **Retorno acumulado** vs. CDI e vs. IMA-B 5+ passivo (buy & hold).
- **Sharpe Ratio.**
- **Máximo Drawdown** — especialmente importante para renda fixa longa (que teve drawdowns de 15%+ em 2021-2022).
- **Acurácia direcional do LLM:** % de vezes que o score corretamente antecipou a direção da Selic.
- **Matriz de confusão:** Score Dovish e Selic efetivamente caiu? Score Hawkish e Selic subiu?
- **Análise de cenário:** Performance durante ciclo de alta Selic (2021-2023) vs. ciclo de queda (2016-2020, 2023-2024).

### 4.5 Dados Necessários e Fontes

| Dado | Fonte | Acesso |
|---|---|---|
| Atas do COPOM (texto integral) | BCB (bcb.gov.br/publicacoes/atascopom) | Gratuito |
| Decisão da Selic (histórico) | BCB (SGS, série 432) | Gratuito |
| IMA-B 5+ diário | Anbima / Tesouro Direto | Gratuito |
| CDI diário | BCB (SGS, série 12) | Gratuito |
| DI Futuro | B3 (Market Data) | Gratuito (séries históricas) |

### 4.6 Tratamento de Vieses no Backtest

- **Look-ahead bias:** O score de cada ata é gerado usando apenas o texto da ata publicada (que é divulgada *após* a decisão). A posição é tomada no dia útil seguinte à publicação da ata, nunca antes.
- **LLM data contamination:** O LLM pode ter sido treinado com dados que incluem as decisões da Selic posteriores. Para mitigar: (a) usar apenas o trecho da ata sem mencionar a decisão; (b) comparar scores de dois LLMs diferentes para verificar consistência; (c) usar prompt que instrui o modelo a ignorar conhecimento externo.
- **Sobre-otimização:** O threshold de `ΔS` (±1.0) deve ser testado com variações (0.5, 1.0, 1.5). Incluir período out-of-sample.
- **Baixa frequência de sinais:** Com apenas ~8 reuniões/ano, a amostra de sinais é pequena. Importante reconhecer isso como limitação.

### 4.7 Uso de IA Generativa

**Este é o projeto com o uso mais profundo e central de IA Generativa entre todas as alternativas.**

- **Núcleo do modelo:** O LLM É o motor de scoring. Sem ele, o modelo não existe. Isso demonstra uso prático e não-superficial.
- **Engenharia de prompt:** Documentar a evolução dos prompts (de genéricos a especializados) mostra sofisticação no uso da IA.
- **Validação:** Comparar outputs de Gemini vs. Claude vs. GPT para a mesma ata demonstra maturidade no uso da ferramenta.
- **Código:** IA auxiliou na extração e parsing das atas (PDF → texto estruturado).

### 4.8 Pontos Fortes e Fracos

| Pontos Fortes | Pontos Fracos |
|---|---|
| Uso de IA Generativa no *núcleo* da estratégia (maximiza os 15%) | Amostra de sinais muito pequena (~8/ano) → baixa significância estatística |
| Tema altamente relevante para gestora brasileira (juros = maior mercado BR) | LLM pode ter data contamination sobre decisões da Selic |
| Baixíssimo turnover (rebalanceamento a cada 45 dias) | Dependência de API de LLM para reprodutibilidade do backtest |
| Dados 100% públicos e gratuitos | Dificuldade de provar que o LLM agrega vs. uma leitura humana simples |
| Fácil de contar a "história" de forma visual | Tema pode ser comum entre equipes (risco de não-originalidade) |

### 4.9 Identidade do Robô

**Copérnico** — referência a Nicolau Copérnico, que mudou a forma como interpretamos o que observamos. Assim como Copérnico reinterpretou os dados celestes, o robô reinterpreta as palavras do Banco Central para antecipar movimentos de mercado. Identidade visual: um olho/lente analisando texto, com ondas de sinal emanando.

---

## Alternativa 5: Detecção de Anomalias em Fluxos de Capital Estrangeiro para Timing de Mercado

### Nome do Robô sugerido: *Maré*

### 5.1 Tese Inicial (Hipótese de Investimento)

**Fenômeno a capturar:** O mercado brasileiro de ações é fortemente influenciado pelo fluxo de capital estrangeiro. Historicamente, entradas líquidas de capital estrangeiro na B3 precedem altas significativas do Ibovespa, e saídas líquidas precedem quedas. No entanto, nem todo fluxo é informativo — o sinal está nas *anomalias* de fluxo (desvios extremos da tendência recente), não no fluxo absoluto.

**Justificativa econômica:** Investidores estrangeiros representam ~50% do volume negociado na B3. Quando esse grupo move capital de forma anormal (muito acima ou abaixo da média), frequentemente reflete repositionamentos estratégicos baseados em informações ou análises macro que ainda não foram absorvidas pelo mercado local. Detectar essas anomalias de fluxo cria uma vantagem informacional temporária.

**Por que é original:** Usa dados *alternativos* (fluxo de capital estrangeiro — dado público mas pouco modelado de forma quantitativa), na linha do vencedor *Ringle* (Spotify como dado alternativo). Combina detecção de anomalias estatísticas (Isolation Forest ou Z-score adaptativo) com uma tese macroeconômica clara sobre o papel do investidor estrangeiro no Brasil.

### 5.2 Modelo Quantitativo

**Dados de Entrada:**
- **Fluxo líquido diário de estrangeiros na B3** (compras - vendas em R$). Dados publicados pela B3 com 1 dia de defasagem.
- **Preços diários do Ibovespa** (BOVA11 ou índice).
- **Câmbio USDBRL** (fator de controle — fluxo estrangeiro em dólar vs. real).

**Processamento:**
1. **Normalização do Fluxo:** Converter o fluxo diário em z-score rolante de 42 dias úteis (2 meses):
   - `Z_flow(t) = (Flow(t) - μ_42) / σ_42`
2. **Detecção de Anomalia (Método 1 — Estatístico):** Anomalia se `|Z_flow| > 2.0`.
3. **Detecção de Anomalia (Método 2 — Machine Learning, opcional):** Treinar um modelo *Isolation Forest* sobre os dados de fluxo diário, volume e câmbio para detectar anomalias multivariadas (fluxo anormalmente alto + câmbio se movendo na direção oposta = sinal mais forte).
4. **Cálculo de Fluxo Acumulado:** Somar o fluxo líquido estrangeiro dos últimos 5 dias úteis (1 semana) para suavizar ruído diário.
5. **Sinal Combinado:** Anomalia de entrada (Z > 2) = sinal de compra. Anomalia de saída (Z < -2) = sinal de venda.

### 5.3 Sinais Gerados e Decisões

| Condição de Fluxo | Sinal | Posição |
|---|---|---|
| `Z_flow > 2.0` (entrada anômala de estrangeiros) | Compra | 100% BOVA11 |
| `Z_flow < -2.0` (saída anômala de estrangeiros) | Venda / Defensivo | 100% CDI |
| `-2.0 ≤ Z_flow ≤ 2.0` (fluxo normal) | Neutro | Manter posição anterior (inércia) |

**Holding period:** Manter a posição por no mínimo 10 dias úteis (2 semanas) após o sinal, a não ser que um sinal contrário ocorra.

### 5.4 Métricas de Avaliação do Backtest

- **Retorno acumulado** vs. Buy & Hold Ibovespa e CDI.
- **Sharpe Ratio** anualizado.
- **Máximo Drawdown.**
- **Precisão dos sinais de anomalia:** Dos sinais de "entrada anômala", quantos % foram seguidos por alta do Ibovespa nos 10-20 dias seguintes?
- **Análise de eventos:** Mapear os sinais de anomalia sobre crises conhecidas (2014-2015 político, 2018 greve dos caminhoneiros, 2020 COVID, 2022 eleições, 2024 fiscal).
- **Falso positivos:** Quantos sinais de anomalia não resultaram em movimento direcional significativo?

### 5.5 Dados Necessários e Fontes

| Dado | Fonte | Acesso |
|---|---|---|
| Fluxo diário de estrangeiros (B3) | B3 (Investidores Não-Residentes — dados de participação) | Gratuito (site B3, boletim diário) |
| Preços diários BOVA11 / Ibovespa | Yahoo Finance / `yfinance` | Gratuito |
| USDBRL diário | BCB (SGS) / Yahoo Finance | Gratuito |
| CDI diário | BCB (SGS, série 12) | Gratuito |

### 5.6 Tratamento de Vieses no Backtest

- **Look-ahead bias:** Os dados de fluxo da B3 são publicados com 1 dia de defasagem (D+1). O sinal é gerado em D+1 e a posição é tomada no fechamento de D+2, garantindo que nenhum dado futuro é utilizado.
- **Survivorship bias:** Não aplicável (opera índice).
- **Data snooping:** O z-score de anomalia (threshold ±2.0) é derivado de princípios estatísticos (2 desvios padrão), não otimizado sobre os dados. Testar com ±1.5 e ±2.5 para verificar robustez.
- **Custos de transação:** Incluir 0.05% por operação. Turnover esperado é baixo (poucos sinais de anomalia por ano).

### 5.7 Uso de IA Generativa

- **Pesquisa e ideação:** IA utilizada para explorar a relação entre fluxo estrangeiro e retornos do Ibovespa na literatura acadêmica.
- **Extração de dados:** IA auxiliou na automação do scraping dos dados de fluxo do site da B3 (que são publicados em formato complexo).
- **Detecção de anomalias:** IA ajudou a implementar e comparar métodos (Z-score vs. Isolation Forest), gerando código Python otimizado.
- **Análise narrativa:** IA usada para cruzar automaticamente datas de anomalias detectadas com eventos macroeconômicos (usando web search), enriquecendo a análise qualitativa no relatório.

### 5.8 Pontos Fortes e Fracos

| Pontos Fortes | Pontos Fracos |
|---|---|
| Dado alternativo público mas pouco explorado quantitativamente | Fluxo pode ser ruidoso no curto prazo (muitas falsas anomalias) |
| Tese macroeconômica clara e intuitiva (investidor estrangeiro move o mercado) | Não captura motivações do fluxo (pode ser hedge, não aposta direcional) |
| Dados 100% gratuitos e acessíveis | Relação fluxo-retorno pode ter enfraquecido com o crescimento do mercado local |
| Poucos sinais = baixo turnover = baixo custo | Poucos sinais = amostra estatística pequena para validação |
| Método 2 (Isolation Forest) adiciona ML sem depender dele | Pode ser difícil distinguir do efeito momentum simples |
| Visual forte para relatório (timeline de eventos + fluxos) | Defasagem de D+1 pode perder parte do movimento |

### 5.9 Identidade do Robô

**Maré** — o fluxo de capital estrangeiro entra e sai da B3 como uma maré. O robô detecta quando a maré está anormalmente alta ou baixa e se posiciona antes que o mercado absorva a informação. Identidade visual: ondas estilizadas com setas de fluxo (entrada/saída), utilizando cores que mudam conforme a direção do sinal.

---

## Quadro Comparativo das 5 Alternativas

| Critério | Entropos (Entropia) | Nexus (Grafos) | Equitas (Momentum/RP) | Copérnico (NLP/COPOM) | Maré (Fluxo Estrangeiro) |
|---|---|---|---|---|---|
| **Originalidade** | ★★★★☆ | ★★★★★ | ★★★☆☆ | ★★★★☆ | ★★★★☆ |
| **Fundamentação Acadêmica** | ★★★★☆ | ★★★★★ | ★★★★★ | ★★★☆☆ | ★★★☆☆ |
| **Facilidade de Implementação** | ★★★★☆ | ★★★☆☆ | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| **Uso de IA no Modelo** | ★★☆☆☆ | ★★☆☆☆ | ★★☆☆☆ | ★★★★★ | ★★★☆☆ |
| **Potencial Visual (5 páginas)** | ★★★☆☆ | ★★★★★ | ★★★★☆ | ★★★★☆ | ★★★★☆ |
| **Risco de Overfitting** | Médio | Médio | Baixo | Baixo | Baixo |
| **Classe de Ativo** | Ibovespa | Ações BR | Multi-asset | Juros/RF | Ibovespa |
| **Frequência de Rebalanceamento** | Diária | Mensal | Mensal | ~45 dias | Evento-driven |
| **Multidisciplinar** | Teoria da Informação | Teoria de Grafos | Finanças Clássicas | NLP + Finanças | Dados Alternativos |
| **Alinhamento c/ Vencedores** | Médio-Alto | Alto (TDA/Persistence) | Médio | Alto (NLP/GenAI) | Alto (Ringle/Alt Data) |

---

## Recomendação para Discussão

A decisão final deve considerar:

1. **Perfil da equipe:** Se a equipe tem mais afinidade com programação e dados, **Nexus** ou **Maré** são naturais. Se tem mais afinidade com finanças macro, **Copérnico** ou **Equitas**.
2. **Diferenciação:** **Nexus** e **Entropos** são os mais multidisciplinares, alinhados ao perfil vencedor do desafio.
3. **Uso de IA:** **Copérnico** maximiza a nota de IA Generativa (15%) ao usar o LLM como motor do modelo.
4. **Segurança de execução:** **Equitas** é a alternativa mais segura e bem fundamentada academicamente, mas pode ser a menos original.
5. **Combinação possível:** Elementos de diferentes alternativas podem ser combinados (ex: Momentum Cross-Asset + filtro de Entropia para regime).
