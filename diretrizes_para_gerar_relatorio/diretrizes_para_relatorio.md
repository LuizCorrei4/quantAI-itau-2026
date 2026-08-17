# Diretrizes Consolidadas para o Relatório Final
## Desafio Itaú Asset Quant AI 2026

> Fonte: Condensação dos 5 documentos oficiais — Edital, Regulamento, Manual de Avaliação, Diretrizes do Relatório Final e Guia de Primeiros Passos.

---

## 1. Regras Invioláveis (Eliminatórias)

| Regra | Consequência do descumprimento |
| :--- | :--- |
| **Máximo de 5 páginas** (capa e apêndice inclusos) | 6+ páginas = **eliminação** |
| **Formato:** PDF, 16:9 (widescreen), legível em tela cheia | Não conformidade = desclassificação |
| **Anonimato total:** proibido qualquer nome de membro, equipe ou universidade/instituição | Identificação = **eliminação** |
| **Nome do arquivo:** `[Chave de envio].pdf` | Chave fornecida após pré-relatório |
| **Prazo:** 17 de agosto de 2026 | Atraso = desclassificação |
| **Backtest feito pela equipe** (código próprio, não ferramentas black-box) | Uso de plataformas automáticas = penalização |

> **Atenção:** Não haverá apresentação oral nesta etapa. A avaliação é **100% baseada no PDF**. Avaliadores não acessam links externos, QR Codes ou código-fonte.

---

## 2. Critérios de Avaliação — Pesos e Detalhamento

### 2.1. Apresentação do Robô — 5%

**O que avaliam:**
- Nome do robô e coerência com a estratégia proposta
- Identidade visual (design)
- Clareza da identidade conceitual
- Explicação do nome escolhido

**O que valorizam:**
- Identidade clara, objetiva e alinhada à proposta técnica

**Pontos negativos:**
- Nome genérico ou sem relação com a estratégia
- Excesso de elementos visuais sem finalidade explicativa
- Baixa clareza na apresentação

---

### 2.2. Conceito da Estratégia — 20%

**O que avaliam:**
- Existência de uma **hipótese clara** de pesquisa
- Coerência da tese sob perspectiva quantitativa, econômica ou estatística
- Grau de originalidade e criatividade
- Consistência como estratégia de investimento

**A equipe deve articular explicitamente:**
1. O fenômeno que pretende capturar
2. A justificativa para sua existência
3. A forma como será testado

**Formato sugerido da hipótese:** *"Acredito que X acontece porque Y; portanto, vou testar Z."*

**O que valorizam:**
- Clareza conceitual e consistência lógica

**Pontos negativos:**
- Ausência de hipótese definida
- Propostas desconexas ou fragmentadas
- Complexidade sem fundamentação

---

### 2.3. Modelagem — 20%

**O que avaliam:**
- Definição clara dos **dados de entrada** (inputs)
- Descrição do **processamento** realizado pelo modelo
- Definição objetiva da **saída** do modelo (outputs)
- Caráter **sistemático e replicável** do processo

**Fluxo esperado:**
```
[Entrada de Dados] ──> [Processamento do Modelo] ──> [Geração da Decisão]
```

**Outputs válidos:**
- Sinais de compra/venda
- Rankings de ativos
- Alocações de portfólio (pesos)
- Regras de rebalanceamento

**Nota técnica:** O modelo quantitativo **não precisa** usar IA/ML internamente. Estratégias com médias móveis, fatores, reversão à média ou filtros estatísticos são plenamente válidas. O que importa é que a lógica seja **sistemática, clara e replicável**.

**O que valorizam:**
- Estrutura lógica clara e consistente

**Pontos negativos:**
- Falta de clareza na lógica de decisão
- Processos não replicáveis
- Uso de ferramentas externas sem compreensão adequada

---

### 2.4. Backtest — 15%

**O que avaliam:**
- Implementação do backtest **pela própria equipe** (Python, Excel, R — não ferramentas black-box)
- Coerência entre o modelo proposto e a simulação realizada
- Adequação do período de análise (justificado)
- Consistência das escolhas metodológicas

