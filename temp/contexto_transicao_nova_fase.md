# Contexto de Transição e Guia-Mestre do Projeto Nexus
## Desafio Itaú Asset Quant AI 2026

> **Data de Atualização:** 16 de Agosto de 2026  
> **Status:** Repositório 100% Auditado, Consolidado e Sincronizado (`main` @ commit `e32eb1b`)  
> **Finalidade:** Servir como documento de transição e ponto de partida definitivo para a construção da base textual e gráfica em `docs/resumo_final_completo` e para o **Relatório Final (PDF de 5 Páginas, Formato 16:9)**.

---

## 1. Visão Executiva e Estado Atual do Projeto

O projeto **Robô Nexus** alcançou **consistência metodológica e matemática estrita**. Todos os dados brutos e processados possuem integridade garantida por hashes SHA-256 imutáveis, o motor de simulação foi centralizado e testado, e todas as métricas publicadas nos documentos `docs/01` a `docs/15` e nas imagens de `images/relatorio/` derivam da mesma esteira reproduzível.

### A Conclusão Científica Central do Projeto
O projeto desenvolveu e testou uma estratégia quantitativa em 4 camadas baseada em **Teoria de Redes Complexas (MST de Mantegna) + Filtros de Momentum + Cap CVM 175 + Filtro de Regime Topológico**:

1. **A Hipótese de Periferia é Válida:** Selecionar ativos com menor dependência do fator comum de mercado (ações periféricas / descorrelacionadas) com tendência de alta confirmada por momentum **superou o CDI e o Ibovespa no período cego Out-of-Sample (2019–2026)**, entregando **CAGR de 9.7% a.a.** e batendo **100% das carteiras do nulo pareado (p-value = 0.0%)**.
2. **O Diagnóstico da MST (Micro vs. Macro):**
   - **No Nível Micro (Seleção de Carteira):** A Minimum Spanning Tree (MST) descarta 97.5% das arestas da matriz de correlação (3.081 de 3.160 pares). Essa poda (*pruning*) radical introduz ruído amostral excessivo em correlações fracas, gerando alto giro de carteira (**57.3% no OOS**) que corrói o retorno da variante V3. O estimador direto de **Menor Correlação Média (Nexus V5)** utiliza a matriz de densidade completa, reduzindo o turnover para **35-39%** e preservando o retorno.
   - **No Nível Macro (Gestão de Cauda e Risco Sistêmico):** A MST é um instrumento excepcional de **Filtro de Regime**. Ao se contrair em momentos de pânico generalizado (COVID em março/2020), o filtro topológico cortou a exposição a ações para 30%, **reduzindo a volatilidade do portfólio no OOS de 21.6% para 19.5% (-2.1 p.p. de risco)** e mantendo o retorno anualizado em **9.5% a.a.**
3. **A Narrativa Vencedora:** O projeto não vende um "Sharpe milagroso artificial", mas sim um **Arco Completo de Engenharia Quantitativa e Falsificação Científica**, demonstrando maturidade institucional, aplicação rigorosa da Navalha de Occam, enquadramento regulatório CVM 175 e uso pioneiro de IA Generativa na auditoria de hipóteses.

---

## 2. A Tabela Mestra Consolidada de Resultados

Todas as métricas abaixo foram extraídas diretamente dos parquets oficiais gerados pelo motor centralizado (`src/nexus/motor.py`):

| Estratégia / Variante | Período In-Sample (2011–2018: 91 meses)<br>CAGR \| Vol \| Sharpe \| MDD \| Turn. | Período Out-of-Sample (2019–2026: 91 meses)<br>CAGR \| Vol \| Sharpe \| MDD \| Turn. | Papel na Tese e Arquitetura |
|---|---|---|---|
| **Nexus V5 + Regime (Completo)** | **14.9%** \| **13.9%** \| **+0.332** \| **-12.3%** \| 35.5% | **9.5%** \| **19.5%** \| **+0.005** \| **-35.6%** \| **35.1%** | **Arquitetura Final:** Micro (Menor Corr) + Macro (Regime MST) + Cap CVM 175 |
| **Nexus V5 (Menor Corr. Média)** | 14.3% \| 14.0% \| **+0.288** \| -12.3% \| 35.4% | **9.7%** \| 21.6% \| **+0.014** \| **-35.6%** \| **39.0%** | Seleção densa sem perda de informação por pruning |
| **Nexus V3 + Regime** | 13.1% \| 14.6% \| +0.195 \| -13.6% \| 54.8% | 1.7% \| 20.5% \| -0.378 \| -43.0% \| 50.9% | MST micro com proteção macro de regime |
| **Nexus V3 (MST Oficial)** | 12.2% \| 14.9% \| **+0.127** \| -13.6% \| 55.7% | 0.0% \| 22.0% \| -0.427 \| -43.1% \| 57.3% | Linha de base da hipótese original via Farness |
| **V2 (MST + Mom SEM Cap)** | 12.0% \| 16.7% \| **+0.101** \| -14.2% \| 62.6% | — | Isola a contribuição do Cap de 10% (+0.026 no Sharpe) |
| **V1 (MST Pura SEM Momentum)** | 3.9% \| 18.4% \| **-0.347** \| -44.4% \| 57.7% | — | MVP original: prova que topologia pura destrói capital |
| **V0 (Universo 80 Equal-Weight)** | 7.9% \| 20.6% \| **-0.118** \| -39.1% \| 2.4% | — | Piso neutro de mercado |
| *CDI (Benchmark Principal)* | 10.3% \| 0.7% \| 0.000 \| 0.0% \| 0.0% | 9.4% \| 1.2% \| 0.000 \| 0.0% \| 0.0% | Custo de oportunidade da renda fixa livre de risco |
| *Ibovespa (Mercado Amplo)* | 6.2% \| 23.3% \| -0.176 \| -43.7% \| — | 9.2% \| 22.6% \| -0.008 \| -40.1% \| — | Índice de mercado de referência |
| *BOVA11 (ETF Investível)* | 6.1% \| 23.5% \| -0.181 \| -43.9% \| — | 9.5% \| 22.6% \| +0.003 \| -40.3% \| — | Mercado acionário líquido de taxa de gestão |

