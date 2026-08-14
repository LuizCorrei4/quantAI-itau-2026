# Plano Final — Robô Nexus
## Grafo de Correlação Dinâmica e Centralidade de Rede para Seleção de Portfólio
### Desafio Quant AI Itaú Asset 2026

> **Status:** Versão 4.0 — Veredito de Occam, CVM 175 e Integração Final (14/ago/2026). Este documento é o guia-mestre do projeto.
> **Deadline oficial (edital):** 17/ago/2026. **Meta interna da equipe:** 16/ago, deixando o dia 17 como buffer.

### Changelog (Versão 4.0) — Veredito de Occam, CVM 175 e Foco no In-Sample
Esta versão documenta as escolhas rigorosas que ditarão a configuração final de entrega do projeto e nossa postura em relação aos dados OOS.

- **Machine Learning Preditivo Descartado:** Aplicamos a Navalha de Occam. Após corrigirmos o *Data Leakage* no modelo de ML implementando uma esteira rigorosa de *Walk-Forward*, o sinal de ML destruiu o alpha (Sharpe 0.053). O filtro de Momentum Puro com Média Móvel de 150 dias (Sharpe In-Sample 0.122) sagrou-se o Filtro Direcional oficial. 
- **Enquadramento CVM 175 (Regra do CAP):** O portfólio agora obedece estritamente a regulação com um limite máximo de 10% de exposição por ativo, gerando realocação do excedente em CDI.
- **Último Passo (Filtro de Regime Topológico):** O filtro de regime ainda precisa ser testado para avaliar sua posição na arquitetura: ele protegerá a carteira **ANTES** ou **DEPOIS** do Filtro de Momentum? Isso exigirá testes exaustivos na base *In-Sample*.
- **Pacto de Integridade do Out-of-Sample:** Para garantirmos zero vazamento de dados, estamos absolutamente **proibidos** de testar qualquer coisa na base Out-Of-Sample (2019-2026) até estarmos completamente certos da arquitetura final pelo In-Sample. O acesso aos dados de Teste ocorrerá apenas no sábado/domingo como validação final cega.

### Changelog (Versão 3.0) — Arquitetura em Cascata com Filtros de Alpha
Esta versão reformula o papel da MST no pipeline: de seletor final de compra para **filtro de universo descorrelacionado**. Sobre esse pool periférico selecionado, Filtros de Alpha (como Momentum) determinam a convicção direcional reduzindo substancialmente o turnover excessivo da topologia pura.

### Changelog (Versão 2.0) — Revisão pós-coleta de dados
Esta versão deixa de ser um plano hipotético sobre dados e passa a descrever **dados que existem**. Mudanças materiais:

- **Survivorship bias reformulado.** A premissa da v1.2/v1.3 ("só conseguimos sobreviventes") estava **pessimista demais** e foi corrigida por teste empírico de 317 tickers. Renomeações não são buraco de dados; 6 empresas mortas entram efetivamente no backtest; os 26 buracos remanescentes estão nomeados um a um. Ver Parte 2.2.
- **Quatro decisões de tratamento de dados** agora documentadas e justificadas: preço ajustado × preço bruto, deduplicação por empresa, calendário de pregão reconstruído e anulação de retornos absurdos. Ver Parte 2.2.
- **Benchmark principal trocado de IBOV para CDI.** Nos dados reais, o CDI rendeu 9,87% a.a. contra 6,16% a.a. do Ibovespa em 15,6 anos. Bater o Ibovespa não prova quase nada; bater o CDI é a régua honesta. Ver Parte 3.2.
- **Betweenness Centrality tem um problema estrutural confirmado empiricamente:** 35 a 48 das 80 ações empatam em centralidade exatamente zero todo mês. A escolha do "Top 10 periférico" seria um sorteio. Parte 2.5 reescrita com a agenda de métricas alternativas.
- **Rastreabilidade de dados:** cada etapa do modelo agora aponta para o arquivo específico em `dados/` que ela consome, com instruções de como regerar tudo do zero.
- **Período do backtest corrigido:** dados desde 01/2011 permitem começar em 05/2011, não em 03/2013. Ganhamos ~2 anos de amostra.

### Changelog (Versão 1.3)
- Correção de tickers (SOUZ3 → CRUZ3) e clarificação entre deslistagem real e ticker renomeado.
- Filtro de Regime: percentil escolhido no in-sample e fixado no out-of-sample.
- Matriz de Correlação: detalhada a implementação do Ledoit-Wolf e o risco de compressão do sinal.

### Changelog (Versão 1.2)
- Cronograma reestruturado com MVP mínimo e relatório em paralelo.
- Filtro de Regime com percentil histórico móvel para evitar overfitting.
- Inclusão do estimador Ledoit-Wolf (shrinkage).

---

## Parte 0: Glossário para a Equipe

Vocês são cientistas de dados — os paralelos com ML/estatística estão marcados ao longo do texto.

### 0.1 Vocabulário básico de bolsa

Estes quatro termos aparecem o tempo todo a partir da Parte 2 e precisam estar claros antes.

**Pregão.** É um *dia de funcionamento da bolsa*. A B3 abre por volta das 10h e fecha às 17h30, de segunda a sexta, exceto feriados nacionais e alguns feriados específicos do mercado financeiro (Carnaval, Corpus Christi, 24 e 31 de dezembro). "63 dias úteis" na verdade quer dizer "63 pregões" — e não são a mesma coisa que 63 dias de calendário nem exatamente os dias úteis do calendário civil, porque a B3 tem seu próprio conjunto de feriados. Num ano típico há cerca de 246 a 252 pregões.

*Por que isso importa para nós:* toda a estratégia é calibrada em contagem de pregões. Se o nosso calendário de pregões estiver errado, a janela de 63 dias pega o período errado.

**Ticker.** É o *código curto* que identifica uma ação na bolsa. Na B3 o padrão são 4 letras identificando a empresa mais um número identificando a espécie da ação:

| Ticker | Leitura |
|---|---|
| `PETR4` | Petrobras (`PETR`), ação preferencial (`4`) |
| `PETR3` | Petrobras, ação ordinária (`3`) |
| `ITUB4` | Itaú Unibanco, preferencial |
| `KLBN11` | Klabin, *unit* (`11`) — pacote que junta ordinárias e preferenciais |

O sufixo `.SA` (de *São Paulo*) é acrescentado só para consultar o Yahoo Finance: `PETR4.SA`. Nos nossos arquivos guardamos sem o sufixo.

Duas consequências práticas: (a) uma mesma empresa pode ter **vários tickers** negociando ao mesmo tempo, e (b) o ticker pode **mudar** sem a empresa mudar — quando a Kroton virou Cogna, `KROT3` virou `COGN3`. Ambas as coisas nos causam problema, tratado na Parte 2.2.

**Cotação fantasma.** É um preço que aparece na base de dados para um dia em que **aquele mercado não funcionou**. Não é um preço errado — é um preço que não deveria existir. No nosso caso, o Yahoo Finance publica cotação em feriados da B3 (12 de outubro, 20 de novembro, Carnaval, 24 de dezembro...) para um punhado de tickers, provavelmente por replicar preço de fechamento anterior ou por captar negócios de listagens estrangeiras da mesma empresa. Encontramos **68 dessas datas** nos nossos dados, cada uma com apenas 1 a 5 tickers cotados, contra ~173 num pregão de verdade. Por que isso é destrutivo está explicado na Parte 2.2.4.

**Analogia para Data Science:** é um registro corrompido que passa na validação de tipo (é um float válido, numa data válida) mas viola uma regra de negócio que ninguém codificou. Só aparece quando você olha a distribuição de completude por linha.

**Volume financeiro.** Quanto **dinheiro** girou numa ação num dia, em reais. Não confundir com *volume* puro, que é a quantidade de ações negociadas. Volume financeiro = preço × quantidade. É a medida certa de liquidez: 1 milhão de ações de R$ 2 (R$ 2 milhões) é muito menos líquido que 100 mil ações de R$ 100 (R$ 10 milhões).

### 0.2 O que é "diversificação é a única free lunch"?

Em economia, **"free lunch"** vem da ideia de que **não existe ganho sem risco**. Se alguém te oferece retorno alto sem risco, provavelmente é golpe. Isso é formalizado como *Hipótese de Mercado Eficiente*.

A **única exceção reconhecida** é a **diversificação**. Harry Markowitz (Nobel de 1990) demonstrou que, ao combinar ativos que não se movem perfeitamente juntos (correlação < 1), é possível **reduzir o risco total da carteira sem reduzir o retorno esperado**. Você ganha (menos risco) sem pagar nada.

**Analogia para Data Science:** é um ensemble tipo Random Forest. Cada árvore é ruidosa, mas combinando muitas árvores *diferentes entre si* (descorrelacionadas), o ensemble tem menos variância sem perder acurácia.

**O problema:** a diversificação só funciona se os ativos forem genuinamente descorrelacionados. Em crises quase tudo cai junto e a diversificação desaparece exatamente quando você mais precisa dela. **É esse problema que o Nexus tenta resolver.**

### 0.3 O que é "exposição idiossincrática"?

O retorno de uma ação se decompõe em duas partes:

1. **Risco sistêmico (de mercado):** a parte causada pelo mercado como um todo. Quando o Ibovespa sobe 2%, quase todas as ações sobem um pouco. **Não dá para eliminar** via diversificação.
2. **Risco idiossincrático (específico):** a parte exclusiva daquela empresa. A Petrobras cai 5% num dia por um problema de gestão enquanto o Ibovespa fica estável — esses −5% são idiossincráticos.

**Exposição idiossincrática** significa que a carteira é dominada por fatores específicos de cada empresa. Se uma ação cai por motivo próprio, as outras não caem junto.

### 0.4 O que é Sharpe Ratio?

```
Sharpe = (Retorno da carteira − Retorno do CDI) / Volatilidade da carteira
```

- **Numerador:** quanto a carteira rendeu *acima* da taxa livre de risco. Carteira 15%, CDI 10% → excesso de 5%.
- **Denominador:** desvio padrão dos retornos.

**Sharpe alto = muito retorno por unidade de risco.** Um detalhe que vira central neste projeto: se a carteira render menos que o CDI, o Sharpe é **negativo**. Como veremos na Parte 3.2, o Ibovespa teve Sharpe negativo nos últimos 15 anos.

### 0.5 Preço ajustado × preço bruto

Duas versões do mesmo preço histórico, e usar a errada estraga o resultado.

**Preço bruto (`Close`):** o número que apareceu na tela naquele dia. Em 04/01/2011 a PETR4 fechou a R$ 27,71. Foi isso que o investidor viu.

**Preço ajustado (`Adj Close`):** o preço histórico recalculado para trás, descontando dividendos pagos e desdobramentos. A mesma PETR4 de 04/01/2011 aparece hoje como R$ 5,13.

Por que a diferença é tão grande? Porque em 15 anos a empresa pagou muito dividendo, e cada pagamento reduz proporcionalmente o preço histórico ajustado.

**Regra prática:**

| Para calcular | Use | Se usar o outro |
|---|---|---|
| Retorno | Ajustado | Um desdobramento de 1:2 vira uma queda falsa de 50% |
| Volume financeiro / liquidez | Bruto | Subestima o giro do passado por um fator de até 5× |

### 0.6 Outros termos

