# `dados/brutos/` — Dados como vieram da fonte

Esta pasta guarda **exatamente o que as fontes devolveram**, sem nenhuma
transformação nossa. A regra é simples: se um número aqui está errado, o erro é
da fonte, não do nosso código. Toda limpeza, filtro e cálculo acontece na etapa
seguinte e é gravado em [`../processados/`](../processados/).

Manter essa separação é o que permite auditar o pipeline: se um resultado
estranho aparecer no backtest, dá para voltar aqui e verificar se o problema
nasceu no dado ou no tratamento.

> **Os arquivos `.parquet` não são versionados no Git** (são pesados). Para
> recriar tudo, rode os scripts 01 a 03 descritos abaixo. Os `.csv` ficam
> versionados porque são leves e registram decisões factuais do projeto.

---

## Arquivos

### `b3_carteiras.csv` — 32 KB
**Origem:** API de índices da B3 · **Gerado por:** [`scripts/01_universo.py`](../../scripts/01_universo.py)

Composição das carteiras teóricas **vigentes** (data da coleta: 06/08/2026) de
cinco índices: IBOV, IBXX, IBRA, SMLL e IGCX. Cada linha é um ativo dentro de um
índice, então um mesmo código aparece várias vezes se pertencer a vários índices.

| Coluna | Significado |
|---|---|
| `codigo` | Ticker sem sufixo (ex.: `PETR4`) |
| `empresa` | Nome curto do emissor na B3 |
| `tipo` | Espécie e segmento (ex.: `ON NM` = ordinária, Novo Mercado) |
| `participacao` | Peso do ativo no índice, em % |
| `qtd_teorica` | Quantidade teórica de ações na carteira do índice |
| `indice` | Qual índice (IBOV, IBXX, IBRA, SMLL, IGCX) |

**Limitação importante:** a B3 só expõe a carteira **do dia**. Não há histórico
de composição por esse caminho — é justamente essa ausência que nos obriga a
reconstruir o universo por liquidez (ver Parte 2.2 do plano).

---

### `universo_candidatos.csv` — 17 KB
**Origem:** união de `b3_carteiras.csv` + tabela curada de tickers históricos
**Gerado por:** [`scripts/01_universo.py`](../../scripts/01_universo.py)

Os **317 códigos** que decidimos testar: 225 vindos dos índices vigentes e 113
candidatos históricos codificados à mão em
[`src/nexus/historicos.py`](../../src/nexus/historicos.py) (empresas que
negociaram entre 2012 e 2026 e sumiram das carteiras atuais).

| Coluna | Significado |
|---|---|
| `codigo` | Ticker |
| `empresa` | Nome |
| `indices` | Índices em que aparece hoje, separados por `\|` (vazio para históricos) |
| `origem` | `indice_vigente` ou `candidato_historico` |
| `motivo_saida` | Por que saiu (deslistagem, fusão, rename, baixa liquidez) |
| `sucessor` | Ticker que herdou o histórico, quando existe |

Esta é a **hipótese** de universo. O que de fato existe está em
[`../processados/disponibilidade.csv`](../processados/disponibilidade.csv).

---

### `precos_ohlcv.parquet` — 12 MB
**Origem:** Yahoo Finance via `yfinance` · **Gerado por:** [`scripts/02_baixar_precos.py`](../../scripts/02_baixar_precos.py)

O painel principal: **3.943 datas × 244 tickers × 3 campos**, de 03/01/2011 a
05/08/2026. Colunas em dois níveis (`campo`, `ticker`).

| Campo | O que é | Para que serve |
|---|---|---|
| `Adj Close` | Fechamento **ajustado** por dividendos, JCP e desdobramentos | Base dos retornos |
| `Close` | Fechamento **bruto**, o preço que apareceu na tela no dia | Base do volume financeiro |
| `Volume` | Quantidade de ações negociadas no dia | Base do volume financeiro |

**Por que baixamos as duas versões do preço.** O download usa
`auto_adjust=False` de propósito. Retorno tem que vir do preço ajustado, senão
um desdobramento de 1:2 vira uma queda falsa de 50%. Já liquidez tem que vir do
preço bruto: em 2011 a PETR4 fechou a R$ 24, mas o ajustado de hoje mostra R$ 5
para aquele mesmo dia. Multiplicar o volume de 2011 pelo preço ajustado
subestimaria o giro real daquele pregão por um fator de quase 5. Usamos
`Close × Volume`, que é o dinheiro que de fato girou.

**As 3.943 datas incluem 68 datas espúrias** (feriados da B3 com cotação
fantasma). Elas são removidas na etapa de processamento — ver
[`../processados/README.md`](../processados/README.md).

---

### `cdi_sgs12.csv` — 193 KB
**Origem:** Banco Central do Brasil, SGS série 12 · **Gerado por:** [`scripts/03_baixar_cdi_ibov.py`](../../scripts/03_baixar_cdi_ibov.py)

Taxa CDI diária, 3.916 dias úteis de 03/01/2011 a 05/08/2026.

| Coluna | Significado |
|---|---|
| `data` | Data do dia útil |
| `cdi_dia_pct` | Taxa efetiva **do dia**, em % (ex.: `0.040132` = 0,040132% naquele dia) |
| `fator` | `1 + cdi_dia_pct/100` — fator de capitalização diário |
| `cdi_acumulado` | Produto acumulado dos fatores desde 03/01/2011 |

A série 12 já é a taxa **efetiva diária**, não uma taxa anual. Não existe
conversão de base a fazer: basta multiplicar os fatores.

**Nota técnica:** a API do SGS recusa janelas longas em séries diárias
(HTTP 406). O script fatia a requisição em blocos de 5 anos.

**No período:** acumulado de 4,34× (9,87% ao ano).

---

### `benchmarks.csv` — 142 KB
**Origem:** Yahoo Finance · **Gerado por:** [`scripts/03_baixar_cdi_ibov.py`](../../scripts/03_baixar_cdi_ibov.py)

Fechamento ajustado de duas referências de mercado.

| Coluna | O que é |
|---|---|
| `data` | Data do pregão |
| `ibov` | Índice Ibovespa (`^BVSP`) — 3.866 observações |
| `bova11` | ETF que replica o Ibovespa (`BOVA11.SA`) — 3.874 observações |

Coletamos os dois porque cumprem papéis diferentes: o **IBOV** é a referência
conceitual que a banca reconhece; o **BOVA11** é o que um investidor de verdade
conseguiria comprar, já líquido de taxa de administração. Comparar contra o
BOVA11 é a comparação honesta.

**No período:** IBOV acumulou 2,54× (6,16% a.a., vol. 23,2%); BOVA11, 2,52×
(6,12% a.a.).

---

## Como recriar esta pasta do zero

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python scripts/01_universo.py        # ~5 min  → b3_carteiras, universo_candidatos
.venv/bin/python scripts/02_baixar_precos.py   # ~10 min → precos_ohlcv.parquet
.venv/bin/python scripts/03_baixar_cdi_ibov.py # ~1 min  → cdi_sgs12, benchmarks
```

**Atenção à reprodutibilidade:** o Yahoo Finance revisa dados retroativamente e
a composição dos índices da B3 muda a cada quadrimestre. Rodar os scripts numa
data futura vai produzir arquivos ligeiramente diferentes. Os números citados
neste README e no plano referem-se à coleta de **06/08/2026**.
