# `dados/processados/` — Datasets prontos para o backtest

Esta pasta contém o resultado do tratamento aplicado sobre
[`../brutos/`](../brutos/). É daqui que o backtest lê — nenhum script de
estratégia deve tocar em `brutos/` diretamente.

Tudo aqui é gerado por [`scripts/04_montar_datasets.py`](../../scripts/04_montar_datasets.py)
e validado por [`scripts/05_validar_dados.py`](../../scripts/05_validar_dados.py).

> **Os `.parquet` não são versionados** (17 MB). Os `.csv` e o
> `relatorio_qualidade.md` ficam no Git porque registram decisões e evidências
> do projeto, não apenas dados.

---

## O que foi feito entre `brutos/` e aqui

Quatro tratamentos, nesta ordem. Cada um está justificado em detalhe na
Parte 2.2 do [plano](../../nexus_contexto_planejamento/plano_final_nexus.md).

1. **Calendário de pregão reconstruído.** Das 3.943 datas brutas, 68 eram
   feriados da B3 em que o Yahoo publicava cotação para 1 a 5 tickers apenas
   (cotação fantasma). Ficaram **3.875 pregões**.
2. **Retornos do preço ajustado, liquidez do preço bruto.** Separação
   deliberada — misturar os dois distorce a medida de liquidez do passado.
3. **Retornos absurdos anulados.** 74 retornos diários acima de |60%| viraram
   ausência (erro de ajuste, não evento de mercado).
4. **Uma classe de ação por empresa.** PETR3/PETR4, ITUB3/ITUB4 e units
   colapsam no radical de 4 letras, ficando a classe mais líquida.

---

## Arquivos

### `precos_ajustados.parquet` — 4,0 MB
Painel **3.875 pregões × 244 tickers** de preços de fechamento ajustados por
proventos e desdobramentos. Índice = data, colunas = ticker.

Valores ausentes (`NaN`) significam "não negociou" ou "empresa ainda não
existia / já saiu da bolsa". **Não são preenchidos por interpolação** — inventar
preço criaria correlação artificial e é exatamente o tipo de erro que a MST
amplificaria.

Usado em: cálculo de retornos, elegibilidade do universo, apuração de resultado
do backtest.

---

### `retornos_log.parquet` — 6,4 MB
Retornos logarítmicos diários, $r_i(d) = \ln(P_i(d) / P_i(d-1))$, no mesmo
formato do painel de preços. **945.500 observações válidas.**

Estatísticas: média −0,00009 · desvio padrão 0,0305 · assimetria 0,11 ·
curtose 24,8. A curtose alta é a cauda gorda esperada em retornos diários de
ações, não sinal de erro.

Usado em: matriz de correlação da janela de 63 dias (entrada da MST).

---

### `volume_financeiro.parquet` — 6,6 MB
Volume negociado em **reais**, calculado como `Close` bruto × `Volume` bruto.
Mesmo formato de painel. Mediana global: R$ 7,6 milhões por ativo por dia.

Usado em: ranking de liquidez que define o universo elegível de cada mês.

---

### `universo_mensal.parquet` — 175 KB
**O dataset mais importante do projeto.** Define quais ações o robô pode
comprar em cada rebalanceamento. **184 rebalanceamentos** (02/05/2011 a
03/08/2026), sempre **exatamente 80 ações**.

| Coluna | Significado |
|---|---|
| `data_rebalanceamento` | Primeiro pregão do mês |
| `ticker` | Ação elegível |
| `grupo` | Radical de 4 letras da empresa (`PETR4` → `PETR`) |
| `rank_liquidez` | Posição no ranking, 1 = mais líquida |
| `liquidez` | Mediana do volume financeiro diário na janela, em R$ |

**Como é construído (e por que não há look-ahead):** para o rebalanceamento na
data `t`, o script pega os 63 pregões com índice **estritamente menor que `t`**,
calcula a mediana do volume financeiro de cada ação nessa janela, exige
cobertura de preço ≥ 90% e negociação em pelo menos um dos 5 últimos dias, e
fica com as 80 mais líquidas após deduplicar por empresa. Nenhum dado de `t` ou
posterior participa da decisão de `t`.

**Estabilidade:** o universo troca em média 1,7 ações por mês (2,2%), com
máximo de 5. Ao longo dos 15 anos passaram 157 tickers distintos.

---

