# Divisão de Tarefas (Sprint Final: 10/08 a 16/08)

**Atualizado em:** 12/ago/2026, 12h00  
**Contexto:** O pipeline de dados (scripts 01-05), a avaliação de métricas (script 06) e o **MVP do backtest** (script 07 + módulos `mst.py` e `portfolio.py`) já estão finalizados. Os resultados do MVP revelaram **Sharpe negativo (-0.21)** e **turnover excessivo (67%)**, confirmando que a seleção topológica pura não gera alpha no Brasil. A equipe decidiu adotar uma **arquitetura em cascata**: a MST passa a ser um *Filtro de Universo Descorrelacionado*, e novos **Filtros de Alpha** (Momentum + ML opcional) são aplicados sobre as ações periféricas para gerar convicção direcional. A Pessoa 1 lidera a implementação dos Filtros de Alpha, a Pessoa 2 continua com o Filtro de Regime e integra as camadas, e a Pessoa 3 atualiza o relatório com a nova arquitetura.

---

## Pessoa 1: "Core Quant" 
**Branch:** `feat/alpha-filters` → mergear em `main` quando estável

### ✅ Concluído (10-11/ago)
- [x] Avaliação e cravação da métrica Farness (`scripts/06_avaliar_periferia.py`, `docs/decisao_metrica_periferia_MST.md`)
- [x] Módulos reutilizáveis do robô (`src/nexus/mst.py`, `src/nexus/portfolio.py`)
- [x] Loop completo do backtest MVP em 183 meses (`scripts/07_backtest.py`)
- [x] Série de retornos, carteiras mensais e farness completa salvos em `dados/resultados/`
- [x] Gráficos automáticos e relatório `docs/resumo_backtest_mvp.md`
- [x] Análise descomplicada com roteiro para a Pessoa 2 
### ✅ Concluído: Filtros de Alpha e Batalha Final (12-13/ago)
- [x] **Módulo de Filtros de Alpha:** Implementação de `src/nexus/alpha_filters.py` com lógicas de Momentum e Machine Learning.
- [x] **Calibração Momentum CV:** Validação cruzada (In-Sample 2015 a 2018) cravou a Média Móvel de 150 dias como a mais robusta (`scripts/10_grid_search_alpha.py`).
- [x] **Teste de Macacos (Monte Carlo):** Threshold de 95% de p-value definido em **Sharpe 0.107** (`scripts/09_baseline_aleatorias.py`).
- [x] **Feature Engineering & ML:** O ML (Regressão Logística) foi testado adequadamente via `Walk-Forward Expanding Window` para evitar *Data Leakage*. (`scripts/11_feature_engineering.py` e `scripts/12_train_ml.py`).
- [x] **Veredito de Occam & CVM 175:** O Momentum Puro (SMA 150) venceu a barreira dos macacos (Sharpe In-Sample de **0.122**) e superou o ML (Sharpe **0.053**). O modelo preditivo de ML foi **descartado** por princípio da parcimônia. Adicionamos a Regra de CAP de 10% de exposição por ativo (Resolução CVM 175).
- [x] **Branch Mergeada:** Todo o código de alpha, auditoria e CVM foi consolidado em `main`.

> **Transição:** O escopo da Pessoa 1 está oficialmente **encerrado**. A arquitetura Alpha (Momentum Puro) comprovou seu valor. A bola agora está exclusivamente com a Pessoa 2 para a criação do Filtro de Regime Topológico.

### ⚠️ Regras Inegociáveis
- **Testes Exaustivos In-Sample:** O filtro de regime e a nova ordem de operações (antes vs. depois do momentum) devem ser testados **à exaustão** apenas nos dados In-Sample (2011-2018).
- **Proibido Olhar o Out-Of-Sample:** ZERO contato com o período Out-of-Sample (2019-2026) até termos certeza absoluta da nossa configuração.
- **Janela de Teste OOS Restrita:** Só rodaremos os testes no Out-Of-Sample no sábado ou domingo (dia 15 ou 16), às vésperas da entrega, como teste cego definitivo.

---

## Pessoa 2: "Analista de Risco & Regime" 
**Branch:** `feat/filtros-robustez` (a ser criada a partir da `main` recém-mergeada)

### Missão Central
O último desafio técnico: implementar e testar o **Filtro de Regime Topológico**.
A grande dúvida que deve ser exaustivamente testada no **In-Sample**: Este filtro deve atuar **antes** ou **depois** do Filtro de Momentum? Qual arquitetura traz o melhor balanço risco-retorno no In-Sample?

### Cronograma de Ações Finais

| Dia | Tarefa | Detalhes |
|---|---|---|
| **14-15/ago** | **Testes Exaustivos In-Sample:** Criar a mecânica do filtro de regime (usando dist_media_mst como termômetro) e fazer dezenas de iterações no In-Sample (2011-2018) alternando a ordem (Momentum -> Regime vs Regime -> Momentum). | Encontrar a lógica ótima que não degrade o Sharpe de 0.122 do Momentum. |
| **15-16/ago** | **Quebra de Vidro (Out-Of-Sample):** Somente quando tivermos certeza da estabilidade da configuração no In-Sample, abriremos a "caixa preta" do período Out-Of-Sample (2019-2026) para rodar o backtest cego final. | Se tudo der certo, essa rodada final sela o projeto técnico. |
| **16/ago** | **Integração Relatório:** Enviar as métricas finais In-Sample e Out-Of-Sample para a Pessoa 3 embutir no PDF e diagramar. | `docs/comparativo_camadas.md` |