| Termo | O que é | Analogia em Data Science |
|---|---|---|
| **Backtest** | Simular a estratégia no passado | Avaliar o modelo em holdout |
| **Look-ahead bias** | Usar dado do futuro numa decisão do passado | Data leakage |
| **Survivorship bias** | Testar só com ações que existem hoje | Treinar só nos dados que sobreviveram à limpeza |
| **Drawdown** | Maior queda pico-a-vale | Pior perda consecutiva |
| **Benchmark** | Referência de comparação | Baseline model |
| **Alfa** | Retorno acima do benchmark | Melhoria vs. baseline |
| **Turnover** | % da carteira que muda por rebalanceamento | Taxa de atualização do modelo |
| **CDI** | Taxa de juros de referência (≈ Selic); retorno "sem risco" | Null model |
| **In-sample / Out-of-sample** | Período de calibração / período de teste cego | Treino / teste |

---

## Parte 1: A Tese

### 1.1 Hipótese Central

> **"A estrutura de correlação entre ações muda ao longo do tempo. Ações que ocupam posições periféricas na rede de correlação oferecem diversificação genuína e, portanto, uma carteira composta por essas ações tende a ter melhor retorno ajustado ao risco do que o índice de mercado."**

**Ajuste de ambição na v2.0.** Escrita assim, a hipótese é fraca demais para o mercado brasileiro: bater o Ibovespa em retorno ajustado ao risco é um alvo baixo, porque o Ibovespa teve Sharpe negativo nos últimos 15 anos. A hipótese que vamos de fato testar é mais dura:

> **A carteira periférica entrega Sharpe positivo — isto é, supera o CDI ajustado ao risco — e não apenas supera o Ibovespa.**

Ver Parte 3.2 para os números que motivam essa mudança.

### 1.2 Sustentação Acadêmica

Três pilares documentados.

#### Pilar 1: Correlações não são estáveis (e sobem em crises)

**"Increased Correlation in Bear Markets"** (Longin & Solnik, 2001, *Journal of Finance*) demonstrou estatisticamente que as correlações entre mercados acionários aumentam em períodos de queda, com 30 anos de dados. Quando o mercado cai, quase tudo cai junto.

- **Forbes & Rigobon (2002):** parte do aumento em crises é real, não artefato estatístico.
- **Ang & Chen (2002):** correlações são assimétricas — sobem mais na baixa do que caem na alta.

**Confirmação nos nossos próprios dados:** a correlação média entre as 80 ações do universo fica entre 0,10 e 0,22 em períodos normais e saltou para **0,595 em maio de 2020**. O fenômeno que a literatura descreve está presente e é forte na nossa amostra.

#### Pilar 2: Redes de correlação em mercados financeiros

**Mantegna (1999)**, em *"Hierarchical Structure in Financial Markets"*, propôs usar a Minimum Spanning Tree para filtrar a matriz de correlação e revelar a estrutura hierárquica do mercado.

- **Onnela et al. (2003):** a MST se contrai em crashes e se expande em mercados calmos.
- **Bonanno et al. (2004):** métricas de centralidade identificam ações sistemicamente importantes.
- **Tumminello et al. (2005):** *Planar Maximally Filtered Graph* (PMFG) como alternativa à MST, retendo mais informação.

#### Pilar 3: Ações periféricas oferecem diversificação real

- **Peralta & Zareei (2016):** portfólios de ações com baixa centralidade têm menor risco sistêmico e melhor Sharpe em médio prazo.
- **Pozzi et al. (2013):** a posição na MST prediz a contribuição da ação ao risco sistêmico do portfólio.

**Ressalva honesta:** esses trabalhos usam mercados desenvolvidos e universos maiores. Não há garantia de que o efeito exista na B3 com 80 ações. Essa é a razão de ser do backtest, e um resultado nulo bem documentado é uma entrega legítima.

### 1.3 Por Que Esta Tese É Competitiva

| Critério | Como o Nexus atende |
|---|---|
| **Conceito (20%)** | Hipótese testável com 3 pilares acadêmicos. Arquitetura em cascata (topologia + momentum + regime) é original e modular. |
| **Originalidade** | Teoria de Grafos + Finanças, mesma família do vencedor de 2024 (TDA). Diferencial: combina MST com filtros preditivos. |
| **Modelagem (20%)** | Pipeline 100% sistemático e reprodutível, do download ao peso da carteira. Cada camada tem papel claro e testável isoladamente. |
| **Backtest (15%)** | Vieses tratados com evidência, não com declaração. In-sample/out-of-sample rigoroso. Ver Parte 2.2 e 3.4. |
| **Análise (15%)** | Teste de contribuição marginal: cada filtro (MST, Momentum, Regime) é avaliado isoladamente e em combinação. |
| **Visual** | Diagrama de cascata + grafos MST são extremamente visuais — perfeitos para 5 páginas. |

---

## Parte 2: O Modelo Quantitativo

### 2.1 Visão Geral do Pipeline

```
[Preços Diários] → [Retornos Log] → [Matriz de Correlação] → [Matriz de Distância]
       ↓
[Minimum Spanning Tree (MST)] → [Métrica de Periferia (Farness)] → [Ranking de Ações]
       ↓
[Pool Periférico: Top N Candidatas]  ← "Filtro de Universo Descorrelacionado"
       ↓
[Filtros de Alpha]  ← NOVA CAMADA (v3.0)
  ├─ Momentum: Preço > SMA(L)  
  └─ ML (opcional): Classificador prevê retorno(+K dias) > 0
       ↓
[Ações Aprovadas] → [Alocação Equal-Weight entre aprovadas, resto em CDI]
       ↓
[Filtro de Regime] → [Ajuste de Exposição: Ações ↔ CDI] → [Backtest]
```

### 2.2 Etapa 1: Dados — O Que Temos e Como Foi Construído

> **Status: CONCLUÍDO em 06/08/2026.** Esta seção descreve dados que existem em `dados/`, não um plano.

#### 2.2.0 Como obter os dados do zero

