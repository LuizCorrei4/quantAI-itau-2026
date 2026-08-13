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
- [x] **Feature Engineering & ML:** Regressão Logística sagrou-se vitoriosa contra Random Forest e XGBoost (`scripts/11_feature_engineering.py` e `12_train_ml.py`).
- [x] **Batalha dos Filtros Final:** A arquitetura em Cascata (Momentum + ML) atingiu inacreditáveis **0.481 de Sharpe In-Sample**, derrotando a barreira dos macacos e se provando superior ao Momentum Puro (`08_backtest_alpha.py`). Merge na `main` efetuado com sucesso!

> **Transição:** O escopo da Pessoa 1 está oficialmente **encerrado**. A arquitetura Alpha comprovou seu valor. A bola agora está exclusivamente com a Pessoa 2 para a criação do Filtro de Regime.

### ⚠️ Regras Inegociáveis
- **Travar L e Pool com base na CV Temporal (2011-2018).** O parâmetro escolhido deve ser estável nos 3 folds temporais. NÃO olhar o out-of-sample (2019-2026) antes de decidir.
- **Reportar TODAS as combinações testadas**, não só a vencedora. A transparência pontua mais que o resultado.
- Se o Momentum não melhorar o Sharpe no in-sample → reportar honestamente e manter o MVP puro como versão final. Resultado nulo bem documentado > maquiagem.

---

## Pessoa 2: "Analista de Risco & Regime" 
**Branch:** `feat/filtros-robustez`

### Missão Central
Implementar o **Filtro de Regime com escada de degraus** e calibrá-lo com rigor metodológico In-Sample/Out-of-Sample. A novidade é que agora o Filtro de Regime opera **sobre a carteira já filtrada pelo Momentum**, não sobre o MVP puro.

Ler obrigatoriamente o `docs/resumo_descomplicado_mvp.md` antes de começar.

### Dados que já estão prontos para você
- `dados/resultados/serie_retornos_nexus.parquet` — contém a coluna `dist_media_mst` (o termômetro do regime!)
- `dados/resultados/farness_completa.parquet` — Farness das 80 ações, todos os meses
- `src/nexus/mst.py` — função `calcular_distancia_media_mst()` pronta para importar
- 🆕 `src/nexus/alpha_filters.py` — módulo dos Filtros de Alpha (assim que a Pessoa 1 entregar)

### Cronograma

| Dia | Tarefa | Detalhes |
|---|---|---|
| **11-12/ago** | **Escada de Defesa:** Implementar a lógica de 3 níveis (🟢 100% ações / 🟡 50-50 / 🔴 20% ações + 80% CDI) usando a `dist_media_mst` como termômetro | Criar `src/nexus/regime.py` |
| **12/ago** | **Calibração com CV Temporal (2011-2018):** Testar combinações de percentis (5/10, 10/15, 10/20, 5/15) usando **Validação Cruzada Temporal** (mesmos 3 folds da Pessoa 1). Anotar o Sharpe de cada uma por fold. Escolher a mais estável e **travar** | Salvar tabela completa em `docs/calibracao_regime_cv.md` |
| **13/ago** | **Teste Cego Out-of-Sample (2019-2026):** Aplicar os percentis travados, sem alterar nada. Medir Sharpe, Drawdown e comparar com MVP puro | Script `08_backtest_com_regime.py` |
| **13/ago** | **Quantificar atraso do filtro:** Em cada crise (2015, 2018, 2020, 2022), medir quantos meses o filtro demorou para reagir | Incluir no relatório |
| **13/ago (extra)** | 🆕 **Teste de camadas isoladas:** Comparar **4 versões**: (a) MVP puro, (b) MVP + Regime, (c) MVP + Momentum, (d) **MVP + Momentum + Regime** (cascata completa). Medir Sharpe, Drawdown e turnover de cada. Essa tabela é OURO para o relatório — mostra a contribuição marginal de cada filtro | `docs/comparativo_camadas.md` |
| **14/ago** | **Merge com Pessoa 1:** Integrar Momentum + Regime no backtest final. Rodar out-of-sample combinado com parâmetros travados | Branch `main` |

### Atenção Crítica
- **NÃO** escolha os percentis olhando o out-of-sample. Isso é overfitting e a banca perceberá.
- **REPORTE TODAS** as variantes testadas, não só a vencedora. Transparência vale mais pontos.
- O teste de camadas isoladas (13/ago extra) é essencial para defender a arquitetura em cascata: se Momentum + Regime combinados forem melhores que cada um isolado, a tese da cascata está validada.

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
| **12/ago (noite)** | 🆕 **Quick sync:** Pessoa 1 mostra primeiros resultados do Momentum no in-sample. Verificar se os filtros produzem resultados sensatos antes de prosseguir. Decisão: o ML é necessário ou o Momentum já resolve? |
| **13/ago (noite)** | 🆕 **Checkpoint de dados:** Pessoa 2 mostra tabela comparativa das 4 versões (MVP / +Regime / +Momentum / +Cascata). Pessoa 3 confirma que o diagrama de cascata está pronto |
| **14/ago (noite)** | Merge das 3 branches em `main`. Pessoa 3 recebe os últimos gráficos e números |
| **15/ago** | Revisão coletiva do PDF. Checar: anonimato total, 5 páginas exatas, < 750 palavras, gráficos legíveis |
| **16/ago** | Buffer de emergência + submissão do PDF até 23h59 |

---

## Contingência: E se o Momentum NÃO melhorar?

Se o Filtro de Momentum **não** melhorar o Sharpe no in-sample:
1. **Reportar honestamente** — resultado nulo é entrega legítima e pontua em Análise (15%) e Conclusão (10%).
2. **Manter o Filtro de Regime** como única melhoria sobre o MVP.
3. **Enquadrar no relatório**: "Testamos Momentum como filtro de alpha e demonstramos que, no contexto brasileiro de 2011-2026, a anomalia de momentum não se somou significativamente à seleção topológica. A diversificação via MST + a proteção do Regime Filter é a melhor combinação encontrada."
4. Isso é melhor do que forçar um resultado positivo e ser pego pela banca.