---

## 3. O Arco Histórico de Falsificação e Descobertas (Dia a Dia)

```
[Etapa 1: Dados] 317 tickers -> 68 datas fantasmas eliminadas -> 47 renames -> 6 falidas resgatadas
      ↓
[Etapa 2: Topologia] Betweenness degenerada (54% zeros) -> Farness eleita -> MVP puro Sharpe -0.347
      ↓
[Etapa 3: Cascata & Occam] ML preditivo Walk-Forward (Sharpe 0.053) DESCARTADO -> Momentum SMA150 (+0.127)
      ↓
[Etapa 4: Auditoria & Integridade] Bug de giro corrigido -> SHA-256 travado -> Nulo Pareado p=51% (49%)
      ↓
[Etapa 5: Out-of-Sample Cego] MST V3 degrada por giro (57%) -> Menor Corr V5 bate CDI/IBOV (9.7% a.a., p100%)
      ↓
[Etapa 6: Sinergia Final] Nexus V5 + Regime Topológico MST corta vol para 19.5% (-2.1 p.p.) e consolida 9.5% a.a.
```

### 1. Auditoria e Limpeza de Dados de Alta Resolução
- **O Mito do Survivorship Bias Generalizado:** A equipe auditou 317 tickers da B3. Descobriu que 47 renomeações societárias preservam todo o histórico sob o novo código no Yahoo Finance. Foram resgatadas 6 empresas mortas históricas (OGXP3, FIBR3, BRPR3, ELPL4, VVAR11, PRML3) que participam ativamente do backtest, e catalogados exatamente os 26 casos sem sucessor.
- **Detecção das 68 Cotações Fantasma:** O Yahoo Finance publicava dados em feriados com 1 a 5 tickers. Isso fazia o universo colapsar de 80 para 4 ações todo mês de janeiro. A reconstrução do calendário oficial de 3.875 pregões eliminou essa distorção.
- **Preço Bruto vs. Preço Ajustado:** Volume financeiro calculado estritamente com preços brutos (`Close`) e retornos calculados com preços ajustados (`Adj Close`), evitando subestimar a liquidez passada em até 4.5×.

### 2. A Degenerescência da Betweenness Centrality
- A formulação teórica inicial propunha selecionar ações por menor Betweenness Centrality na MST.
- O teste empírico revelou que em uma árvore conexa, **41 a 48 das 80 ações (54%) empatam exatamente em Betweenness zero todo mês**. A seleção de um "Top 10" seria decidida por ordem alfabética.
- **Correção:** A métrica foi substituída por **Farness** (soma das distâncias geodésicas na MST), que é estritamente contínua e imune a empates.

### 3. A Falha do MVP Topológico e a Arquitetura em Cascata
- O backtest da topologia pura (comprar o Top 10 de Farness sem filtros) produziu Sharpe de **-0.347** e Max Drawdown de **-44.4%**.
- **Diagnóstico:** A topologia diz *onde olhar* (ações com risco idiossincrático), mas não diz *quando comprar*. Ações periféricas podem estar em queda livre.
- **A Solução em Cascata:** Introdução da camada de momentum direcional (SMA 150) e do teto de alocação de 10% por ativo (CVM 175), com o excedente aplicado em CDI.