**Mitigação de vieses — a banca observa especificamente:**
- Escolhas oportunistas de período (cherry-picking temporal)
- Simulações inconsistentes com a lógica da estratégia
- Ausência de justificativas para decisões metodológicas
- Overfitting e look-ahead bias

**Detalhes técnicos:**
- Período de backtest é livre, mas deve ser **justificado**
- Divisão treino/teste (out-of-sample) **não é obrigatória**, mas bem-vinda
- Custos de transação/slippage **não são obrigatórios**, mas adicionam realismo
- Uso de **benchmark é altamente recomendável** (Ibovespa, S&P 500, CDI, etc.)

**O que valorizam:**
- Backtests replicáveis, transparentes e coerentes com a proposta

---

### 2.5. Análise dos Resultados — 15%

**O que avaliam:**
- Análise de **retorno e risco** (não apenas retorno)
- Identificação de **limitações** do modelo
- Clareza na **apresentação** dos resultados (priorizar gráficos/tabelas)
- Consistência da interpretação

**A equipe deve demonstrar capacidade de:**
- Explicar o comportamento da estratégia ao longo do tempo
- Identificar cenários favoráveis e desfavoráveis
- Reconhecer limitações de forma objetiva

**Pontos negativos:**
- Apresentação exclusivamente descritiva de métricas (listar números sem interpretar)
- Ausência de análise crítica
- Omissão de fragilidades do modelo

> **Princípio-chave:** Um resultado ruim no backtest **não elimina a equipe**. A banca avalia honestidade analítica e capacidade de interpretação.

---

### 2.6. Conclusão e Próximos Passos — 10%

**O que avaliam:**
- Coerência entre resultados e conclusões
- Qualidade das recomendações de evolução
- Realismo das propostas apresentadas

**A equipe deve demonstrar maturidade ao:**
- Reconhecer os limites do modelo
- Evitar conclusões desproporcionais às evidências
- Indicar caminhos claros e realistas para aprimoramento

**Pontos negativos:**
- Conclusões genéricas ou pouco fundamentadas
- Ausência de direcionamento futuro
- Exagero na interpretação dos resultados

---

### 2.7. Uso de IA Generativa — 15%

**O que avaliam:**
- A etapa do projeto em que a IA foi utilizada
- A relevância da aplicação
- O impacto efetivo no desenvolvimento do trabalho
- A clareza na explicação do uso

**Usos válidos de GenAI (exemplos):**
- Geração e estruturação de ideias/hipóteses
- Auxílio técnico: código, limpeza de dados, análise
- Organização e comunicação do projeto (revisão do relatório)
- Interpretação de resultados e limitações
- Design e identidade do robô
- Análise de sentimento de notícias (se integrado ao modelo)

**Informações que devem constar:**
1. **Etapa de aplicação** (ideação, código, revisão, visualização, etc.)
2. **Ferramenta utilizada** (ChatGPT, Gemini, Copilot, etc.)
3. **Contribuição efetiva** para o trabalho
4. **Distinção clara** entre conteúdo da equipe vs. conteúdo gerado por IA

**Não é obrigatório:** Mostrar prompts (mas pode ajudar a ilustrar). Dedicar uma página inteira (pode estar distribuído no relatório).

**O que valorizam:**
- Aplicações concretas, relevantes e claramente explicadas

**Pontos negativos:**
- Uso superficial ou meramente declaratório ("usamos IA para gerar ideias")
- Ausência de impacto prático demonstrado
- Falta de compreensão do papel da IA na solução

---

## 3. Princípios da Banca Avaliadora

A banca **não** busca o modelo mais complexo ou o melhor retorno histórico. Os princípios centrais são:

1. **Qualidade da construção** > resultado do backtest
2. **Coerência metodológica:** lógica clara entre hipótese → modelagem → teste
3. **Neutralidade à complexidade:** estratégias simples bem executadas valem mais que complexas mal justificadas
4. **Capacidade de explicação:** domínio sobre dados, premissas, lógica, backtest e limitações
5. **Análise crítica honesta:** reconhecer falhas é mais valorizado que escondê-las

