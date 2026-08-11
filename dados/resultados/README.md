# Dados de Resultados do Backtest — Robô Nexus

Esta pasta contém os artefatos de saída gerados pela execução do **backtest** (produzidos pelo script `scripts/07_backtest.py`).

Esses dados servem como base auditável do projeto e são consumidos diretamente pelos scripts subsequentes (como o Filtro de Regime da Pessoa 2 e as visualizações da Pessoa 3).

---

## Estrutura dos Arquivos

### 1. `serie_retornos_nexus.parquet`
**Descrição:** Série temporal de retornos e métricas mensais do modelo Nexus MVP comparado aos benchmarks.

- **Índice:** `data_rebalanceamento` (Data do primeiro pregão útil do mês)
- **Colunas:**
  - `retorno_bruto` *(float)*: Retorno percentual bruto da carteira equal-weight do Top 10 periférico.
  - `retorno_liquido` *(float)*: Retorno descontado de custos de transação (b3 + corretagem).
  - `turnover` *(float)*: Fração da carteira girada no mês `(Σ|peso_novo - peso_antigo| / 2)`.
  - `custo` *(float)*: Impacto financeiro absoluto das taxas no mês.
  - `dist_media_mst` *(float)*: Média dos pesos das arestas da MST no mês (**termômetro para o Filtro de Regime**).
  - `retorno_ibov` *(float)*: Retorno do Ibovespa no mesmo período exato.
  - `retorno_bova11` *(float)*: Retorno do ETF BOVA11 no mesmo período exato.
  - `retorno_cdi` *(float)*: Retorno da taxa CDI no mesmo período exato.

---

### 2. `carteiras_mensais.parquet`
**Descrição:** Histórico detalhado de composição do portfólio (as 10 ações selecionadas em cada rebalanceamento).

- **Colunas:**
  - `data_rebalanceamento` *(datetime)*: Data de execução da montagem da carteira.
  - `ticker` *(string)*: Código da ação selecionada (ex: `ITSA4.SA`).
  - `farness` *(float)*: Valor exato da metric de Farness (soma das distâncias na MST) no momento da seleção.
  - `peso` *(float)*: Peso atribuído ao ativo na carteira (padrão MVP: `0.10` / 10%).

---

### 3. `farness_completa.parquet`
**Descrição:** Registro completo do valor de Farness para **todas as 80 ações** do universo elegível em cada mês (não apenas do Top 10).

- **Colunas:**
  - `data_rebalanceamento` *(datetime)*: Data do rebalanceamento.
  - `ticker` *(string)*: Código da ação.
  - `farness` *(float)*: Soma das distâncias mais curtas do nó até todos os outros nós na MST.

> **Nota:** Este arquivo permite que a Pessoa 2 ou a Pessoa 3 façam simulações com variação de tamanho de carteira (Top 5, Top 15, Top 20) sem precisar reprocessar os grafos da MST.
