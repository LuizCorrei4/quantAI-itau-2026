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