### 4. A Aplicação da Navalha de Occam (Descarte do Machine Learning)
- Desenvolveu-se um classificador Random Forest/XGBoost com 9 features técnicas para prever retornos positivos nos próximos 10 dias.
- Com esteira de *Walk-Forward* rigorosa (sem *data leakage*), o ML entregou Sharpe de apenas **+0.053**.
- O filtro simples de Momentum (preço > SMA 150) entregou Sharpe de **+0.127**.
- **Decisão:** O modelo de ML foi formalmente descartado pela Navalha de Occam (*"complexidade sem ganho estatístico comprovado é overfitting"*).

### 5. O Teste de Monte Carlo Corrigido (`docs/13`)
- A alegação inicial de significância estatística ("p-value = 3.2%") comparava o Nexus (que detém caixa em CDI) contra macacos 100% investidos em ações num período em que o CDI superou a bolsa.
- O **Nulo Pareado de 200 sorteios (N2)**, submetido às exatas mesmas regras de momentum e caixa da estratégia oficial, revelou que o V3 (MST) fica no **percentil 49.0% (p-value = 51.0%)**. Ou seja, a seleção de pool via MST empatou com um sorteio aleatório.

### 6. O Teste Cego Out-of-Sample e a Descoberta Micro-Macro (`docs/14`)
- No teste cego (2019–2026), a variante **Nexus V3 (MST)** degradou para CAGR 0.0% (Sharpe -0.427) devido a turnover excessivo de 57.3% provocado pelo descarte de 97.5% das arestas na árvore geradora mínima.
- O controle de **Menor Correlação Média (Nexus V5)**, que utiliza a matriz densa completa, reduziu o giro para **39.0%**, atingiu **CAGR de 9.7% a.a.** (superando o CDI de 9.4% e o Ibovespa de 9.2%) e ficou no **percentil 100.0% contra o nulo pareado OOS (p-value = 0.0%)**.
- Ao acoplar o **Filtro de Regime Topológico da MST**, o **Nexus V5 + Regime** reduziu a volatilidade para **19.5% (-2.1 p.p. de risco)** durante os choques de 2020 e 2021-2022, mantendo **9.5% a.a.** de retorno e drawdown de **-35.6%**.

---

## 4. O Papel da IA Generativa (15% da Nota) — Os 5 Pilares

O projeto documenta o uso de IA Generativa de forma madura, auditável e com exemplos reais onde a IA mudou o rumo da pesquisa:

| Pilar de Atuação | Como a IA foi utilizada | Impacto Prático no Projeto |
|---|---|---|
| **1. Ideação & Formalização Teórica** | Mapeamento da literatura acadêmica (Mantegna 1999, Onnela 2003, Peralta 2016) e formalização da métrica de distância $d_{ij} = \sqrt{2(1-\rho_{ij})}$. | Construção de hipótese econômica sólida com 3 pilares acadêmicos. |
| **2. Auditoria e Engenharia de Dados** | Detecção automatizada das 68 cotações fantasmas em feriados e teste sistemático dos 317 tickers da B3. | Eliminação de distorções em 9 rebalanceamentos e resgate de 6 empresas deslistadas. |
| **3. Auditoria Matemática & Algorítmica** | Prova matemática da degenerescência da Betweenness Centrality em grafos acíclicos (MST). | Prevenção de uma falha de seleção onde 54% dos ativos empatariam em zero. |
| **4. Falseamento de Hipóteses (Occam)** | Implementação de validação Walk-Forward para ML, evidenciando sobreajuste e justificando seu descarte em favor da SMA 150. | Defesa metodológica irrefutável contra complexidade desnecessária. |
| **5. Diagnóstico de Microestrutura** | Identificação do efeito de *pruning* da MST (perda de 97.5% das arestas) e proposta do controle por Menor Correlação Média. | Criação da versão vencedora Nexus V5 (+Regime), superando CDI e Ibovespa no OOS. |

> **Menção de Limitação Obrigatória da IA (Rigor Crítico):**  
> Na fase inicial, a IA alucinou o ticker `SOUZ3` (que não existe na B3, sendo o código correto `CRUZ3`). Isso gerou a falsa impressão de que a base sofria de survivorship bias severo. A equipe estabeleceu um protocolo de verificação cruzada automática onde **nenhum ativo é consumido sem teste prévio de existência e validação em API oficial**.

---

## 5. Diretrizes e Storytelling para o Relatório Final (5 Páginas)

### Orientações Oficiais do Itaú Asset:
- **Formato:** Apresentação em PDF, 16:9 widescreen, **estritamente 5 páginas**.
- **Anonimato Obrigatório:** Zero nomes de autores, universidade ou time.
- **Volume de Texto:** Menos de **750 palavras** no total (altamente visual).
- **Critério de Ouro:** Clareza, objetividade e facilidade de leitura para uma banca de gestores e pesquisadores quantitativos seniores.

