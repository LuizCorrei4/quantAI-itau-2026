# Robô Nexus — Desafio Itaú Asset Quant AI 2026

Este repositório contém todo o código, documentação e artefatos necessários para a entrega do projeto **Robô Nexus** no Desafio Itaú Asset Quant AI 2026.

O objetivo do projeto é desenvolver, testar e apresentar uma estratégia quantitativa de investimento baseada em **Teoria de Grafos (Árvores Geradoras Mínimas — MST)** e **Finanças**, com foco em alocação em ações periféricas e mitigação de risco sistêmico via Filtro de Regime.

---

## 📂 Estrutura Atual do Repositório

```text
quantAI-itau-2026/
├── nexus_contexto_planejamento/
│   ├── plano_final_nexus.md      # Plano-mestre v2.0 (tese, regras de negocio, rigor estatistico)
│   └── divisao_tarefas_10_a_16.md # Gestao da sprint final e cronograma de branches por membro
├── dados/
│   ├── brutos/                   # Cotacoes e arquivos originais sem transformacao
│   ├── processados/              # Paveis limpos em .parquet (precos, retornos, universo 80)
│   └── resultados/               # Saidas auditaveis do backtest (serie de retornos, carteiras)
├── src/nexus/                    # Modulos Python reutilizaveis da estrategia
│   ├── config.py                 # Constantes centrais (janelas, universos, custos, caminhos)
│   ├── historicos.py             # Mapeamento e resolucao de deslistagens/renames na B3
│   ├── b3.py                     # Extracao de composicao historica de indices
│   ├── mst.py                    # Ledoit-Wolf, distancias Mantegna, geracao de MST e Farness
│   └── portfolio.py              # Selecao Top N, equal-weight, calculo de retorno e turnover
├── scripts/                      # Pipeline numerado executavel
│   ├── 01_universo.py            # Coleta de carteiras B3 e verificacao de disponibilidade
│   ├── 02_baixar_precos.py       # Coleta de series históricas via yfinance
│   ├── 03_baixar_cdi_ibov.py     # Download de CDI (SGS 12) e benchmarks (IBOV / BOVA11)
│   ├── 04_montar_datasets.py     # Construcao dos paineis .parquet e universo das 80 mais liquidas
│   ├── 05_validar_dados.py       # Validacao estatistica, look-ahead bias e relatorio de qualidade
│   ├── 06_avaliar_periferia.py   # Teste empírico de metricas de grafos vs. baselines (Beta/Correlacao)
│   └── 07_backtest.py            # Orquestrador do backtest MVP (2011-2026)
├── images/                       # Graficos gerados para relatorios e apresentacao
│   ├── retorno_acumulado_nexus_vs_benchmarks.png
│   ├── drawdown_nexus.png
│   └── turnover_mensal_nexus.png
├── docs/                         # Documentacao tecnica e relatorios analiticos
│   ├── decisao_metrica_periferia_MST.md # Justificativa da escolha da Farness
│   ├── relatorio_qualidade.md           # Auditoria e tratamento de vieses nos dados
│   ├── resumo_backtest_mvp.md           # Consolidação automatica de metricas do backtest MVP
│   └── resumo_descomplicado_mvp.md      # Analise conceitual, diagnostico de turnover/drawdown e guia p/ Pessoa 2
└── temp/                         # Documentos de trabalho e planejamentos temporarios
```

---

## 🛠️ Como Executar o Projeto

### 1. Preparação do Ambiente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Pipeline de Dados (Scripts 01 a 05)

```bash
python scripts/01_universo.py       # Mapeia 317 códigos de ativos na B3
python scripts/02_baixar_precos.py  # Coleta histórico de preços via yfinance
python scripts/03_baixar_cdi_ibov.py # Coleta CDI (SGS/BCB) e IBOV/BOVA11
python scripts/04_montar_datasets.py # Consolida os datasets em dados/processados/
python scripts/05_validar_dados.py   # Executa testes de integridade e viés
```

### 3. Validação de Métricas e Backtest (Scripts 06 e 07)

```bash
python scripts/06_avaliar_periferia.py # Avalia empates em Betweenness vs Farness/Closeness
python scripts/07_backtest.py          # Executa o backtest MVP completo (183 meses)
```

---

## 📊 Principais Resultados do MVP (`07_backtest.py`)

A execução da estratégia pura de periferia (**Farness**, Top 10, Equal-Weight, sem Filtro de Regime) no período de **Mai/2011 a Jul/2026** apresentou o seguinte diagnóstico:

- **Retorno Acumulado:** 122,4% (contra 318,5% do CDI e 144,9% do Ibovespa)
- **Sharpe Ratio:** **-0,21** (Riscos não compensaram a renda fixa sem proteção de crise)
- **Max Drawdown:** **-48,2%** (Perda máxima concentrada em crashes sistêmicos)
- **Turnover Médio:** **67,4% ao mês** (Giro elevado consumiu retorno via custos operacionais)

> **Diagnóstico & Próximos Passos:** Esses resultados comprovam a necessidade de acoplar o **Filtro de Regime** (Etapa 6 do plano mestre), utilizando a contração da distância média da MST como sinalizador antecipado para migrar temporariamente o portfólio para o CDI.

---

## 📑 Documentação de Referência

- **Plano Mestre:** [`nexus_contexto_planejamento/plano_final_nexus.md`](file:///home/gabyl/projetos/quantAI-itau-2026/nexus_contexto_planejamento/plano_final_nexus.md)
- **Divisão de Tarefas da Sprint:** [`nexus_contexto_planejamento/divisao_tarefas_10_a_16.md`](file:///home/gabyl/projetos/quantAI-itau-2026/nexus_contexto_planejamento/divisao_tarefas_10_a_16.md)
- **Decisão da Métrica de Periferia:** [`docs/decisao_metrica_periferia_MST.md`](file:///home/gabyl/projetos/quantAI-itau-2026/docs/decisao_metrica_periferia_MST.md)
- **Análise do MVP para a Equipe:** [`docs/resumo_descomplicado_mvp.md`](file:///home/gabyl/projetos/quantAI-itau-2026/docs/resumo_descomplicado_mvp.md)
- **Saídas do Backtest:** [`dados/resultados/README.md`](file:///home/gabyl/projetos/quantAI-itau-2026/dados/resultados/README.md)
