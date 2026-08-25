# Robo Nexus — Desafio Itau Asset Quant AI 2026

Repositorio oficial de codigo, dados auditados, documentacao tecnica e artefatos de pesquisa da estrategia quantitativa **Nexus**, desenvolvida para o Desafio Itau Asset Quant AI 2026.

---

## Reconhecimento Oficial

O projeto foi classificado no **Top 5% dos melhores trabalhos da competicao**, recebendo o **Certificado de Destaque** concedido pela Itau Asset Management.

<div align="center">
  <img src="images/certificado_destaque_top5.png" alt="Certificado de Destaque - Top 5% no Desafio Itau Asset Quant AI 2026" width="850"/>
</div>

* **Documento Oficial em PDF:** [NEXUS.pdf](NEXUS.pdf)
* **Integrantes:**
  * Arthur Filliettaz Mendes
  * Italo Carlos Martins Bresciani
  * Luiz Gabriel Correia dos Santos

---

## Resumo da Estrategia

O Robo Nexus e um sistema quantitativo sistematico de alocacao em acoes brasileiras (B3) baseado em **Teoria de Redes Complexas (Arvores Geradoras Minimas — MST)** e **Fatores Direcionais de Alpha**.

### Racional Economico
A diversificacao tradicional de Markowitz colapsa durante choques de mercado, quando as correlacoes entre acoes disparam (de $\rho \approx 0,15$ para $\approx 0,60$), propagando perdas por contagio sistemico. O Nexus mapeia a topologia da bolsa para selecionar ativos situados na **periferia da rede**, caracterizados por dinamicas idiossincraticas e baixo acoplamento com o fator comum de mercado.

Como o isolamento topologico por si so nao garante retorno (comprar ativos perifericos em tendencia de baixa destroi capital), a estrategia acopla um filtro direcional de momentum e regras estruturais de gestao de risco.

### Arquitetura em Cascata (4 Camadas Deterministicas)
1. **Topologia e Descorrelacao (Onde Olhar):** Matriz de correlacao de 63 pregoes com encolhimento de Ledoit-Wolf, distancia ultrametrica de Mantegna $d_{ij} = \sqrt{2(1-\rho_{ij})}$ e selecao do Top 20 por *Farness* (ou Menor Correlacao Media na versao V5).
2. **Filtro Direcional de Alpha (Quando Comprar):** Aprovacao condicional apenas para ativos com preco de fechamento acima da media movel simples de 150 dias ($P_t > \text{SMA}_{150}$).
3. **Gestao de Risco CVM 175 (Quanto Expor):** Alocacao uniforme com teto regulatorio de 10% por ativo ($w_i = \min(1/K, 0,10)$). O saldo remanescente recua automaticamente para o **CDI**, funcionando como amortecedor passivo de volatilidade.
4. **Filtro de Regime Topologico (Como Frear):** Monitoramento da distancia media das arestas da MST. Se a arvore contrair abaixo do percentil 10% historico (indicando estresse sistemico), a exposicao acionaria e reduzida para 30%, com 70% alocado em CDI.

---

## Principais Resultados

### 1. Backtest In-Sample (2011–2018: 91 meses)
* **CAGR:** 14,9% a.a. (vs. 10,3% do CDI e 6,2% do Ibovespa)
* **Volatilidade Anualizada:** 13,9% (vs. 23,3% do Ibovespa)
* **Sharpe Ratio Geometrico (vs. CDI):** +0,332 (vs. -0,176 do Ibovespa)
* **Sortino Ratio:** +0,551
* **Max Drawdown:** -12,3% (vs. -43,7% do Ibovespa)
* **Alpha de Jensen:** +6,1% a.a. ($\beta = 0,41$)
* **Break-Even de Custos:** 52,8 bps por perna (suporta mais de 10x o custo de mercado)

### 2. Teste Cego Out-of-Sample (2019–2026: 91 meses)
Executado com hiperparametros rigidamente congelados em `parametros_travados.json`:
* **CAGR:** 9,5% a.a. (vs. 9,4% do CDI, 9,5% do BOVA11 e 9,2% do Ibovespa)
* **Volatilidade Anualizada:** 19,5% (reducao de -2,1 p.p. via Filtro de Regime vs. 21,6% sem regime)
* **Max Drawdown:** -35,6% (vs. -40,1% do Ibovespa e -40,3% do BOVA11)
* **Taxa de Vitoria Mensal vs. CDI:** 59,3% dos meses
* **Significancia no Nulo Pareado:** **Percentil 100,0% ($p\text{-value} = 0,0\%$)** contra 200 simulacoes de controle com mesmas regras de momentum e caixa.