Nada em `dados/` precisa ser baixado manualmente. O pipeline inteiro é reproduzível:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python scripts/01_universo.py         # ~5 min  — carteiras B3 + teste de 317 tickers
.venv/bin/python scripts/02_baixar_precos.py    # ~10 min — OHLCV de 244 tickers via yfinance
.venv/bin/python scripts/03_baixar_cdi_ibov.py  # ~1 min  — CDI (BCB) + Ibovespa/BOVA11
.venv/bin/python scripts/04_montar_datasets.py  # ~30 s   — painéis limpos + universo mensal
.venv/bin/python scripts/05_validar_dados.py    # ~20 s   — checagens + relatório de qualidade
```

Os arquivos `.parquet` **não estão no Git** (17 MB); os scripts os regeneram. Os `.csv` e o `relatorio_qualidade.md` estão versionados porque registram decisões e evidências.

**Alerta de reprodutibilidade:** o Yahoo revisa dados retroativamente e as carteiras da B3 mudam a cada quadrimestre. Rodar numa data futura produz arquivos ligeiramente diferentes. Todos os números deste plano são da coleta de **06/08/2026**.

**Fontes:**

| Dado | Fonte | Acesso |
|---|---|---|
| Composição vigente de IBOV, IBXX, IBRA, SMLL, IGCX | API de índices da B3 | Gratuito, sem chave |
| Preços ajustados, preços brutos e volume | Yahoo Finance via `yfinance` | Gratuito |
| CDI diário | Banco Central, SGS série 12 | Gratuito, sem chave |
| Ibovespa e BOVA11 | Yahoo Finance | Gratuito |

#### 2.2.1 O que existe hoje

| Arquivo | Conteúdo |
|---|---|
| [`dados/processados/precos_ajustados.parquet`](../dados/processados/) | 3.875 pregões × 244 tickers, 03/01/2011 a 05/08/2026 |
| [`dados/processados/retornos_log.parquet`](../dados/processados/) | 945.500 retornos logarítmicos diários |
| [`dados/processados/volume_financeiro.parquet`](../dados/processados/) | Volume em R$ (mediana global R$ 7,6 mi/dia por ativo) |
| [`dados/processados/universo_mensal.parquet`](../dados/processados/) | 184 rebalanceamentos × 80 ações elegíveis |
| [`dados/processados/cdi_diario.parquet`](../dados/processados/) | CDI diário, fator e acumulado |
| [`dados/processados/benchmarks.parquet`](../dados/processados/) | Ibovespa e BOVA11 com retornos log |
| [`dados/processados/metadados_tickers.csv`](../dados/processados/) | Ficha dos 244 tickers |
| [`dados/processados/disponibilidade.csv`](../dados/processados/) | Resultado do teste dos 317 candidatos |
| [`dados/processados/relatorio_qualidade.md`](../dados/processados/) | Checagens automatizadas |

Descrição campo a campo em [`dados/brutos/README.md`](../dados/brutos/README.md) e [`dados/processados/README.md`](../dados/processados/README.md).

#### 2.2.2 Decisão 1 — Preço ajustado para retorno, preço bruto para liquidez

> Esta seção é explicada do zero, sem pressupor conhecimento de finanças.

##### O ponto de partida: existem dois preços para o mesmo dia

Quando pedimos ao Yahoo Finance o histórico da Petrobras, ele devolve **dois números diferentes para o mesmo pregão**. Para 04/01/2011:

| | Valor | O que é |
|---|---|---|
| **Preço bruto** (`Close`) | **R$ 26,90** | O número que apareceu na tela naquele dia. Quem comprou PETR4 em 04/01/2011 pagou R$ 26,90 por ação. |
| **Preço ajustado** (`Adj Close`) | **R$ 5,88** | O mesmo dia, mas *recalculado hoje*, em 2026. |

Não é erro. São duas coisas diferentes, e a confusão entre elas é a origem do problema.

##### Por que o preço ajustado existe

Uma ação não rende só pela variação de preço. Ao longo dos anos a empresa faz duas coisas que **mudam o preço sem que ninguém tenha ganhado ou perdido dinheiro**:

**1. Pagar dividendo.** A empresa distribui parte do lucro aos acionistas. Suponha uma ação a R$ 100 que paga R$ 5 de dividendo. No dia seguinte ela abre valendo R$ 95 — porque aqueles R$ 5 saíram do caixa da empresa e foram para o bolso do acionista.

Olhando só o preço, parece uma queda de 5%. Mas o investidor **não perdeu nada**: ele tem R$ 95 em ação mais R$ 5 em dinheiro. O patrimônio dele continua R$ 100.

**2. Desdobrar a ação (*split*).** A empresa transforma cada ação em duas, para baratear o preço unitário e facilitar a negociação. Uma ação de R$ 100 vira duas de R$ 50.

Olhando só o preço, parece uma **queda de 50%**. Mas quem tinha 1 ação de R$ 100 agora tem 2 de R$ 50. Continua com R$ 100.

O **preço ajustado** conserta isso. Ele reescreve todo o passado como se os dividendos tivessem sido reinvestidos e os desdobramentos nunca tivessem acontecido. É por isso que a PETR4 de 2011 aparece como R$ 5,88 e não R$ 26,90: em 15 anos a Petrobras pagou muito dividendo, e cada pagamento empurra o preço histórico ajustado um pouco mais para baixo.

##### Uso 1: para calcular RETORNO, o ajustado é obrigatório

Retorno é "quanto o investidor ganhou". Se usarmos preço bruto, um desdobramento aparece como −50% num único dia.

Isso não é só um número feio na planilha. Lembre o que o Nexus faz: ele mede **correlação** entre ações, ou seja, se elas sobem e descem juntas. Um −50% falso é um evento gigantesco na série. Se duas empresas desdobrarem ações no mesmo mês, o modelo veria as duas despencando juntas e concluiria que **são fortemente correlacionadas** — quando na verdade não aconteceu absolutamente nada no mercado. A MST ligaria as duas com uma aresta curtíssima, e a rede inteira sairia distorcida.

**Por isso o retorno vem do preço ajustado.**

##### Uso 2: para medir LIQUIDEZ, o bruto é obrigatório

Aqui a lógica se inverte, e é essa parte que costuma confundir.

**Liquidez** é o quanto uma ação é fácil de comprar e vender. A medida usual é o **volume financeiro**: quanto *dinheiro* trocou de mãos naquele dia. É o que define quais 80 ações entram no nosso universo (Parte 2.2.6).

Volume financeiro = preço × quantidade de ações negociadas. E a pergunta é: **qual preço?**

Em 04/01/2011 a PETR4 negociou 30.936.600 ações:

| Conta | Resultado |
|---|---|
| **Bruto:** R$ 26,90 × 30.936.600 | **R$ 832 milhões** ← o dinheiro que de fato girou |
| **Ajustado:** R$ 5,88 × 30.936.600 | R$ 182 milhões ← número que nunca existiu |

Naquele dia, R$ 832 milhões realmente mudaram de mãos na PETR4. Esse é o fato histórico. Os R$ 182 milhões são uma ficção: resultam de multiplicar uma quantidade real de 2011 por um preço que só passou a existir em 2026, depois de 15 anos de ajustes.

**A regra em uma frase:** o preço ajustado responde "quanto o investidor ganhou"; o preço bruto responde "quanto dinheiro girou". Liquidez é sobre dinheiro que girou.

##### Por que o erro seria pior do que um simples "número menor"

Se o preço ajustado apenas dividisse tudo pelo mesmo fator, não haveria problema — o **ranking** de liquidez continuaria igual, e o ranking é tudo que usamos. Se toda ação encolhesse 4,57×, a mais líquida continuaria sendo a mais líquida.

**Mas o fator é diferente para cada ação**, porque cada empresa pagou uma quantidade diferente de dividendos e fez desdobramentos diferentes. No mesmo 04/01/2011:

| Ação | Preço bruto | Preço ajustado | Fator de distorção |
|---|---|---|---|
| PETR4 | R$ 26,90 | R$ 5,88 | **4,57×** |
| ITUB4 | R$ 16,08 | R$ 7,22 | **2,23×** |
| WEGE3 | R$ 3,20 | R$ 2,29 | **1,40×** |

Uma ação seria encolhida 4,57×, a outra 1,40×. **Isso embaralha o ranking em vez de apenas reduzi-lo.** Empresas que historicamente pagaram muito dividendo (bancos, elétricas, Petrobras) apareceriam artificialmente menos líquidas do que empresas de crescimento que nunca distribuíram lucro.

E há um agravante: o fator **cresce quanto mais para trás no tempo**, porque acumula mais anos de dividendos. Em 05/08/2026 o fator é 1,00× para todo mundo (não houve tempo de ajustar nada). Em 2011 chega a 4,57×. Ou seja, a distorção não seria ruído aleatório — seria um **viés sistemático que aumenta com a idade do dado**, exatamente o tipo que passa despercebido numa inspeção rápida e contamina a metade mais antiga do backtest.

##### Qual o tamanho real do estrago — medido, não estimado

Testamos: quantas das 80 ações do universo mudariam se tivéssemos usado o preço errado?

| Data do rebalanceamento | Ações que mudariam |
|---|---|
| 02/05/2011 | 3 de 80 (4%) |
| 02/01/2014 | 5 de 80 (6%) |
| 02/01/2020 | 4 de 80 (5%) |
| 02/01/2024 | 1 de 80 (1%) |

**Sejamos honestos: o impacto é modesto**, de 1% a 6% do universo. O corte nas 80 mais líquidas é grosseiro o bastante para que as gigantes permaneçam gigantes de qualquer jeito — a troca acontece nas ações de fronteira, que disputam as últimas vagas.

Em 02/05/2011, por exemplo, ALPA4, INEP4 e VIVR3 entrariam indevidamente, enquanto BRPR3, CMIG3 e COCE5 sairiam. Note que **BRPR3 é uma das seis empresas mortas** que conseguimos recuperar (Parte 2.2.7) — perdê-la por um erro de preço seria especialmente irônico.

##### Então por que insistir nisso?

Três razões:

1. **Custa zero fazer certo.** É um parâmetro no download (`auto_adjust=False`) e uma multiplicação a mais. Não há trade-off.
2. **O erro é sistemático, não aleatório.** Erros aleatórios se diluem em 184 rebalanceamentos; um viés que cresce com a idade do dado, não. Ele empurraria consistentemente na mesma direção na metade mais antiga da amostra.
3. **É defensável perante a banca.** O critério de Backtest (15%) avalia justamente "consistência das escolhas metodológicas". Poder mostrar que a equipe conhecia a diferença, escolheu conscientemente e *mediu o impacto da escolha* vale mais do que o impacto em si.

**Onde está no código:** [`scripts/02_baixar_precos.py`](../scripts/02_baixar_precos.py) baixa as duas versões (`auto_adjust=False`); [`scripts/04_montar_datasets.py`](../scripts/04_montar_datasets.py) calcula retornos do ajustado e volume financeiro do bruto.

#### 2.2.3 Decisão 2 — Uma classe de ação por empresa

Muitas empresas brasileiras têm **duas ou três classes de ação negociando ao mesmo tempo**: `PETR3` e `PETR4`, `ITUB3` e `ITUB4`, `BBDC3` e `BBDC4`, além de *units* como `KLBN11`. São títulos diferentes da **mesma empresa**, com direitos de voto e dividendo distintos, mas com preço que se move quase em uníssono — correlação típica acima de 0,95.

**Por que isso destruiria a MST.** A árvore geradora mínima conecta primeiro os pares mais próximos. Um par PETR3–PETR4 com ρ ≈ 0,98 tem distância ≈ 0,20, quase o menor valor possível na rede. Resultado: a MST gastaria suas 79 arestas ligando pares de classes da mesma empresa antes de revelar qualquer estrutura econômica de verdade. Pior, cada par assim cria um "galho" artificial de dois nós pendurado na árvore — e ambos os nós ficariam classificados como periféricos, quando na verdade são Petrobras e Itaú, as ações mais sistêmicas do mercado brasileiro.

**Analogia para Data Science:** é ter duas features quase idênticas no dataset. Em regressão isso causa multicolinearidade; num algoritmo de clustering ou de grafo, elas se agrupam entre si e mascaram a estrutura real.

**A regra:** agrupamos pelo **radical de 4 letras** do ticker (`PETR4` → `PETR`), que na B3 identifica a empresa, e mantemos apenas a **classe mais líquida** de cada empresa. No universo atual isso reduz 157 tickers distintos a 156 empresas distintas ao longo dos 15 anos.

**Isto é decisão de modelagem, não de limpeza.** É reversível numa linha em [`scripts/04_montar_datasets.py`](../scripts/04_montar_datasets.py). Se a equipe quiser testar o efeito, vale rodar a sensibilidade com e sem deduplicação e reportar — é um bom argumento de rigor no relatório.

#### 2.2.4 Decisão 3 — Calendário de pregão reconstruído

Este é o problema mais traiçoeiro que encontramos, e vale explicar por completo.

**O sintoma.** Ao montar o universo mensal pela primeira vez, quase todos os rebalanceamentos tinham 80 ações elegíveis — mas **sete deles tinham 4 ações, e dois tinham 1 ação**. Eram todos 2 de janeiro (de 2012 a 2017) e 1º de março de 2017.

**A causa.** O Yahoo Finance publica **cotação fantasma** (ver Glossário 0.1) em feriados da B3. Encontramos 68 dessas datas: 25 de janeiro (aniversário de São Paulo), Carnaval, 21 de abril, 1º de maio, Corpus Christi, 7 de setembro, 12 de outubro, 2 e 15 e 20 de novembro, 24 e 31 de dezembro. Em cada uma delas, entre **1 e 5 tickers** têm preço, contra ~173 num pregão de verdade.

**Por que isso zera a elegibilidade do universo inteiro.** A cadeia de causa e efeito:

1. Nosso calendário inicial era simplesmente "toda data em que *algum* ticker tem preço". As 68 datas fantasma entraram nele como se fossem pregões.
2. Para decidir a carteira do dia `t`, o algoritmo pega os 63 pregões anteriores a `t` e exige que a ação **tenha negociado recentemente** — a versão original da regra checava o preço no **último dia da janela**.
3. Quando `t` é 2 de janeiro, o dia anterior no calendário contaminado é **31 de dezembro** — uma data fantasma, em que só 4 tickers têm preço.
4. Logo, para 240 dos 244 tickers, o teste "tem preço no último dia da janela?" respondia **não**. A elegibilidade do universo inteiro ia a zero, sobrando as 4 ações que por acaso tinham a cotação espúria.

Ou seja: **um punhado de registros lixo em 68 datas conseguia destruir 9 dos 184 rebalanceamentos** — e não de forma aleatória, mas concentrada em janeiro, sempre no mesmo ponto do ciclo anual.

**A correção, em duas frentes:**

1. **Calendário de verdade.** Uma data só conta como pregão se tiver cotação para pelo menos 25% da mediana de ativos cotados (corte de 43 ativos/dia). A separação é limpíssima: as datas fantasma têm de 1 a 5 ativos, e o 5º percentil dos pregões reais é 152. Das 3.943 datas brutas ficaram **3.875 pregões**.
2. **Regra de negociação recente relaxada.** Em vez de exigir preço no último dia exato, exigimos negociação em **pelo menos um dos 5 últimos pregões** da janela. Uma ação legítima pode simplesmente não ter tido negócio num dia.

**Validação cruzada.** O calendário final tem 3.875 pregões; a série do Ibovespa tem 3.866, e **nenhuma data do Ibovespa está fora do nosso calendário**. Depois da correção, todos os 184 rebalanceamentos têm exatamente 80 ações.

**Onde está no código:** função `calendario_pregao` em [`scripts/04_montar_datasets.py`](../scripts/04_montar_datasets.py).

Este episódio é forte para o relatório: mostra que a equipe **auditou** os dados em vez de confiar na API, e é exatamente o tipo de rigor que o critério de Backtest (15%) premia.

#### 2.2.5 Decisão 4 — Retornos absurdos anulados

Retornos diários acima de |60%| (74 ocorrências) foram convertidos em ausência. Na prática são falhas de ajuste de proventos ou grupamentos, não movimentos de mercado.

Ficamos **conservadores de propósito**: o corte é alto o bastante para não tocar em movimentos reais e violentos. Retornos entre 25% e 60% foram mantidos — são 734 observações (0,08% do total), concentradas em ações como OGXP3, PDGR3, LUPA3 e OIBR3, empresas que de fato colapsaram no período. Apagá-las seria maquiar a história.

#### 2.2.6 O universo: como "80 ações mais líquidas" é construído

A B3 só publica a carteira teórica **do dia** — não há histórico público de composição do Ibovespa por API. Sem isso, a regra "só compre ações que estavam no IBOV naquele mês" é inexequível com fontes gratuitas.

**Nossa regra substituta:** a cada rebalanceamento, o robô só pode comprar as **80 ações de maior volume financeiro** do período recente. É uma substituição defensável porque o Ibovespa é, por definição, um índice construído sobre liquidez e negociabilidade — estamos reconstruindo o critério do índice em vez de copiar a lista.

**Construção, passo a passo (arquivo [`universo_mensal.parquet`](../dados/processados/)):**

1. Data de rebalanceamento `t` = primeiro pregão de cada mês.
2. Janela = os 63 pregões com índice **estritamente menor que `t`**.
3. Elegibilidade: cobertura de preço ≥ 90% na janela **e** negociação em pelo menos um dos 5 últimos pregões **e** volume financeiro mediano > 0.
4. Ranking pela mediana do volume financeiro na janela (mediana, não média — resiste a um único dia de leilão atípico).
5. Deduplicação por empresa (Decisão 2).
6. Corte nas 80 primeiras.

**Resultado:** 184 rebalanceamentos de 02/05/2011 a 03/08/2026, sempre com 80 ações. O universo troca em média **1,7 ações por mês (2,2%)**, com máximo de 5 — é estável, o que é bom sinal: a estratégia não vai ficar refém de um universo que se reinventa todo mês. Ao longo dos 15 anos passaram 157 tickers distintos.

**Ausência de look-ahead, verificada:** o script [`05_validar_dados.py`](../scripts/05_validar_dados.py) confirma que **zero** ações foram selecionadas sem dado na janela anterior à decisão.

#### 2.2.7 Survivorship bias: o que fazemos além de "usar sobreviventes"

A v1.2 deste plano concluiu que estaríamos restritos a sobreviventes. **Essa conclusão foi revista** — ela se apoiava num teste com tickers errados (`SOUZ3`, que nem existe; o código real da Souza Cruz é `CRUZ3`) e não distinguia deslistagem de renomeação.

Refizemos o teste com rigor: montamos uma tabela curada de **113 tickers históricos** ([`src/nexus/historicos.py`](../src/nexus/historicos.py)), cada um com motivo de saída e sucessor mapeado, e submetemos os **317 códigos** do universo candidato ao yfinance. O resultado está em [`disponibilidade.csv`](../dados/processados/) e separa três situações:

**(a) Renomeação não é buraco de dados — 47 casos resolvidos.**
Quando uma empresa troca de ticker, o Yahoo **reescreve o histórico completo sob o código novo**. Verificado um a um:

| Ticker atual | Era | Histórico disponível desde |
|---|---|---|
| `BHIA3` | VVAR3 → VIIA3 (Via Varejo / Casas Bahia) | 2010 |
| `COGN3` | KROT3 (Kroton) | 2012 |
| `MOTV3` | CCRO3 (CCR / Motiva) | 2010 |
| `AZZA3` | ARZZ3 (Arezzo) | 2011 |
| `ALOS3` | ALSC3 → ALSO3 (Aliansce) | 2011 |
| `DXCO3` | DTEX3 (Duratex / Dexco) | 2010 |
| `AMER3` | LAME3/LAME4 (Lojas Americanas) | 2010 |
| `PCAR3`, `TIMS3`, `VIVT3`, `YDUQ3`, `B3SA3`, `SUZB3`, `PRIO3`, `ENEV3`, `RENT3` | diversos | 2010–2011 |

Esse era o grosso do que a v1.2 dava como perdido.

**(b) Empresas mortas recuperadas — 19 séries, 6 delas com peso real.**
O Yahoo preserva o histórico de várias ações deslistadas até a data em que morreram. **Seis delas efetivamente entram no universo do backtest**, com participação longa:

| Ticker | Empresa | Série termina | Meses no universo |
|---|---|---|---|
| `FIBR3` | Fibria | 02/01/2019 (fusão com Suzano) | 91 |
| `BRPR3` | BR Properties | 06/08/2024 | 83 |
| `ELPL4` | Eletropaulo | 12/03/2018 (comprada pela Enel) | 81 |
| `VVAR11` | Via Varejo units | 23/11/2018 | 56 |
| `PRML3` | Prumo Logística | 09/03/2018 | 40 |
| `OGXP3` | OGX Petróleo | 10/01/2019 (recuperação judicial) | 37 |

Isso é o oposto de survivorship bias: são empresas que **quebraram ou saíram da bolsa** e cujo histórico está dentro do backtest. A OGXP3 em particular é o caso emblemático do ciclo 2012-2015 brasileiro.

**(c) Buracos remanescentes — 26 empresas, nomeadas.**
Deslistadas sem ticker sucessor e sem dados no Yahoo:

> ABRE11, ALLL3, BISA3, CIEL3, CPLE5, CRDE3, CRUZ3, CTIP3, ELET6, ELPL3, ENBR3, GPCP3, IDNT3, LINX3, MAGG3, MMXM3, MOSI3, MPLU3, NETC4, SEDU3, SGPS3, SMLE3, SQIA3, SSBR3, TAMM4, TCNO4

**O que dizemos no relatório.** Não "assumimos survivorship bias como limitação" — essa é a resposta preguiçosa. Dizemos:

> *"Testamos 317 códigos da B3 e documentamos o destino de cada um. Renomeações foram resolvidas via ticker sucessor (47 casos). Seis empresas que morreram entre 2018 e 2024 participam do backtest com 37 a 91 meses de presença no universo. Restam 26 buracos, nomeados individualmente. O viés residual é limitado a esses 26 casos e a empresas anteriores a 2011."*

Isso é verificável, específico e demonstra trabalho — vale muito mais que uma declaração genérica.

**Teste de robustez a executar:** rodar o backtest **com e sem** as 6 séries mortas e reportar a diferença. Isso mede diretamente o quanto o viés remanescente importa, em vez de especular sobre ele. Ver Parte 3.5.

### 2.3 Etapa 2: Matriz de Correlação Rolante

> **Consome:** [`retornos_log.parquet`](../dados/processados/) e [`universo_mensal.parquet`](../dados/processados/).

Para cada data de rebalanceamento `t`:

1. Ler as 80 ações elegíveis em `t` a partir de `universo_mensal.parquet`.
2. Recortar de `retornos_log.parquet` os **63 pregões anteriores a `t`**, formando uma matriz 63 × 80. Cada ação vira uma série temporal de 63 retornos diários.
3. Calcular a matriz de correlação de Pearson 80 × 80 entre essas séries.

**Como a janela "rola":** em 1º de abril, reunimos os retornos diários de janeiro, fevereiro e março e decidimos a alocação. Em 1º de maio a janela avança: descartamos janeiro, incluímos abril. O cálculo roda uma vez por mês.

**Por que 63 dias?** Trade-off:
- 21 dias: capta dinâmica recente mas é ruidosíssimo.
- 252 dias: robusto mas lento para reagir a mudança de regime.
- 63 dias (≈ 3 meses) é o padrão da literatura (Onnela et al., 2003).

**A fragilidade estatística e o shrinkage.** Estimar a correlação de 80 ações exige 3.160 parâmetros a partir de 63 observações. A matriz sai mal condicionada. **Atenção:** a MST mitiga o ruído *descartando* arestas fracas, mas **não corrige** o erro de estimação nas arestas que sobrevivem.

Usaremos o **Estimador de Shrinkage de Ledoit-Wolf** (`sklearn.covariance.LedoitWolf`). A ordem importa: o shrinkage age na **covariância**, não na correlação. Pipeline exato:

1. Estimar a covariância *shrinkada* dos retornos (alvo padrão do sklearn: identidade escalada pela variância média).
2. Normalizar para correlação, dividindo pelos desvios-padrão.
3. Só então aplicar a transformação de distância de Mantegna.

**Ressalva a monitorar:** o shrinkage comprime a diferença entre correlações fortes e fracas — "achata" o sinal. Como a MST depende dessa diferença para separar central de periférico, precisamos comparar a dispersão das centralidades **com e sem** shrinkage e relatar o efeito.

**Tratamento de ausências na janela:** ações com cobertura < 90% na janela já foram excluídas pelo filtro de elegibilidade. Para as ausências residuais, a escolha é entre descartar a ação ou imputar zero. **Não interpolar preço** — isso criaria correlação artificial. A decisão fica registrada no código do MVP.

### 2.4 Etapa 3: Distância e Construção da MST

**Da correlação para distância.** A correlação de Pearson ($ρ_{ij}$) compara a série da ação $i$ com a da ação $j$:
- Sobem e descem juntas → $ρ$ perto de +1.
- Uma sobe quando a outra desce → $ρ$ perto de −1.
- Sem relação → $ρ$ perto de 0.

Para construir um grafo precisamos de uma **distância** geométrica, não de um índice de correlação. Transformação de Mantegna (1999):

$$d_{ij} = \sqrt{2 \times (1 - ρ_{ij})}$$

| Correlação (ρ) | Distância (d) | Interpretação |
|---|---|---|
| +1,0 | 0,00 | Perfeitamente juntas |
| +0,5 | 1,00 | Correlacionadas |
| 0,0 | 1,41 | Independentes |
| −0,5 | 1,73 | Anti-correlacionadas |
| −1,0 | 2,00 | Perfeitamente opostas |

**Construção da MST.** Comece imaginando um **grafo completo**: 80 ações, cada uma ligada às outras 79, formando 3.160 pares. É um emaranhado onde quase tudo é ruído.

A **Minimum Spanning Tree** é a sub-árvore que:
- Conecta **todos** os 80 nós (ninguém fica de fora).
- Usa exatamente **79 arestas**, descartando as outras 3.081 ligações.
- **Minimiza a soma total das distâncias**, escolhendo iterativamente as pontes mais curtas sem formar ciclos.

**E a ação isolada, que não se correlaciona com ninguém?** Ela **não** é excluída — a regra de ouro da MST é que nenhum nó fica de fora. O algoritmo a liga pela sua ponte *menos longa* (a maior correlação que ela tem, mesmo sendo fraca). Ela fica na rede, pendurada por um único fio comprido. **É exatamente isso que a torna periférica.**

**Por que MST e não o grafo completo?** A MST filtra e mantém só as conexões de primeira ordem. É como desenhar só as rodovias principais de um país, ignorando as estradinhas de terra.

**Analogia para Data Science:** a MST é *feature selection* drástica, como um Lasso muito forte — em vez de 3.160 interações, você fica com o esqueleto de 79.

**Implementação:** Kruskal ou Prim via `networkx`.

### 2.5 Etapa 4: Medir Periferia — Problema Aberto do Projeto

> ⚠️ **Esta é a decisão técnica mais crítica em aberto, e precisa ser resolvida antes de escrever o loop de backtest.**

#### 2.5.1 O problema: Betweenness numa árvore é degenerada

A **Betweenness Centrality** mede quantos caminhos mais curtos passam por um nó:

$$BC(v) = Σ_{s≠v≠t} [σ_{st}(v) / σ_{st}]$$

- $σ_{st}$: número de caminhos mais curtos entre os nós $s$ e $t$.
- $σ_{st}(v)$: quantos deles passam por $v$.

Alta betweenness = a ação é uma "ponte principal", no caminho entre vários grupos. Ela se move e a rede inteira sente — comportamento sistêmico. Baixa betweenness = está na ponta de um galho, ninguém precisa passar por ela.

**O problema matemático:** numa **árvore**, todo nó-folha (grau 1) tem betweenness **exatamente zero**, por definição — nenhum caminho entre dois outros nós pode passar por uma ponta. E MSTs de correlação financeira são cheias de folhas.

**Medido nos nossos dados** (16 datas, uma por ano, com Ledoit-Wolf aplicado):

| Data | Nós | Folhas | % folhas | Empates em BC = 0 | Correlação média |
|---|---|---|---|---|---|
| 05/2011 | 80 | 41 | 51% | 41 | 0,134 |
| 05/2014 | 80 | 38 | 48% | 38 | 0,198 |
| 05/2017 | 80 | 42 | 53% | 42 | 0,131 |
| **05/2020** | 80 | 41 | 51% | 41 | **0,595** |
| 05/2023 | 80 | 43 | 54% | 43 | 0,223 |
| 05/2024 | 80 | 48 | 60% | 48 | 0,175 |
| 05/2026 | 80 | 37 | 46% | 37 | 0,363 |

**Entre 35 e 48 ações empatam em centralidade zero todo mês** — de 44% a 60% do universo. "Selecionar as Top 10 de menor centralidade" seria, na prática, **sortear 10 entre ~41 ações**, com o desempate decidido pela ordem alfabética do `pandas`. O sinal não seria da estratégia; seria do `sort` do dataframe.

**Isto invalida a regra de seleção como está escrita e precisa ser corrigido.** É também, ironicamente, um ótimo material para o relatório: mostra a equipe encontrando e corrigindo uma falha estrutural do próprio modelo antes de rodar o backtest.

#### 2.5.2 O que NÃO resolve

- **Betweenness ponderada pela distância** (`weight='weight'`): não adianta. A folha tem BC = 0 por topologia, independentemente dos pesos.
- **Degree Centrality:** piora. Numa árvore, toda folha tem grau exatamente 1 — o empate seria idêntico e ainda mais grosseiro.

#### 2.5.3 Agenda de métricas a testar

Todas produzem ranking **contínuo**, sem empate em massa. A escolha entre elas deve ser feita no período in-sample e relatada por completo.

| # | Métrica | Definição | Por que pode funcionar |
|---|---|---|---|
| 1 | **Closeness Centrality ponderada** | Inverso da soma das distâncias na MST até todos os outros nós | Contínua por construção; captura "estou longe de todo mundo" |
| 2 | **Comprimento da aresta de ligação** | Distância da única (ou menor) aresta que conecta o nó à árvore | Interpretação direta: o fio que me prende ao mercado é comprido |
| 3 | **Excentricidade** | Maior distância do nó até qualquer outro nó da árvore | Mede "quão longe da borda oposta eu estou" |
| 4 | **Soma das distâncias (farness)** | Soma dos caminhos mais curtos até todos os outros | Versão não-normalizada da closeness |
| 5 | **Eigenvector centrality** | Importância recursiva: sou central se me conecto a centrais | Contínua; padrão em análise de redes |
| 6 | **Betweenness em duas etapas** | Filtrar as folhas, depois desempatar por (2) ou (1) | Preserva a intuição original da tese |
| 7 | **PMFG em vez de MST** | Grafo planar maximamente filtrado (Tumminello et al., 2005) | Não é árvore — betweenness deixa de ser degenerada |

#### 2.5.4 Os dois controles obrigatórios (sem grafo)

Esta é a pergunta que a banca vai fazer: **"por que precisa de grafo?"** Se um cálculo trivial produzir a mesma carteira, a MST é enfeite. Precisamos de dois baselines sem teoria de grafos:

| Controle | Como calcular | O que testa |
|---|---|---|
| **Menor correlação média** | Para cada ação, média de ρ com as outras 79; pegar as 10 menores | Se a MST não ganhar deste, o grafo não agrega |
| **Menor beta vs. Ibovespa** | Regressão Linear (onde a inclinação/slope é o beta) dos retornos da ação contra o IBOV. O "Beta" mede o quanto a ação responde aos choques do mercado. Ações com baixo beta (< 1) variam menos e são o porto-seguro óbvio. | Testa se "ação periférica na rede MST" é só um jeito chique e complicado de selecionar ações de baixo beta. Se a MST só trouxer ações de baixo beta iguais à regressão, a teoria de grafos não agrega valor prático. |

**Este é o teste mais importante do projeto para o critério de Conceito (20%).** Um resultado em que a MST empata com "menor correlação média" ainda é uma entrega honesta e valiosa — mas precisa ser dito.

#### 2.5.5 Critério de decisão

A métrica escolhida deve:
1. Produzir ranking contínuo (menos de 5% de empates no top 20).
2. Gerar carteira com **estabilidade razoável** mês a mês (turnover não explosivo).
3. Ter interpretação econômica defensável em uma frase.
4. Vencer, ou ao menos igualar com justificativa, os dois controles de 2.5.4.

#### 2.5.6 Veredito Oficial (Atualizado em 10/ago/2026)

Conforme testes empíricos rigorosos realizados e documentados em `docs/decisao_metrica_periferia_MST.md` (via script `06_avaliar_periferia.py`), a métrica oficial cravada para a estratégia é a **FARNESS (Soma Absoluta das Distâncias)**. 
- A *Betweenness* foi matematicamente reprovada (54% de empates no valor zero). 
- O *Edge Length* mostrou-se excessivamente correlacionado com o baseline de baixo Beta ("míope", não vê a árvore inteira). 
- A *Closeness* inverte contra-intuitivamente a escala (dificultando a explicação para a banca). 
A **Farness** provou ser 100% contínua, isolar ações verdadeiramente imunes aos choques sistêmicos e capturar a macro-topologia real do mercado.

### 2.6 Etapa 5: Seleção do Pool Periférico

> **Consome:** ranking da Etapa 4. **Produz:** pool de candidatas para os Filtros de Alpha.

**Regra de seleção do pool:** ordenar as 80 ações do universo pela **Farness** (da maior para a menor, visto que valores maiores indicam ações mais distantes do "miolo" da rede) e selecionar as **Top N mais periféricas** como **pool de candidatas**.

**Mudança na v3.0:** na versão anterior, o Top 10 era a carteira final. Agora o Top N (N = 15 ou 20, calibrado no in-sample) é um **pool de triagem** — as ações que efetivamente entram na carteira são decididas pelos Filtros de Alpha (Etapa 5B). A expansão do pool dá margem para os filtros operarem: se começássemos com 10, o Momentum eliminaria metade e a carteira ficaria concentrada demais.

*Por que 80 e por que N entre 15-20.* O universo de 80 nomes concentra a liquidez da B3 — buscar alfa fora dele significa small caps com spread de compra/venda enorme e backtest irrealista. Selecionar os 15-25% mais periféricos (Top 15-20 de 80) é um filtro forte dentro de um universo com liquidez garantida, e ao mesmo tempo largo o suficiente para que os Filtros de Alpha tenham material de trabalho.

**Regra de alocação:** **equal-weight entre as ações aprovadas** pelos Filtros de Alpha. Se M ações passam em todos os filtros (M ≤ N), cada uma recebe 1/M do capital alocado a ações. O restante (1 − M/M_max) pode ir para o CDI quando o número de aprovadas é muito baixo — ver Etapa 5B.

*Por que equal-weight e não otimização de Markowitz:* otimizar pesos exigiria estimar retornos esperados, que é exatamente a parte da matriz que menos se consegue estimar com 63 observações. Equal-weight é transparente, robusto e não introduz mais um grau de liberdade para overfitar. É uma escolha defensável, não preguiça.

**Por que a seleção topológica sozinha NÃO basta (lição do MVP).**  O MVP (v2.0) provou que comprar as Top 10 periféricas indiscriminadamente produz Sharpe −0,21. O diagnóstico:

1. **Estar na periferia da rede é condição necessária, mas não suficiente.** A ação pode ser descorrelacionada do mercado e ainda assim estar em queda livre. A MST não sabe nada sobre *direção* — ela só sabe sobre *estrutura*.
2. **O turnover de 67% mostra que o modelo compra e vende sem convicção.** Ações entram porque ficaram periféricas num mês e saem no seguinte sem ter gerado retorno.
3. **A periferia é onde olhar; o alpha vem de QUANDO comprar.** A MST filtra o universo para ações descorrelacionadas; os Filtros de Alpha (Etapa 5B) adicionam convicção direcional.

**Onde a estratégia é frágil:**
1. **Crash absoluto de liquidez.** Quando todos vendem tudo sem olhar fundamento (março de 2020), a rede se contrai tanto que o conceito de periferia perde força. Nossos dados mostram a correlação média indo a 0,595 nesse mês.
2. **Custo de turnover.** Se as ações mudarem completamente todo mês, a corretagem come o retorno. Os Filtros de Alpha devem mitigar isso (ver 2.6B), mas precisa ser medido no backtest.
3. **Concentração setorial acidental.** Nada na regra impede que as periféricas de um mês sejam 6 elétricas. Precisamos **medir** a concentração setorial da carteira e reportar; se for extrema, considerar um teto por setor como variante.

**Rebalanceamento:** mensal, no primeiro pregão. Recalcular MST com os 63 dias anteriores, atualizar o pool periférico, aplicar os Filtros de Alpha, reequilibrar pesos.

### 2.6B Etapa 5B: Filtros de Alpha (Predição) — NOVA na v3.0

> **Consome:** pool periférico da Etapa 5 + preços históricos. **Produz:** carteira final de ações aprovadas.

Esta etapa é a principal inovação da v3.0. O raciocínio em uma frase:

> *A MST diz ONDE olhar (ações descorrelacionadas). Os Filtros de Alpha dizem QUANDO comprar (ações com convicção direcional). Juntos, eles combinam diversificação genuína com timing de mercado.*

#### 2.6B.1 Filtro de Momentum (Simples e Robusto)

**Regra:** entre as Top N ações do pool periférico, o robô só compra aquelas cujo **preço de fechamento está acima da Média Móvel Simples de L dias (SMA_L)**.

$$\text{Compra se: } P_t > \text{SMA}(L) = \frac{1}{L} \sum_{i=t-L+1}^{t} P_i$$

Se a ação é periférica mas o preço está **abaixo** da SMA, o robô a descarta naquele mês — independentemente de quão periférica ela seja. Estar na periferia sem tendência de alta é diversificação sem direção.

**Parâmetro L (comprimento da SMA):** é o único grau de liberdade deste filtro. Será calibrado no in-sample testando 4 valores:

| L (dias) | Equivalência | Característica |
|---|---|---|
| 50 | ~2,5 meses | Reativo, mais sensível a reversões de curto prazo |
| 100 | ~5 meses | Balanço entre reatividade e estabilidade |
| 150 | ~7 meses | Tendência de médio prazo |
| 200 | ~10 meses | Clássico de longo prazo, usado pela indústria |

**Sustentação acadêmica — por que isso NÃO é overfitting.** O momentum é a **anomalia mais documentada e persistente em finanças**:

- **Jegadeesh & Titman (1993):** demonstraram que ações que subiram nos últimos 3-12 meses tendem a continuar subindo nos próximos 3-12 meses. Publicado no *Journal of Finance*, replicado em dezenas de mercados.
- **Asness, Moskowitz & Pedersen (2013):** confirmaram o efeito de momentum em ações, moedas, commodities e bonds, em 8 mercados e 40 anos de dados. "Value and Momentum Everywhere", *Journal of Finance*.
- **Fama & French (2012):** incluíram momentum como fator de risco nos modelos de precificação, reconhecendo que a anomalia persiste.

Usar SMA como proxy de momentum não é um modelo complexo — é um filtro binário (acima/abaixo). A única escolha é L, testada em 4 valores com **validação cruzada temporal** dentro do in-sample (3 folds expansíveis — ver Parte 3.1.1). O L escolhido deve ser estável nos 3 folds, não apenas o melhor no período inteiro. **Comparar isso com um modelo de ML com 200 features seria desproporcional.**

**Interpretação econômica:** ações periféricas na MST são guiadas por fatores idiossincráticos (não sistêmicos). Quando esses fatores estão gerando retorno positivo (preço acima da SMA), a ação tem momentum idiossincrático — e a decorrelação da MST protege esse momentum de ser cancelado por choques de mercado.

**Analogia para Data Science:** é como ter um bom feature set (MST seleciona features descorrelacionadas) e depois aplicar um threshold simples (SMA como decision boundary). O threshold não é aprendido dos dados — é um corte natural (acima/abaixo da média móvel).

#### 2.6B.2 Filtro de Machine Learning (Preditivo — Opcional/Complementar)

> ⚠️ **Este filtro é opcional.** Só entra na versão final se demonstrar melhoria sobre o Momentum puro no in-sample. Os critérios do Itaú são explícitos: *"complexidade sem justificação é fator negativo"*. Se o Momentum sozinho resolver, ML seria over-engineering.

**Objetivo:** treinar um classificador leve para prever se o retorno dos próximos K pregões (K = 5 ou 10) de uma ação periférica será **positivo ou negativo**. Usado como gatilho final de compra.

**Modelo:** Random Forest Classifier ou XGBoost, com complexidade deliberadamente limitada:
- `max_depth ≤ 5` (árvores rasas, sem memorizar o treino)
- `n_estimators ≤ 100`
- `min_samples_leaf ≥ 10`

**Features (todas backward-looking — zero look-ahead):**

| Feature | Descrição | Fonte |
|---|---|---|
| `farness_score` | Posição na periferia da MST | `farness_completa.parquet` |
| `sma_ratio_50` | Preço / SMA(50) | `precos_ajustados.parquet` |
| `sma_ratio_200` | Preço / SMA(200) | `precos_ajustados.parquet` |
| `vol_21d` | Volatilidade rolante de 21 dias | `retornos_log.parquet` |
| `volume_ratio` | Volume atual / mediana 63 dias | `volume_financeiro.parquet` |
| `rsi_14` | RSI de 14 dias | Calculado dos retornos |
| `ret_5d` | Retorno dos últimos 5 dias | `retornos_log.parquet` |
| `ret_21d` | Retorno dos últimos 21 dias | `retornos_log.parquet` |
| `ret_63d` | Retorno dos últimos 63 dias | `retornos_log.parquet` |

**Disciplina de treinamento (CRÍTICO para anti-overfitting):**

Duas abordagens serão testadas e comparadas:

1. **Walk-forward validation:** treinar com todos os dados até o mês `t`, prever o mês `t+1`. A cada mês, o modelo é retreinado com os dados novos. Imita o que faríamos em produção real.

2. **Single-train-and-freeze:** treinar uma única vez no in-sample (2011-2018), congelar o modelo, e aplicá-lo sem alteração no out-of-sample (2019-2026). Mais simples e mais fácil de defender contra acusação de overfitting.

**Análise de feature importance:** se o modelo depender majoritariamente das features de momentum (`sma_ratio_50`, `sma_ratio_200`, `ret_5d/21d/63d`), isso **confirma** que o Momentum Filter sozinho é suficiente — e o ML não agrega. Nesse caso, aplicamos a Navalha de Occam: descartamos o ML e ficamos com o filtro mais simples. **Isso é um resultado legítimo e defensável, não uma falha.**

#### 2.6B.3 Arquitetura em Cascata — Como os Filtros Interagem

Os filtros operam em **cascata sequencial**, cada um reduzindo o universo:

```
80 ações do universo mensal
       ↓