### Atenção Crítica
- **NÃO DESTRUA O ALPHA:** O filtro de regime deve proteger a carteira sem diluir o *alpha* recém-conquistado do Momentum. O foco é mitigação de Drawdown extremo.

---

## Pessoa 3: "Visual Storyteller" 
**Branch:** `feat/identidade-relatorio`

### Missão Central
Criar a identidade do Robô Nexus e montar o relatório PDF de 5 páginas, 16:9, altamente visual. **Atualização:** o diagrama de pipeline agora inclui a arquitetura em cascata (MST → Alpha Filters → Regime Filter).

### Cronograma

| Dia | Tarefa | Detalhes |
|---|---|---|
| **10-11/ago** | **Identidade Visual do Nexus:** Nome, logo, paleta de cores (neon sobre fundo escuro sugerido). Justificar coerência com a tese de grafos/redes | Logotipo e paleta salvos em `images/` |
| **11-12/ago** | **Esqueleto do PDF:** Montar o template 16:9 com as 5 páginas (Capa+Tese, Metodologia, Backtest, Análise Crítica, Conclusão). Já preencher tese e metodologia | Template em `relatorio/` ou ferramenta de slides |
| **12-13/ago** | **Visualizações da MST + Diagrama de Cascata:** (a) Usar `networkx` + `matplotlib` para gerar 2 grafos lado a lado (mercado calmo vs. março/2020), destacando as 10 ações periféricas. (b) 🆕 Criar diagrama visual da **arquitetura em cascata**: MST (Filtro de Universo) → Momentum (Filtro Direcional) → Regime (Filtro de Exposição). Esse diagrama substitui o pipeline linear antigo | Pode importar `from nexus.mst import construir_mst` |
| **13-14/ago** | **Seção "Uso de IA Generativa":** Documentar concretamente como o Gemini foi usado. 🆕 **Incluir obrigatoriamente**: (a) os 3 achados já documentados (survivorship, cotação fantasma, betweenness degenerada), (b) **NOVO**: a IA diagnosticou que o Sharpe negativo do MVP vinha da ausência de convicção direcional, e propôs a arquitetura em cascata com Filtros de Alpha. Incluir exemplos reais de prompts e respostas | Peso: 15% da nota! |
| **14-15/ago** | **Integração Final:** Receber gráficos e métricas das Pessoas 1 e 2. Inserir no PDF. Enxugar texto total para < 750 palavras. Verificar anonimato | PDF pronto para revisão |

### 🆕 Atualização na Página 2 (Metodologia)
A página de Metodologia agora precisa mostrar a **cascata de 3 filtros** como elemento visual central:
1. **Filtro de Universo (MST + Farness):** "Onde olhar" — seleciona ações descorrelacionadas
2. **Filtro de Alpha (Momentum):** "Quando comprar" — só compra se a ação está em tendência de alta
3. **Filtro de Regime (Distância Média MST):** "Quanto expor" — reduz exposição em crises sistêmicas

Esse diagrama é a nova "imagem-assinatura" do relatório, junto com as MSTs comparativas.

---

## Agenda Conjunta (Todo o time)

| Dia | Atividade |
|---|---|
| **14/ago (noite)** | **Merge de Alpha Finalizado.** Todo o modelo Veredito de Occam (Momentum Puro, Regras CVM) foi mergeado em `main`. |
| **15/ago** | **Dia D do In-Sample:** Pessoa 2 roda testes exaustivos do Filtro de Regime no In-Sample. Decisão da Ordem (Antes/Depois de Momentum). Pessoa 3 adianta PDF com toda a base teórica e dados in-sample prontos. |
| **16/ago (manhã)** | **Teste Cego Out-of-Sample:** Quebra do vidro! Backtest OOS rodado. Dados finais para o relatório. |
| **16/ago (noite)** | Revisão do PDF: anonimato, 5 páginas exatas, limites CVM, análise de custo embutida. |
| **17/ago** | Buffer final e submissão! |

---

## Contingência: E se o Momentum NÃO melhorar?

Se o Filtro de Momentum **não** melhorar o Sharpe no in-sample:
1. **Reportar honestamente** — resultado nulo é entrega legítima e pontua em Análise (15%) e Conclusão (10%).
2. **Manter o Filtro de Regime** como única melhoria sobre o MVP.
3. **Enquadrar no relatório**: "Testamos Momentum como filtro de alpha e demonstramos que, no contexto brasileiro de 2011-2026, a anomalia de momentum não se somou significativamente à seleção topológica. A diversificação via MST + a proteção do Regime Filter é a melhor combinação encontrada."
4. Isso é melhor do que forçar um resultado positivo e ser pego pela banca.