### 3. Falsificacao e Navalha de Occam
Modelos de Machine Learning (Random Forest / XGBoost) apresentaram Sharpe inflado de 0,481 em testes preliminares devido a *data leakage*. Quando submetidos a esteira Walk-Forward estrita (retreino em $T-1$, inferencia cega em $T$), o Sharpe colapsou para +0,053 em funcao de ruido e excesso de giro. Pela **Navalha de Occam**, o modelo de ML foi formalmente descartado em favor da regra simples de Momentum ($+0,127$), mantendo o registro negativo como criterio de integridade cientifica.

---

## Estrutura do Repositorio

Abaixo estao descritos exclusivamente os diretorios e arquivos rastreados no controle de versao:

```text
quantAI-itau-2026/
├── NEXUS.pdf                             # Certificado Oficial de Destaque (Top 5%) - Itau Asset
├── parametros_travados.json              # Registro de congelamento de parametros para o OOS
├── requirements.txt                      # Dependencias Python do projeto
├── README.md                             # Documento principal do repositorio
├── CLAUDE.md / GEMINI.md                 # Instrucoes operacionais para assistentes de IA
│
├── src/nexus/                            # Pacote modular Python da estrategia
│   ├── __init__.py
│   ├── config.py                         # Constantes operacionais, caminhos e custos
│   ├── b3.py                             # Modulo de composicao e regras da B3
│   ├── historicos.py                     # Mapeamento e resolucao de renames e deslistagens
│   ├── mst.py                            # Matriz de covariancia, Ledoit-Wolf, Mantegna e MST
│   ├── alpha_filters.py                  # Filtros direcionais de Momentum e classificadores
│   ├── portfolio.py                      # Alocacao de pesos, teto CVM 175 e calculo de retornos
│   ├── regime.py                         # Logica de deteccao de estresse sistemico via MST
│   └── motor.py                          # Motor de simulacao centralizado com hashes SHA-256
│
├── scripts/                              # Pipeline numerado e reproduzivel
│   ├── 01_universo.py                    # Mapeamento e filtragem de ativos na B3
│   ├── 02_baixar_precos.py               # Coleta de precos historicos
│   ├── 03_baixar_cdi_ibov.py             # Download de CDI (SGS 12) e benchmarks (IBOV, BOVA11)
│   ├── 04_montar_datasets.py             # Construcao e alinhamento das matrizes de dados
│   ├── 05_validar_dados.py               # Auditoria de integridade, datas fantasmas e look-ahead
│   ├── 06_avaliar_periferia.py           # Validacao da metrica de Farness vs. Betweenness
│   ├── 07_backtest.py                    # Backtest do MVP puro (topologia pura)
│   ├── 08_backtest_alpha.py              # Teste dos filtros direcionais de alpha
│   ├── 09_baseline_aleatorias.py         # Baseline de carteiras aleatorias (Monte Carlo N1)
│   ├── 10_grid_search_alpha.py           # Grid search de parametros in-sample
│   ├── 11_feature_engineering.py         # Engenharia de atributos para modelos de ML
│   ├── 12_train_ml.py                    # Treinamento e auditoria walk-forward de ML
│   ├── 13_sensibilidade_custos.py        # Analise de sensibilidade a atrito e break-even
│   ├── 14_ablacao_atribuicao.py          # Execucao das variantes de ablacao (V0 a V6)
│   ├── 14_graficos_relatorio.py          # Renderizador de graficos oficiais em alta resolucao
│   ├── 15_monte_carlo_corrigido.py       # Bateria de controle estatistico com 3 nulos (N1, N2, N3)
│   ├── 16_calibracao_regime.py           # Calibracao do percentil do filtro de regime
│   ├── 17_out_of_sample.py               # Execucao cega do teste Out-of-Sample (2019-2026)
│   ├── 18_cv_temporal.py                 # Validacao cruzada temporal expansivel
│   └── 19_graficos_auditoria.py          # Geracao de diagnosticos visuais complementares
│
├── dados/                                # Dados e resultados auditados
│   ├── CHECKSUMS.sha256                  # Hashes criptograficos para garantia de integridade
│   ├── README.md
│   ├── brutos/                           # CSVs originais de carteiras, cdi e benchmarks
│   ├── processados/                      # Metadados de tickers, disponibilidade e relatorio
│   └── resultados/                       # Parquets e CSVs de retornos, ablacao, CV e OOS
│       ├── ablacao/                      # Resultados das variantes V0 a V6 e nulo pareado
│       ├── cv_temporal/                  # Series temporais das batalhas de filtros
│       ├── out_of_sample/                # Series de retornos e carteiras do teste OOS
│       └── sensibilidade_custos_transacao.csv
│
├── docs/                                 # Documentacao tecnica e relatorios metodologicos
│   ├── 01_auditoria_dados_base.md
│   ├── 02_decisao_metrica_periferia_MST.md
│   ├── 03_resultados_backtest_mvp.md
│   ├── 04_diagnostico_mvp_e_arquitetura_cascata.md
│   ├── 05_calibracao_momentum_cv.md
│   ├── 06_teste_monte_carlo_baselines.md
│   ├── 07_limite_do_momentum_grid_search.md
│   ├── 08_batalha_dos_filtros_alpha.md
│   ├── 09_regra_cap_concentracao_cvm175.md
│   ├── 10_sensibilidade_custos_e_slippage.md
│   ├── 11_auditoria_data_leakage_e_ia_generativa.md
│   ├── 12_ablacao_e_atribuicao.md
│   ├── 13_monte_carlo_corrigido.md
│   ├── 14_out_of_sample.md
│   ├── 15_filtro_regime.md
│   └── resumo_final_completo/
│       └── arquivo_mestre.md             # Base canônica com formulas, metricas e justificativas
│
├── diretrizes_para_gerar_relatorio/      # Roteiro do relatorio final e apresentacao
│   ├── diretrizes_para_relatorio.md      # Consolidacao das regras do edital e manual
│   ├── dicas_adicionais_relatorio.md     # Boas praticas de comunicacao visual
│   └── texto_e_diagramacao_relatorio_final.md # Roteiro de storytelling e diagramacao 16:9
│
├── documentos_desafio/                   # Documentos oficiais da competicao
│   ├── edital_desafio_quant_ai_2026.md
│   ├── regulamento_desafio_quant_ai_2026.md
│   ├── Criterios_Avaliacao_Desafio.md
│   ├── diretrizes_relatorio_final.md
│   └── guia_primeiros_passos_quant_ai.md
│
├── images/                               # Graficos e diagramas oficiais
│   ├── certificado_destaque_top5.png     # Renderizacao visual do Certificado de Destaque
│   ├── 01_mvp_puro_drawdown.png a 14_out_of_sample_nulo.png # Painel canônico numerado
│   ├── relatorio/                        # Imagens formatadas para o relatorio final
│   └── Identidade visual Nexus(1)/       # Templates HTML e assets da identidade visual
│
├── modelos/
│   └── alpha_ml_vencedor.joblib          # Modelo serializado de ML (registro de Occam)
│
└── notebooks/
    └── nexus_resultados.ipynb            # Notebook interativo para analise de resultados
```

