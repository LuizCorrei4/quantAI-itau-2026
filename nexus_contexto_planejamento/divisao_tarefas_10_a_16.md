# Divisão de Tarefas (Sprint Final: 10/08 a 16/08)

**Atualizado em:** 11/ago/2026, 12h25  
**Contexto:** O pipeline de dados (scripts 01-05), a avaliação de métricas (script 06) e o **MVP do backtest** (script 07 + módulos `mst.py` e `portfolio.py`) já estão finalizados. Os resultados do MVP revelaram Sharpe negativo (-0.21) e turnover excessivo (67%), criando duas frentes de trabalho claras para as Pessoas 2 e 3. A Pessoa 1, com o core finalizado, assume a frente de **Testes de Robustez e Benchmarks Complementares**.

---

## Pessoa 1: "Core Quant" 
**Branch:** `feat/backtest-core` → mergear em `main` quando estável

### ✅ Concluído (10-11/ago)
- [x] Avaliação e cravação da métrica Farness (`scripts/06_avaliar_periferia.py`, `docs/decisao_metrica_periferia_MST.md`)
- [x] Módulos reutilizáveis do robô (`src/nexus/mst.py`, `src/nexus/portfolio.py`)
- [x] Loop completo do backtest MVP em 183 meses (`scripts/07_backtest.py`)
- [x] Série de retornos, carteiras mensais e farness completa salvos em `dados/resultados/`
- [x] Gráficos automáticos e relatório `docs/resumo_backtest_mvp.md`
- [x] Análise descomplicada com roteiro para a Pessoa 2 (`docs/resumo_descomplicado_mvp.md`)

### 🔜 Próximas Tarefas (12-14/ago)

A Pessoa 1 assume a frente de **Benchmarks Complementares e Testes de Robustez**, que são independentes do Filtro de Regime e podem rodar em paralelo:

| Dia | Tarefa | Entrega |
|---|---|---|
| **12/ago** | **Benchmark Equal-Weight das 80:** Rodar o backtest com TODAS as 80 ações elegíveis (sem seleção por Farness) para isolar se o efeito vem da seleção ou do peso igual | `dados/resultados/serie_retornos_equalweight80.parquet` |
| **12/ago** | **200 Carteiras Aleatórias:** Sortear 200x, 10 ações aleatórias do universo, medir Sharpe de cada. Gerar histograma e posicionar o Nexus como percentil | `images/histograma_sharpe_aleatorias.png` |
| **13/ago** | **Sensibilidade de Janela:** Rodar o backtest MVP com janelas de 42, 63 e 126 pregões. Comparar Sharpe e turnover | Tabela comparativa em `docs/` |
| **13/ago** | **Sensibilidade de Top N:** Rodar com Top 5, 10, 15 e 20. Ver se concentrar mais ou diluir melhora o resultado | Tabela comparativa em `docs/` |
| **14/ago** | **Merge com Pessoa 2:** Integrar o Filtro de Regime sobre os resultados do MVP. Rodar backtest final combinado | Branch `main` atualizada |

> **Por que a Pessoa 1 faz isso e não a Pessoa 2?** Porque esses testes usam o mesmo loop do `07_backtest.py` que a Pessoa 1 escreveu. Ela já conhece cada linha do código e consegue parametrizar rapidamente. Enquanto isso, a Pessoa 2 foca exclusivamente no Filtro de Regime, que é uma lógica nova e independente.

---

## Pessoa 2: "Analista de Risco & Regime" 
**Branch:** `feat/filtros-robustez`

### Missão Central
Implementar o **Filtro de Regime com escada de degraus** e calibrá-lo com rigor metodológico In-Sample/Out-of-Sample. Ler obrigatoriamente o `docs/resumo_descomplicado_mvp.md` antes de começar.

### Dados que já estão prontos para você
- `dados/resultados/serie_retornos_nexus.parquet` — contém a coluna `dist_media_mst` (o termômetro do regime!)
- `dados/resultados/farness_completa.parquet` — Farness das 80 ações, todos os meses
- `src/nexus/mst.py` — função `calcular_distancia_media_mst()` pronta para importar

### Cronograma

| Dia | Tarefa | Detalhes |
|---|---|---|
| **11-12/ago** | **Escada de Defesa:** Implementar a lógica de 3 níveis (🟢 100% ações / 🟡 50-50 / 🔴 20% ações + 80% CDI) usando a `dist_media_mst` como termômetro | Criar `src/nexus/regime.py` |
| **12/ago** | **Calibração In-Sample (2011-2018):** Testar todas as combinações de percentis (5/10, 10/15, 10/20, 5/15) e anotar o Sharpe de CADA uma em tabela. Escolher a melhor e **travar** | Salvar tabela completa em `docs/calibracao_regime_insample.md` |
| **13/ago** | **Teste Cego Out-of-Sample (2019-2026):** Aplicar os percentis travados, sem alterar nada. Medir Sharpe, Drawdown e comparar com MVP puro | Script `08_backtest_com_regime.py` |
| **13/ago** | **Quantificar atraso do filtro:** Em cada crise (2015, 2018, 2020, 2022), medir quantos meses o filtro demorou para reagir | Incluir no relatório |
| **14/ago** | **Merge com Pessoa 1:** Integrar robustez + regime no backtest final | Branch `main` |

### Atenção Crítica
- **NÃO** escolha os percentis olhando o out-of-sample. Isso é overfitting e a banca perceberá.
- **REPORTE TODAS** as variantes testadas, não só a vencedora. Transparência vale mais pontos.

---

## Pessoa 3: "Visual Storyteller" 
**Branch:** `feat/identidade-relatorio`

### Missão Central
Criar a identidade do Robô Nexus e montar o relatório PDF de 5 páginas, 16:9, altamente visual.

### Cronograma

| Dia | Tarefa | Detalhes |
|---|---|---|
| **10-11/ago** | **Identidade Visual do Nexus:** Nome, logo, paleta de cores (neon sobre fundo escuro sugerido). Justificar coerência com a tese de grafos/redes | Logotipo e paleta salvos em `images/` |
| **11-12/ago** | **Esqueleto do PDF:** Montar o template 16:9 com as 5 páginas (Capa+Tese, Metodologia, Backtest, Análise Crítica, Conclusão). Já preencher tese e metodologia | Template em `relatorio/` ou ferramenta de slides |
| **12-13/ago** | **Visualizações da MST:** Usar `networkx` + `matplotlib` para gerar 2 grafos lado a lado (mercado calmo vs. março/2020). Destacar em cor as 10 ações periféricas selecionadas | Pode importar `from nexus.mst import construir_mst` |
| **13-14/ago** | **Seção "Uso de IA Generativa":** Documentar concretamente como o Gemini foi usado (ideação, código, revisão, análise). Incluir exemplos reais de prompts e respostas | Peso: 15% da nota! |
| **14-15/ago** | **Integração Final:** Receber gráficos e métricas das Pessoas 1 e 2. Inserir no PDF. Enxugar texto total para < 750 palavras. Verificar anonimato | PDF pronto para revisão |

---

## Agenda Conjunta (Todo o time)

| Dia | Atividade |
|---|---|
| **14/ago (noite)** | Merge das 3 branches em `main`. Pessoa 3 recebe os últimos gráficos e números |
| **15/ago** | Revisão coletiva do PDF. Checar: anonimato total, 5 páginas exatas, < 750 palavras, gráficos legíveis |
| **16/ago** | Buffer de emergência + submissão do PDF até 23h59 |