### Estrutura Sugerida para as 5 Páginas:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ PÁGINA 1: IDENTIDADE DO ROBÔ & A TESE ECONÔMICA                                         │
│ • Robô Nexus: O Navegador de Redes Complexas (Identidade Visual & Conceito - 5%)        │
│ • Hipótese Central: Extração de Alpha Idiossincrático na Periferia do Mercado           │
│ • Diagrama Arquitetural em Cascata: Liquidez -> Descorrelação -> Momentum -> Regime     │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ PÁGINA 2: MODELAGEM SISTEMÁTICA & ENGENHARIA DE DADOS                                   │
│ • Pipeline sem Look-Ahead: 80 Ações Líquidas, Preço Bruto vs Ajustado, Calendário Limpo │
│ • Topologia de Redes (MST de Mantegna): Farness vs Betweenness Degenerada               │
│ • Filtro Direcional (Momentum SMA 150) & Enquadramento CVM 175 (Cap 10% + Caixa CDI)    │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ PÁGINA 3: ABLAÇÃO IN-SAMPLE & O VEREDITO DE OCCAM                                       │
│ • Tabela de Ablação por Camadas (V0 a V6): De onde vem o retorno real (+0.473 Momentum) │
│ • Descarte do ML Preditivo via Walk-Forward (Occam: Sharpe 0.053 vs 0.127)              │
│ • Teste de Monte Carlo Corrigido: N1 Clássico (p=8%) vs N2 Pareado (p=51%)              │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ PÁGINA 4: O TESTE CEGO OUT-OF-SAMPLE (2019–2026) & DIAGNÓSTICO MICRO-MACRO              │
│ • Curva de Equity OOS (Nexus V5 vs Nexus V3 vs CDI vs BOVA11)                           │
│ • O Efeito Pruning da MST (Perda de 97.5% das Arestas) -> Giro Excessivo de 57.3%      │
│ • A Vitória do Nexus V5: CAGR 9.7% a.a., p100% no Nulo Pareado e Vol Contida em 19.5%   │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ PÁGINA 5: CONCLUSÕES, GOVERNANÇA & O PAPEL DA IA GENERATIVA                             │
│ • Síntese do Arco de Falsificação Científica e Maturidade Institucional                 │
│ • Os 5 Pilares de Atuação da IA Generativa (com Limitações e Protocolos de Validação)   │
│ • Próximos Passos: Métricas de Informação Mútua e Alocação por Risco Marginal           │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Mapeamento de Artefatos no Repositório

### Scripts Executáveis (`scripts/`):
- `14_ablacao_atribuicao.py` — Simulação das variantes V0 a V6 e atribuição por camadas.
- `15_monte_carlo_corrigido.py` — Bateria de 3 nulos de Monte Carlo (N1, N2, N3).
- `16_calibracao_regime.py` — Calibração do percentil expansível do filtro de regime.
- `17_out_of_sample.py` — Teste cego OOS com Nexus V3, V5, V5+Regime e benchmarks.
- `18_cv_temporal.py` — Validação cruzada temporal em 3 folds expansíveis.
- `19_graficos_auditoria.py` e `14_graficos_relatorio.py` — Suíte de geração gráfica.

### Documentação Técnica (`docs/`):
- `05_calibracao_momentum_cv.md` — Relatório da validação cruzada temporal.
- `12_ablacao_e_atribuicao.md` — Relatório completo de ablação in-sample.
- `13_monte_carlo_corrigido.md` — Relatório do teste de Monte Carlo de três nulos.
- `14_out_of_sample.md` — Relatório do teste cego Out-of-Sample e diagnóstico da V5.
- `15_filtro_regime.md` — Relatório de calibração do regime topológico.

### Imagens Prontas para o Relatório (`images/relatorio/`):
- `rel_01_mst_comparativa.png` — MST em mercado calmo vs. crise de maio/2020.
- `rel_02_equity_insample.png` — Curva de patrimônio in-sample vs benchmarks.
- `rel_03_montecarlo.png` — Distribuição de Monte Carlo.
- `rel_04_custos.png` — Análise de sensibilidade a custos de transação.
- `rel_05_drawdown.png` — Curvas de drawdown histórico.
- `rel_06_alocacao.png` — Dinâmica de alocação de ativos e caixa ao longo do tempo.
- `rel_07_ablacao_variantes.png` — Gráfico de barras com Sharpe de cada variante.
- `rel_08_nulo_pareado.png` — Histograma do nulo pareado in-sample.
- `rel_09_oos_equity.png` — Curva de patrimônio Out-of-Sample (Nexus V5+Regime vs V3 vs CDI vs BOVA11).
- `rel_10_regime_drawdown.png` — Efeito protetor do filtro de regime nos drawdowns.

---

Este documento consolida o estado da arte do projeto e serve como **ponte de transição de alta fidelidade** para as próximas sessões.