Etapa 5: MST + Farness → Top N periféricas (N = 15-20)
       ↓  "Filtro de Universo" — WHERE to look
Etapa 5B.1: Momentum (P > SMA_L) → M ações aprovadas (M ≤ N)
       ↓  "Filtro de Alpha" — WHEN to buy
Etapa 5B.2: ML (opcional, retorno previsto > 0) → M' ações (M' ≤ M)
       ↓  "Filtro de Precisão" — refinamento opcional
Etapa 5: Alocação equal-weight entre M' ações
       ↓
Etapa 6: Filtro de Regime → ajuste de exposição total (ações ↔ CDI)
       ↓  "Filtro de Proteção" — HOW MUCH to expose
Backtest
```

**Regra para meses "vazios":** se em um mês nenhuma ação do pool periférico passar no Filtro de Momentum, o robô **aloca 100% no CDI**. Se apenas 3 ações passarem, aloca ~33% em cada e coloca os ~1% restantes em CDI (sem fração residual relevante). Isso é uma feature, não um bug:

> *Se o mercado não oferece ações periféricas em tendência de alta, o robô prefere esperar em segurança. Isso é consistente com a tese: diversificação + momentum = comprar com convicção descorrelacionada.*

**Impacto no turnover.** O turnover de 67% do MVP vem de compras e vendas sem convicção — a ação entra porque ficou periférica e sai no mês seguinte. Com o Filtro de Momentum:

1. **Menos compras:** ações periféricas em queda não entram (filtro de entrada).
2. **Menos vendas:** ações que já estão na carteira e ainda estão acima da SMA permanecem (filtro de saída implícito).
3. **Estimativa:** a ser verificada no backtest, mas o efeito esperado é redução de 67% para algo na faixa de 30-50%.

#### 2.6B.4 Safeguards Anti-Overfitting (Para a Banca)

Este é o argumento de defesa mais importante do projeto na v3.0:

| Safeguard | Como implementado |
|---|---|
| **Momentum não é fitted** | É um filtro binário (acima/abaixo da SMA). O único parâmetro é L, testado em 4 valores pré-definidos. |
| **Validação cruzada temporal (v3.0)** | Parâmetros calibrados via 3 folds expansíveis dentro do in-sample (2011→2014/15/16 treinando, 2015-16/16-17/17-18 validando). Parâmetro escolhido deve ser estável nos 3 folds, não apenas o melhor no período inteiro. Ver Parte 3.1.1. |
| **ML capped em complexidade** | max_depth ≤ 5, n_estimators ≤ 100. Walk-forward validation ou freeze após in-sample. |
| **Cascata testável por camadas** | Cada filtro (MST, Momentum, Regime) é avaliado isoladamente e em combinação. A contribuição marginal de cada camada é medida. |
| **In-sample / out-of-sample rigoroso** | Parâmetros (L, N, percentis do regime) calibrados em 2011-2018 via CV temporal e travados. Aplicados cegamente em 2019-2026. |
| **Reportamos TODAS as variantes** | Não só a vencedora. Grid completo Pool × SMA publicado, com resultado por fold. |
| **Controles sem grafo mantidos** | "Menor correlação média" e "Menor beta" da Parte 2.5.4 são testados com e sem Momentum. |
| **Navalha de Occam aplicada** | Se o ML não agrega sobre o Momentum, fica de fora. Se o Momentum não agrega sobre o MVP, reportamos honestamente. |

### 2.7 Etapa 6: Filtro de Regime

> **Consome:** distância média da MST (Etapa 3) e [`cdi_diario.parquet`](../dados/processados/).

A MST informa não só posições relativas, mas o **estado geral do mercado**:

- **Mercado calmo:** MST espalhada — muitos ramos, distâncias médias grandes (correlações baixas).
- **Mercado em crise:** MST contraída — poucas ações dominam o centro, distâncias despencam.

**Confirmado nos nossos dados:** correlação média de 0,10 a 0,22 em períodos normais contra **0,595 em maio de 2020**. O sinal existe e é grande — não é sutileza estatística.

**A métrica e a escolha do threshold:**
- Monitoramos a **distância média normalizada** da MST mês a mês.
- **Risco de overfitting:** escolher o threshold depois de ver o backtest inteiro invalida o modelo.
- **Regra:** a métrica é *backward-looking* (só olha distâncias até `t−1`). O **percentil** (5%, 10% ou 15% histórico) é calibrado no **in-sample via validação cruzada temporal** (mesmos 3 folds da Parte 3.1.1) e depois **fixado e aplicado cegamente** no out-of-sample. O percentil escolhido deve ser estável nos 3 folds — se cada fold elege um percentil diferente, a escada de regime é frágil e devemos reportar isso.
- **Transparência:** relatamos **todas** as alternativas testadas e seus resultados **por fold e no in-sample inteiro**, e mostramos se a escolha sobreviveu no out-of-sample.
- **Defesa ativa:** distância média abaixo do limiar → cortar exposição em ações (para 50% ou 20%) e alocar o restante no CDI.
- **Retomada:** distância volta a subir acima do limiar → restaurar 100%.

**Limitação estrutural a declarar no relatório.** A distância média vem de uma janela *trailing* de 63 dias e é avaliada uma vez por mês. Num crash que se desenvolve em dias — como março de 2020 — **o filtro reage depois do estrago**. Ele protege contra crises que se arrastam, não contra choques súbitos. Vender isso como proteção geral seria desonesto; precisamos quantificar o atraso da reação no backtest e mostrá-lo.

---

## Parte 3: O Backtest

### 3.1 Estrutura

```
Para cada rebalanceamento t de Mai/2011 a Jul/2026 (183 meses):
  1. Ler as 80 ações elegíveis em t          → universo_mensal.parquet
  2. Recortar 63 pregões anteriores a t      → retornos_log.parquet
  3. Covariância Ledoit-Wolf → correlação → distância → MST
  4. Calcular Farness → ranking → Pool Top N periféricas
  5. FILTROS DE ALPHA (v3.0):
     5a. Momentum: manter apenas ações com Preço > SMA(L)
     5b. (Opcional) ML: manter apenas ações com retorno previsto > 0
     → M ações aprovadas
  6. Alocação: equal-weight entre as M aprovadas (resto em CDI)
  7. Filtro de Regime: distância média da MST vs. threshold
     7a. Acima  → manter alocação (100% exposto em ações aprovadas)
     7b. Abaixo → reduzir exposição, restante no CDI → cdi_diario.parquet
  8. Apurar retorno da carteira até o rebalanceamento seguinte → precos_ajustados.parquet
  9. Descontar custos de transação sobre o turnover efetivo