---

## Como Reproduzir o Projeto

### 1. Instalacao do Ambiente

Recomenda-se o uso de Python 3.10 ou superior:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Execucao do Pipeline Completo

O pipeline e sequencial e deterministico:

```bash
# 1. Coleta e Preparacao de Dados
python scripts/01_universo.py
python scripts/02_baixar_precos.py
python scripts/03_baixar_cdi_ibov.py
python scripts/04_montar_datasets.py
python scripts/05_validar_dados.py

# 2. Avaliacao de Hipoteses e Filtros In-Sample
python scripts/06_avaliar_periferia.py
python scripts/07_backtest.py
python scripts/08_backtest_alpha.py
python scripts/09_baseline_aleatorias.py
python scripts/10_grid_search_alpha.py
python scripts/11_feature_engineering.py
python scripts/12_train_ml.py
python scripts/13_sensibilidade_custos.py

# 3. Ablacao, Monte Carlo e Calibracao de Regime
python scripts/14_ablacao_atribuicao.py
python scripts/15_monte_carlo_corrigido.py
python scripts/16_calibracao_regime.py
python scripts/18_cv_temporal.py

# 4. Execucao Cega Out-of-Sample
python scripts/17_out_of_sample.py

# 5. Geracao de Figuras e Graficos
python scripts/14_graficos_relatorio.py
python scripts/19_graficos_auditoria.py
```

### 3. Verificacao de Integridade

Para verificar se os arquivos gerados correspondem aos dados auditados:

```bash
sha256sum -c dados/CHECKSUMS.sha256
```

---

## Auditoria de Dados e Mitigacao de Vieses

A esteira de dados foi submetida a controles estritos para eliminar distorcoes econometricas:

* **Zero Look-Ahead Bias:** Todas as decisoes de alocacao no primeiro dia util do mes $T$ utilizam exclusivamente dados observados ate $T-1$.
* **Mitigacao de Survivorship Bias:** O universo e recalculado mes a mes com os 80 ativos mais liquidos no periodo anterior (157 tickers distintos ao longo do historico). Empresas falidas ou deslistadas com negociacao historica foram preservadas na base.
* **Expurgo de Cotacoes Fantasmas:** 68 registros espurios reportados em feriados ou finais de semana pelo yfinance foram expurgados contra o calendario oficial da B3.
* **Volume por Preco Bruto:** O filtro de liquidez utiliza o volume financeiro mediano calculado com precos brutos (`Close`), evitando distorcoes retroativas de splits e grupamentos. O calculo de retorno utiliza precos ajustados por proventos (`Adj Close`).
* **Custos Transacionais Realistas:** Todas as simulacoes incorporam 10 bps por giro completo (5 bps por perna) cobrados sobre o turnover da carteira.
