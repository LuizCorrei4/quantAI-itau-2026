# Robô Nexus - Desafio Itaú Asset Quant AI 2026

Este repositório contém todo o material, documentação e código necessários para a entrega final do desafio. O objetivo do projeto é desenvolver, testar e apresentar uma estratégia quantitativa competitiva baseada em Teoria de Grafos e Finanças.

## Estrutura Atual do Repositório

- **nexus_contexto_planejamento/**: Contém o `plano_final_nexus.md`, o guia-mestre do projeto, com a tese completa, cronograma, modelagem quantitativa, estrutura de backtest e métricas.
- **contexto_geracao_ideias/**: Documentos e pesquisas iniciais, incluindo lições dos últimos vencedores e alternativas de estratégias estudadas antes de decidirmos pelo modelo Nexus.
- **documentos_desafio/**: Diretrizes oficiais e materiais de referência fornecidos para a competição.
- **GEMINI.md e CLAUDE.md**: Documentações auxiliares elaboradas para prover contexto focado para os agentes de Inteligência Artificial que auxiliam no projeto (Agy e Claude).

- **scripts/**: Pipeline de dados numerado, executável na ordem 01 → 05.
- **src/nexus/**: Módulos de apoio (configuração, carteiras da B3, tabela de tickers históricos).
- **dados/**: `brutos/` guarda o que veio das fontes sem transformação; `processados/` guarda os painéis prontos para o backtest. Os `.parquet` não são versionados — os scripts os regeneram.

## Pipeline de Dados

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/01_universo.py       # carteiras B3 + históricos → teste de disponibilidade
.venv/bin/python scripts/02_baixar_precos.py  # OHLCV via yfinance
.venv/bin/python scripts/03_baixar_cdi_ibov.py # CDI (SGS 12) + Ibovespa/BOVA11
.venv/bin/python scripts/04_montar_datasets.py # painéis limpos + universo mensal
.venv/bin/python scripts/05_validar_dados.py   # checagens e relatório de qualidade
```

### O que existe hoje em `dados/processados/`

| Arquivo | Conteúdo |
|---|---|
| `precos_ajustados.parquet` | 3.875 pregões × 244 tickers (01/2011 a 08/2026), ajustado por proventos |
| `retornos_log.parquet` | Retornos logarítmicos diários (945 mil observações) |
| `volume_financeiro.parquet` | Volume em R$ = `Close` bruto × `Volume` bruto |
| `universo_mensal.parquet` | As 80 ações mais líquidas elegíveis em cada um dos 184 rebalanceamentos |
| `cdi_diario.parquet` | CDI diário e fator acumulado (BCB SGS série 12) |
| `benchmarks.parquet` | Ibovespa e BOVA11 com retornos log |
| `metadados_tickers.csv` | Ficha por ticker: empresa, radical, histórico, liquidez, se a série encerrou |
| `disponibilidade.csv` | Registro do teste de 317 códigos no yfinance |
| `relatorio_qualidade.md` | Checagens de calendário, retornos, universo, vieses e look-ahead |

Consulte o `plano_final_nexus.md` para o cronograma e as métricas de avaliação, e o
`relatorio_qualidade.md` para as decisões metodológicas de dados já tomadas.