```

**Período.** Os dados começam em 03/01/2011; os primeiros 63 pregões são consumidos pela primeira janela. O primeiro rebalanceamento possível é **02/05/2011** e o último mês completo é **julho de 2026** — **183 meses (15,2 anos)**. A v1.3 propunha começar em Mar/2013; com os dados que temos, começar em Mai/2011 ganha quase 2 anos de amostra e inclui o ciclo de colapso das *ex-*queridinhas (OGX, PDG) que hoje está no universo.

**Divisão in-sample / out-of-sample:**

| Período | Intervalo | Meses | Serve para |
|---|---|---|---|
| **In-sample** | Mai/2011 – Dez/2018 | 92 | Calibrar todos os parâmetros (L, Pool, percentis do regime) |
| **Out-of-sample** | Jan/2019 – Jul/2026 | 91 | Teste cego, nenhum parâmetro tocado |

**Por que a divisão ~50/50? (Equilíbrio de Regimes e Crises)**
A escolha de particionar 15,2 anos quase exatamente pela metade não é arbitrária, mas sim uma decisão fundamentada na história macroeconômica brasileira. Essa linha de corte garante que tanto o período de calibração quanto o de teste cego contenham uma amostra robusta de crises severas e ciclos de alta *(bull markets)*:

- **O que o In-Sample (2011-2018) aprende:** A crise macroeconômica brasileira, o colapso prolongado das commodities (ex: OGX), o forte *bull market* do ciclo de *impeachment* (2016-2017), o *crash* de evento único do *Joesley Day* (2017) e o estresse sistêmico da Greve dos Caminhoneiros (2018).
- **O que o Out-Of-Sample (2019-2026) valida:** O *bull market* da Reforma da Previdência (2019), o choque global imediato dos *circuit breakers* da COVID-19 (2020), o ciclo inflacionário violento que levou a Selic de 2% a 13,75% (2021-2022) e a posterior estabilização.

Se fizéssemos um corte 80/20 (padrão em Machine Learning), correríamos o risco de calibrar o modelo em um excesso de regimes e validar em uma janela curta, enviesada para um único comportamento de mercado. Com a proporção 50/50, provamos que a calibração no In-Sample não precisa ver o futuro (COVID, Selic a 13,75%) para sobreviver a ele.

#### 3.1.1 Validação Cruzada Temporal dentro do In-Sample (v3.0)

**O problema.** O in-sample é usado para escolher o melhor L (SMA), Pool (Top N) e percentis do regime. São poucos parâmetros (~64 combinações no grid), mas selecionar o "melhor" por Sharpe no período inteiro é uma forma leve de otimização. Se o parâmetro vencedor funcionar por acaso num sub-período específico (ex: rally de 2016-2017), o out-of-sample pode decepcioná-lo.

**A solução: validação cruzada temporal com janela expansível.** Em vez de olhar apenas o Sharpe no in-sample inteiro, dividimos o in-sample em **3 folds temporais** que simulam o que faríamos em tempo real — treinar com dados passados e validar no futuro imediato:

```
Fold 1: Treino 2011-2014  →  Validação 2015-2016  (24 meses)
Fold 2: Treino 2011-2015  →  Validação 2016-2017  (24 meses)
Fold 3: Treino 2011-2016  →  Validação 2017-2018  (24 meses)
```

**Critério de seleção de parâmetros:** o parâmetro escolhido (ex: L=200, Pool=20) deve ter Sharpe **consistente nos 3 folds**, não necessariamente o maior em cada um. Concretamente:

1. Rodar o grid Pool × SMA em cada fold.
2. Se L=200 é o melhor nos 3 folds → robustez forte, confiança alta.
3. Se cada fold elege um L diferente → o sinal é fraco e deve ser reportado honestamente.
4. Se uma **região** do heatmap (ex: L=100-200 e Pool=15-20) é consistentemente boa nos 3 folds → a escolha é insensível ao valor exato e o risco de overfitting é baixo.

**Por que não criar um conjunto de validação separado.** Com 183 meses totais, um split em 3 partes (treino/validação/teste) deixaria cada conjunto com ~60 meses — curto demais para capturar ciclos de mercado completos. A CV temporal **dentro** do in-sample dá a mesma proteção sem sacrificar amostra no out-of-sample.

**Analogia para Data Science:** é `TimeSeriesSplit` do scikit-learn. Cada fold respeita a ordem cronológica — nunca treina no futuro.

### 3.2 Benchmarks — E Por Que o CDI É o Alvo Real

**O fato que reorienta o projeto.** Nos dados coletados, em 15,6 anos:

| Referência | Acumulado | Anualizado | Vol. anualizada |
|---|---|---|---|
| **CDI** | **4,34×** | **9,87%** | — |
| Ibovespa | 2,54× | 6,16% | 23,2% |
| BOVA11 (ETF investível) | 2,52× | 6,12% | 23,5% |

**O CDI rendeu 71% a mais que o Ibovespa, sem oscilar.** Quem comprou índice em 2011 assumiu 23% de volatilidade ao ano para terminar bem atrás de quem deixou o dinheiro rendendo juros.

**Duas consequências diretas:**

1. **Bater o Ibovespa não prova quase nada.** Qualquer estratégia que passe parte do tempo em caixa provavelmente bate o Ibovespa nesse período — inclusive não fazer nada. Se a página de resultados mostrar só "Nexus vs. IBOV", um avaliador experiente vai perceber na hora que o benchmark é fácil.

2. **O Sharpe do Ibovespa foi negativo.** Com retorno abaixo do CDI, o numerador do Sharpe é negativo. Isso quer dizer que **"Sharpe superior ao Ibovespa" é um alvo baixíssimo** — e a versão original da nossa hipótese (Parte 1.1) mirava exatamente nele. Por isso a hipótese foi endurecida na v2.0.

**Como isso vira vantagem no relatório.** Em vez de esconder, usamos a assimetria como argumento de honestidade:

> *"Bater o Ibovespa neste período é um alvo baixo — o CDI o superou com folga e sem volatilidade. Por isso adotamos o CDI como benchmark principal e reportamos Sharpe absoluto, não relativo ao índice."*

Isso pontua em Análise de Resultados (15%) e em Conclusão (10%), porque mostra que a equipe entende o que está medindo.

**Conjunto final de benchmarks:**

| Benchmark | Papel | Fonte |
|---|---|---|
| **CDI** | **Benchmark principal.** Sharpe positivo exige superá-lo | [`cdi_diario.parquet`](../dados/processados/) |
| **BOVA11** | Mercado investível de verdade, líquido de taxa | [`benchmarks.parquet`](../dados/processados/) |
| **Ibovespa** | Referência conceitual que a banca reconhece | [`benchmarks.parquet`](../dados/processados/) |
| **Equal-weight das 80 do universo** | Isola o efeito da *seleção* do efeito de *peso igual* | Calculado no backtest |
| **10 ações sorteadas do universo** | Controle aleatório: a seleção bate o acaso? | Calculado no backtest (200 sorteios, distribuição) |

O último merece destaque: comparar contra **carteiras aleatórias de 10 ações do mesmo universo** responde diretamente "o ranking de periferia agrega ou 10 ações quaisquer dariam o mesmo?". Rodando 200 sorteios obtemos uma distribuição e podemos posicionar o Nexus como percentil. É barato de computar e é evidência forte.

### 3.3 Métricas

| Métrica | O que mede | Fórmula |
|---|---|---|
| **Retorno acumulado** | Rendimento do período total | Produto dos (1 + retorno mensal) |
| **Retorno anualizado** | Retorno médio por ano | (1 + Retorno Total)^(1/anos) − 1 |
| **Volatilidade anualizada** | Oscilação por ano | Desvio padrão dos retornos mensais × √12 |
| **Sharpe Ratio** | Retorno por unidade de risco | (Retorno − CDI) / Volatilidade |
| **Máximo drawdown** | Pior queda pico-a-vale | Maior queda acumulada consecutiva |
| **Information Ratio** | Excesso vs. benchmark / tracking error | (Retorno − BOVA11) / Vol(Retorno − BOVA11) |
| **Turnover mensal** | Fração da carteira que muda | **Σ\|peso_novo − peso_antigo\| / 2** |
| **Calmar Ratio** | Retorno anualizado / Max Drawdown | Retorno por unidade de pior perda |
| **Beta vs. Ibovespa** | Sensibilidade ao mercado | Regressão dos retornos mensais |
| **% de meses em caixa** | Quanto o filtro de regime atuou | Meses com exposição < 100% / total |
| **Concentração setorial** | Risco escondido de setor | Máx. de ações do mesmo setor na carteira |

**Correção na v2.0:** o turnover era definido como "nº de ações substituídas / 10". Isso ignora que o rebalanceamento também **reequilibra os pesos** das ações que permaneceram — uma ação que subiu muito precisa ser parcialmente vendida para voltar a 10%. A fórmula correta é a soma das variações absolutas de peso dividida por 2, que é o que de fato gera custo.

### 3.4 Tratamento de Vieses

| Viés | Como mitigamos | Status |
|---|---|---|
| **Look-ahead bias** | Janela estritamente `< t` na formação do universo e da correlação. Verificado por script: **0 violações**. Posição assumida no fechamento do 1º pregão do mês. | ✅ Verificado |
| **Survivorship bias** | 317 tickers testados; 47 renames resolvidos; 6 empresas mortas dentro do backtest (37 a 91 meses); 26 buracos nomeados. Teste com/sem séries mortas planejado. | ✅ Mitigado e quantificado |
| **Cotação fantasma / calendário** | 68 datas de feriado removidas; calendário validado contra o Ibovespa. | ✅ Corrigido |
| **Distorção de liquidez histórica** | Volume financeiro do preço bruto, nunca do ajustado. | ✅ Corrigido |
| **Multicolinearidade de classes** | Uma classe por empresa (radical de 4 letras). | ✅ Corrigido |
| **Sobre-otimização** | In-sample / out-of-sample de ~50/50. **Validação cruzada temporal** com 3 folds expansíveis dentro do in-sample (Parte 3.1.1). Sensibilidade em múltiplos eixos (Parte 3.5). Todas as variantes testadas reportadas, não só a vencedora. | ✅ Controlado |
| **Custos de transação** | 0,05% por operação sobre o turnover em peso. Sensibilidade também a 0,10% e 0,20%. | ✅ Controlado |
| **Transaction timing** | Decisão com dados até o fechamento do último pregão do mês anterior; execução no fechamento do 1º pregão do mês. | ✅ Controlado |
| **Viés de seleção do próprio autor** | Controles sem grafo (correlação média, beta) e carteiras aleatórias como piso. | ✅ Planejado |

### 3.5 Testes de Robustez

| # | Parâmetro | Variações | O que responde |
|---|---|---|---|
| 1 | Janela de correlação | 42, 63, 126 pregões | O resultado depende de uma janela específica? |
| 2 | Nº de ações | Top 5, 10, 15, 20 | O efeito de periferia persiste com outras concentrações? |
| 3 | **Métrica de periferia** | As 7 da Parte 2.5.3 | **Qual métrica sobrevive?** (crítico) |
| 4 | **Controles sem grafo** | Correlação média, beta | **A MST agrega sobre o trivial?** (crítico) |
| 5 | **Carteiras aleatórias** | 200 sorteios de 10 ações | O ranking bate o acaso? |
| 6 | Threshold do regime | 5%, 10%, 15% históricos | Qual nível de defesa maximiza Sharpe sem sacrificar alta? |
| 7 | Custo de transação | 0,05%, 0,10%, 0,20% | A estratégia sobrevive a custo realista? |
| 8 | Shrinkage | Com e sem Ledoit-Wolf | O shrinkage achatou o sinal de centralidade? |
| 9 | Deduplicação de classes | Com e sem | Quanto a decisão da Parte 2.2.3 muda o resultado? |
| 10 | **Séries mortas** | Com e sem as 6 empresas encerradas | Qual o tamanho real do survivorship bias residual? |
| 11 | Sub-períodos | 2011-2015, 2016-2020, 2021-2026 | O efeito é estável no tempo ou vem de um período só? |
| 12 | **Comprimento da SMA (v3.0)** | L = 50, 100, 150, 200 dias | Qual SMA captura melhor o momentum periférico? |
| 13 | **Tamanho do Pool pré-Alpha (v3.0)** | Top 10, 15, 20, 25 | Quantas candidatas alimentam os Filtros de Alpha? |
| 14 | **Camadas isoladas (v3.0)** | MVP puro / +Regime / +Momentum / +Cascata completa | Qual a contribuição marginal de cada filtro? |
| 15 | **ML vs. Momentum (v3.0)** | Momentum puro / ML puro / Momentum+ML / Walk-forward vs. freeze | O ML agrega sobre o Momentum? (Navalha de Occam) |
| 16 | **Estabilidade por CV temporal (v3.0)** | Melhor (L, Pool) em cada fold vs. in-sample inteiro | O parâmetro vencedor é estável ou depende do sub-período? |

Os itens **3, 4, 5, 10, 14 e 16** são os que geram argumento de defesa mais forte. Se o tempo apertar, são os últimos a cortar. O item **14** mostra contribuição marginal de cada camada; o **16** prova que os parâmetros não foram sobre-otimizados.

---

## Parte 4: Análise de Resultados

### 4.1 Visualizações Planejadas

1. **Retorno acumulado** — Nexus vs. **CDI** vs. BOVA11 vs. Ibovespa. Gráfico principal. Note a ordem: o CDI vem primeiro na legenda, porque é o alvo.
2. **Grafo MST lado a lado** — período calmo (espalhada) vs. março de 2020 (contraída), com as periféricas selecionadas destacadas. É a imagem-assinatura do robô.
3. **Tabela de métricas** — Nexus vs. os 5 benchmarks da Parte 3.2.
4. **Distribuição das carteiras aleatórias** — histograma do Sharpe de 200 carteiras sorteadas, com o Nexus marcado. Comunica "não é sorte" numa imagem só.
5. **Gráfico de sensibilidade** — Sharpe em função da janela e do nº de ações (heatmap).
6. **Timeline de regime** — períodos de contração/expansão da rede sobre eventos de mercado, com a correlação média (0,13 → 0,595 em 2020) como série de fundo.

### 4.2 Análise Crítica

A banca valoriza honestidade. A abordar:

- **O benchmark fácil.** Declarar de saída que bater o Ibovespa neste período é pouco mérito e que o CDI é o alvo. Se o Nexus bater o Ibovespa mas perder do CDI, **dizer isso com todas as letras** — é o resultado mais provável para qualquer estratégia long-only de ações no Brasil de 2011 a 2026, e reconhecê-lo vale mais que escondê-lo.
- **Survivorship bias residual.** 26 empresas nomeadas, mais o que existiu antes de 2011. Quantificado pelo teste 10 da Parte 3.5.
- **Overfitting no filtro de regime.** Qualquer mecanismo de corte de exposição corre risco de ter sido calibrado "pelo olhar". Defender com a separação out-of-sample e reportar todas as alternativas.
- **Atraso estrutural do filtro.** Janela trailing de 63 dias avaliada mensalmente não protege contra choque súbito. Quantificar o atraso em março de 2020.
- **Tamanho amostral.** 63 observações para 3.160 parâmetros é frágil, mesmo com shrinkage. A árvore sempre carrega erro de estimação.
- **A pergunta do grafo.** Se os controles de 2.5.4 empatarem com a MST, dizer que a contribuição do grafo foi de interpretabilidade e visualização, não de alfa. É uma conclusão legítima.
- **Cenários favoráveis:** mercados laterais ou setorialmente dispersos, onde a diferenciação entre ações é alta.
- **Cenários desfavoráveis:** crashes sistêmicos de liquidez, em que a periferia deixa de existir.

---

## Parte 5: Uso de IA Generativa (15% da nota)

### 5.1 Estratégia de Documentação

O uso de IA deve estar integrado ao relatório, mas precisa ser **específico e concreto**. Nada de "usamos IA para ajudar no código".

### 5.2 Mapa de Uso — Com Exemplos Reais Já Ocorridos

| Etapa | Como a IA foi usada | Ferramenta |
|---|---|---|
| **Ideação** | Revisão da literatura (Mantegna, Onnela, Peralta) e formulação da hipótese | Gemini / Claude |
| **Auditoria de dados** | A IA testou 317 tickers da B3 e **descobriu que renomeações não são buraco de dados**, derrubando uma premissa errada do próprio plano | Claude Code |
| **Detecção de bug de dados** | A IA identificou as **68 datas de cotação fantasma** que zeravam a elegibilidade de 9 rebalanceamentos, e propôs o calendário reconstruído | Claude Code |
| **Revisão crítica de modelagem** | A IA demonstrou empiricamente que **Betweenness Centrality é degenerada em árvores** (35-48 empates em zero), invalidando a regra de seleção original antes de qualquer backtest | Claude Code |
| **Diagnóstico do MVP e arquitetura em cascata (v3.0)** | Após o MVP revelar Sharpe −0,21, a IA **diagnosticou que a seleção topológica pura não gera alpha** e propôs a reformulação: MST como Filtro de Universo + Filtros de Alpha (Momentum/ML) como camada preditiva. Mapeou a arquitetura técnica e os safeguards anti-overfitting | Gemini |
| **Código do pipeline** | Scripts 01 a 07 de coleta, limpeza, validação e backtest | Claude Code |
| **Visualização** | Código para MST comparativa e gráficos de performance | Gemini / Claude |
| **Identidade do robô** | Geração da imagem do Nexus a partir do conceito de grafos | Gemini (imagem) |
| **Estruturação do relatório** | Organização das 5 páginas priorizando visual | Gemini / Claude |

### 5.3 O Que Mostrar no Relatório

Os quatro achados em **negrito** acima são o material mais forte que temos, porque são casos em que a IA **mudou o rumo do projeto**, não apenas acelerou a digitação:

1. *"Pedimos à IA que validasse nossa premissa de survivorship bias. Ela testou 317 tickers e mostrou que estávamos errados: renomeações preservam o histórico. Recuperamos 47 casos que dávamos como perdidos."*
2. *"A IA encontrou 68 datas de feriado com cotação espúria que faziam nosso universo colapsar de 80 para 4 ações em todo mês de janeiro."*
3. *"Antes de rodar o backtest, a IA provou que a métrica central da nossa tese (Betweenness) empata 41 das 80 ações em zero, o que tornaria a seleção um sorteio. Trocamos a métrica."*
4. *"O MVP confirmou Sharpe −0,21. A IA diagnosticou que a seleção topológica pura identifica ONDE olhar mas não QUANDO comprar, e propôs a arquitetura em cascata com Filtros de Alpha (Momentum + ML), transformando a MST de seletor final em filtro de universo."*

**Menção de limitação da IA (obrigatório para não parecer propaganda):** a primeira validação de dados, feita com apoio de IA, usou o ticker `SOUZ3` — que não existe. O código real da Souza Cruz é `CRUZ3`. Esse erro levou a equipe a concluir prematuramente que estaria restrita a sobreviventes, e só foi corrigido numa segunda rodada com verificação empírica ticker a ticker. **Lição: IA generativa alucina identificadores com confiança, e nenhum código de ativo deve entrar no pipeline sem teste automático de existência.**

Essa admissão é valiosa — mostra uso maduro em vez de deslumbramento.

---

## Parte 6: O Relatório Final — 5 Páginas

### Restrições Absolutas
- **Máximo 5 páginas.** 6+ = eliminação.
- **PDF, 16:9** (widescreen).
- **Anonimato total.** Nenhum nome de pessoa, equipe ou universidade.
- **Menos de 750 palavras** no total.
- Nome do arquivo = chave de envio fornecida após o pré-relatório.

### Estrutura Sugerida

| Página | Conteúdo | Peso |
|---|---|---|
| **1** | **Identidade + Conceito.** Logo, nome, explicação. Hipótese em 2-3 frases (versão endurecida: bater o CDI). Diagrama do pipeline em cascata (MST → Alpha → Regime). | Robô (5%) + Conceito (20%) |
| **2** | **Modelagem.** Diagrama da cascata de 3 filtros como elemento central: MST (ONDE olhar) → Momentum (QUANDO comprar) → Regime (QUANTO expor). MST visual: uma ação central vs. uma periférica. Menção à Farness e ao Momentum com sustentação acadêmica. | Modelagem (20%) |
| **3** | **Backtest e Resultados.** Retorno acumulado (Nexus Cascata vs. MVP vs. CDI vs. BOVA11). Tabela de métricas. Tabela de contribuição marginal (4 versões). Box de tratamento de vieses. | Backtest (15%) + Análise (15%) |
| **4** | **Análise Crítica + IA.** Heatmap Pool × SMA. Distribuição das carteiras aleatórias. Os 4 achados em que a IA mudou o projeto (incluindo diagnóstico do MVP) + limitação do `SOUZ3`. | Análise (15%) + IA (15%) |
| **5** | **Conclusão e Próximos Passos.** Limitações. Evoluções: Mutual Information, PMFG, ML mais sofisticado, outros mercados. | Conclusão (10%) |

---

## Parte 7: Cronograma até 17/08/2026

| Período | Entrega | Status |
|---|---|---|
| **~06/ago** | **Dados base.** Universo, preços, volume, CDI, benchmarks, validação e relatório de qualidade. | ✅ **CONCLUÍDO** |
| **06-07/ago** | **Resolver a métrica de periferia (Parte 2.5).** Testar as 7 candidatas + os 2 controles sem grafo. Escolher e justificar. | ✅ **CONCLUÍDO** (Farness cravada) |
| **07-10/ago** | **MVP do backtest.** Loop ponta a ponta: universo → Ledoit-Wolf → MST → Farness → Top 10 equal-weight → apuração com custos. | ✅ **CONCLUÍDO** (Sharpe −0,21) |
| **10-11/ago** | **Diagnóstico do MVP.** Análise dos resultados negativos. Decisão de reformular para arquitetura em cascata. | ✅ **CONCLUÍDO** |
| **12-13/ago** | **Filtros de Alpha (v3.0).** Implementar Momentum, calibrar L e Pool no in-sample. Grid Pool × SMA. | 🔴 **EM ANDAMENTO** |
| **11-13/ago** | **Filtro de Regime.** Escada de degraus, calibrar percentis no in-sample. | 🔴 **EM ANDAMENTO** |
| **13-14/ago** | **Out-of-sample cego + teste de camadas.** Aplicar parâmetros travados. Comparar 4 versões. | Pendente |
| **11-14/ago** | **Relatório e visuais** *(em paralelo)*. Diagrama de cascata, MSTs comparativas, heatmap, identidade. | Em andamento |
| **15-16/ago** | **Revisão fina.** < 750 palavras, estética 16:9, checagem de anonimato. | Pendente |
| **17/ago** | **Buffer + entrega.** | — |

**Risco de cronograma:** os Filtros de Alpha são a nova prioridade. Se em 13/ago o Momentum não estiver calibrado, usar L=200 (valor padrão da indústria) e Pool=20 como fallback, e seguir para o out-of-sample.

---

## Parte 8: Identidade do Robô Nexus (5%)

### Nome
**Nexus** — do latim *nexus*, "conexão" ou "vínculo". O robô constrói e analisa a **rede de conexões** entre as ações do mercado.

### Conceito Visual
- Nós e arestas de um grafo.
- Nós periféricos (as ações selecionadas) brilham em destaque.
- Nós centrais mais opacos, sombreados.
- Paleta: fundo escuro (azul-marinho ou preto), periféricos em dourado ou verde-neon, arestas em cinza translúcido.

### Racional
"Nexus mapeia a rede invisível de conexões entre ações e investe onde os vínculos são mais fracos — porque é na periferia que está a diversificação genuína."

---

## Parte 9: Riscos e Contingência

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| **Nenhuma métrica de periferia bate os controles sem grafo** | Média | Alto | Reportar honestamente: a contribuição do grafo foi interpretabilidade e visualização. Manter a MST como ferramenta de diagnóstico de regime, que funciona muito bem (0,13 → 0,595). |
| **Nexus perde do CDI** | **Alta** | Médio | Provável para qualquer long-only de ações no período. Enquadrar como achado: "o custo de oportunidade da renda variável brasileira em 2011-2026". Mostrar Sharpe por sub-período — pode ser positivo em 2016-2020. |
| Nexus perde do equal-weight do universo | Média | Alto | Significa que a seleção não agrega. Reportar e investigar em quais regimes ela agrega. |
| Turnover alto destrói o retorno | Média | Médio | Filtros de Alpha devem reduzir de 67% para ~30-50%. Se não, testar rebalanceamento trimestral. |
| Concentração setorial acidental | Média | Médio | Medir; se extrema, testar variante com teto por setor. |
| MST instável mês a mês | Baixa | Médio | Testar janela de 126 dias. Reportar estabilidade temporal. |
| **Filtros de Alpha introduzem complexidade (v3.0)** | Média | Médio | Momentum é anomalia documentada há 30 anos (Jegadeesh & Titman). ML é opcional e capped em complexidade. A cascata é testável por camadas isoladas. Os critérios do Itaú são explícitos: "complexidade sem justificação é fator negativo" — por isso cada camada tem justificativa acadêmica independente. |
| **Momentum não melhora o Sharpe no in-sample (v3.0)** | Média | Médio | Reportar honestamente: "testamos e a anomalia de momentum não se somou à seleção topológica no Brasil 2011-2026". Manter MVP + Regime como versão final. Resultado nulo bem documentado > maquiagem. |
| Tempo insuficiente para o relatório | Média | Alto | Priorizar: (1) backtest com Momentum funcional, (2) gráfico de retorno com 4 versões, (3) heatmap Pool × SMA, (4) visual. Se o ML não couber no tempo, descartá-lo (é opcional). |
| ~~yfinance falha para tickers antigos~~ | — | — | ✅ **Resolvido.** 244 de 317 tickers obtidos, 6 séries mortas dentro do backtest. |
| ~~Composição histórica do IBOV indisponível~~ | — | — | ✅ **Resolvido** por universo de liquidez, com 184 rebalanceamentos estáveis. |