### `cdi_diario.parquet` — 82 KB
CDI diário com retorno log já calculado. Índice = data.

| Coluna | Significado |
|---|---|
| `cdi_dia_pct` | Taxa efetiva do dia, em % |
| `fator` | `1 + cdi_dia_pct/100` |
| `cdi_acumulado` | Produto acumulado desde 03/01/2011 |
| `ret_log_cdi` | `ln(fator)` — aditivo, comparável aos retornos das ações |

Usado em: taxa livre de risco do Sharpe, remuneração do caixa quando o filtro de
regime corta exposição, e **benchmark principal da estratégia**.

---

### `benchmarks.parquet` — 157 KB
Ibovespa e BOVA11 com seus retornos log. Índice = data.

| Coluna | Significado |
|---|---|
| `ibov` / `bova11` | Fechamento ajustado |
| `ret_ibov` / `ret_bova11` | Retorno logarítmico diário |

---

### `metadados_tickers.csv` — 23 KB
Ficha de cada um dos 244 tickers do painel. É onde se consulta "o que é esse
código e o que aconteceu com ele".

| Coluna | Significado |
|---|---|
| `ticker`, `grupo`, `empresa` | Identificação |
| `n_obs`, `inicio`, `fim` | Cobertura da série |
| `liquidez_mediana` | Volume financeiro mediano de toda a série |
| `origem` | `indice_vigente` ou `candidato_historico` |
| `motivo_saida`, `sucessor` | História do ticker, quando aplicável |
| `meses_no_universo` | Em quantos dos 184 rebalanceamentos foi elegível |
| `serie_encerrada` | `True` se a série termina antes do último pregão — ou seja, **empresa que morreu** |

A coluna `serie_encerrada` é a evidência direta contra o survivorship bias.

---

### `disponibilidade.csv` — 26 KB
Registro do teste dos 317 candidatos no Yahoo Finance. **É a prova documental**
da nossa discussão de viés de sobrevivência — não uma afirmação, um resultado
verificável.

| Coluna | Significado |
|---|---|
| `codigo`, `empresa`, `indices` | Identificação |
| `origem` | De onde veio o candidato |
| `motivo_saida`, `sucessor` | História do ticker |
| `n_obs`, `inicio`, `fim` | O que o Yahoo devolveu |
| `disponivel` | `True` se retornou ao menos 120 observações |

**Resultado:** 244 disponíveis de 317. Todos os 225 de índices vigentes, e
19 dos 92 candidatos históricos.

---

### `relatorio_qualidade.md` — 3,6 KB
Relatório em markdown gerado automaticamente por
[`scripts/05_validar_dados.py`](../../scripts/05_validar_dados.py), com seis
seções: calendário, retornos, universo, survivorship bias, benchmarks e
checagem de look-ahead. **É o insumo direto da seção de tratamento de vieses do
relatório final.**

Rodar o script de novo regenera o arquivo com os números atualizados.

---

## Qual dataset entra em qual etapa do modelo

| Etapa do pipeline Nexus | Lê | Produz |
|---|---|---|
| 1. Universo elegível do mês | `universo_mensal.parquet` | 80 tickers |
| 2. Janela de retornos | `retornos_log.parquet` (63 dias antes de `t`) | matriz 63 × 80 |
| 3. Correlação com shrinkage | matriz da etapa 2 | matriz 80 × 80 |
| 4. Distância e MST | matriz da etapa 3 | árvore com 79 arestas |
| 5. Centralidade e ranking | árvore da etapa 4 | ranking de periferia |
| 6. Seleção e pesos | ranking da etapa 5 | carteira de 10 ações |
| 7. Filtro de regime | distância média da MST (etapa 4) | exposição de 0 a 100% |
| 8. Apuração do mês | `precos_ajustados.parquet`, `cdi_diario.parquet` | retorno da carteira |
| 9. Comparação | `benchmarks.parquet`, `cdi_diario.parquet` | métricas vs. IBOV e CDI |

---

## Como recriar esta pasta

```bash
# Requer dados/brutos/ já populado (ver ../brutos/README.md)
.venv/bin/python scripts/04_montar_datasets.py  # ~30 s
.venv/bin/python scripts/05_validar_dados.py    # ~20 s
```

Os parâmetros (tamanho do universo, janela de liquidez, cobertura mínima) ficam
em [`src/nexus/config.py`](../../src/nexus/config.py).