**Critérios de desempate:** Clareza da tese, consistência e capacidade de defesa técnica.

---

## 4. Guia de Formatação e Comunicação

### Estrutura do PDF (5 páginas, 16:9)

| Aspecto | Diretriz |
| :--- | :--- |
| **Palavras totais** | Referência: < 750 palavras |
| **Visuais** | Priorizar gráficos, tabelas, diagramas, fluxogramas |
| **Texto** | Evitar blocos longos; usar bullets e frases concisas |
| **Ferramentas** | Livre: PowerPoint, Google Slides, Canva, LaTeX, Figma |
| **Legibilidade** | Deve ser legível em tela cheia sem zoom |
| **Fórmulas/código** | Permitidos se ajudam a explicar a lógica |
| **Idioma** | Português (termos técnicos em inglês permitidos) |
| **Links/QR Codes** | Não recomendados (avaliadores não acessam) |

### Distribuição Sugerida de Conteúdo por Página

| Página | Conteúdo Principal | Peso coberto |
| :---: | :--- | :---: |
| **1** | Robô (nome, identidade visual, conceito) + Hipótese da estratégia | 5% + 20% |
| **2** | Modelagem (fluxo de dados, lógica, sinais, decisões) | 20% |
| **3** | Backtest (metodologia, período, premissas, mitigação de vieses) | 15% |
| **4** | Análise de Resultados (gráficos, métricas risco/retorno, cenários, limitações) | 15% |
| **5** | Conclusão + Próximos Passos + Uso de IA Generativa | 10% + 15% |

> Esta distribuição é sugestiva. A equipe tem liberdade para reorganizar, desde que cubra todos os 7 critérios dentro do limite de 5 páginas.

---

## 5. Checklist Pré-Entrega

- [ ] PDF em formato 16:9 (widescreen)
- [ ] Máximo de 5 páginas (incluindo capa, se houver)
- [ ] Arquivo nomeado com a chave de envio: `[CHAVE].pdf`
- [ ] **Zero** menções a nomes de membros, equipe ou universidade
- [ ] Robô com nome, design e explicação do nome
- [ ] Hipótese de investimento explícita e clara
- [ ] Fluxo do modelo: entrada → processamento → saída
- [ ] Backtest implementado pela equipe (não black-box)
- [ ] Período do backtest justificado
- [ ] Benchmark utilizado (recomendado)
- [ ] Análise de risco e retorno (não apenas retorno)
- [ ] Limitações do modelo reconhecidas
- [ ] Cenários favoráveis e desfavoráveis identificados
- [ ] Uso de IA Generativa descrito com exemplos concretos
- [ ] Ferramenta(s) de IA mencionada(s)
- [ ] Contribuição efetiva da IA demonstrada
- [ ] Conclusões proporcionais às evidências
- [ ] Próximos passos realistas indicados
- [ ] < 750 palavras no total (referência)
- [ ] Prioritariamente visual (gráficos > texto)
- [ ] Legível em tela cheia sem zoom

---

## 6. Nota sobre Divergência entre Documentos

O **Regulamento** apresenta pesos ligeiramente diferentes (Backtest = 20%, IA = 10%) em relação ao **Manual de Avaliação oficial**, ao **Edital** e às **Diretrizes do Relatório Final** (Backtest = 15%, IA = 15%). O regulamento também menciona "até 10 páginas", enquanto as diretrizes do relatório estabelecem **5 páginas com eliminação para 6+**.

**Recomendação:** Seguir os pesos e limites do **Manual de Avaliação** e das **Diretrizes do Relatório Final**, pois são os documentos mais específicos e recentes sobre a avaliação e o formato da entrega.

---

> **Filosofia do desafio:** *"Não é sobre fazer o modelo mais complexo — é sobre fazer um modelo bem pensado, bem testado e bem explicado."*
