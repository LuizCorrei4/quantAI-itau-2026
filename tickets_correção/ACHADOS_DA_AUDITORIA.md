# Achados da Auditoria e Estado da Implementação

**Data:** 15/ago/2026
**Escopo:** auditoria de `src/nexus/`, `scripts/` e `docs/01` a `docs/11`

---

## ⚠️ Fronteira honesta deste documento

Este documento separa duas coisas que não podem ser confundidas:

| Seção | Natureza | Status |
|---|---|---|
| **Parte 1 — Achados de código** | Verificáveis lendo os arquivos indicados. Não dependem de execução. | ✅ **Confirmados** |
| **Parte 2 — Resultados empíricos** | Dependem de rodar os scripts sobre os dados. | ⏳ **Pendentes** |

**Os scripts de correção foram escritos, mas não executados.** O ambiente onde
esta auditoria rodou não tem interpretador Python (apenas o stub da Microsoft
Store) nem distro WSL, e `dados/processados/*.parquet` está no `.gitignore` e
ausente do clone. Nenhum número empírico deste documento foi produzido por
execução — e nenhum foi inventado para preencher a lacuna.

---

# PARTE 1 — Achados de código (confirmados)

## 1.1 O achado central: a contribuição da MST nunca foi medida

O teste de Monte Carlo é o argumento estatístico central do projeto. Ele compara:

| Lado | Composição |
|---|---|
| **Tratamento** | MST top-20 por farness **+** momentum SMA 150 **+** cap de 10% (colchão de caixa) |
| **Nulo** | 10 ações aleatórias, **100% investidas**, sem momentum, sem cap |

As duas pontas diferem em **três** dimensões simultâneas, e toda a diferença é
atribuída à primeira. É o equivalente a testar um remédio contra um grupo controle
que também recebeu dieta e exercício diferentes, e creditar o resultado ao remédio.

**Evidência:** [`09_baseline_aleatorias.py:86`](../scripts/09_baseline_aleatorias.py#L86) —
`calcular_pesos_equal_weight(candidatas_macaco)` é chamado sem o argumento `cap`.
Com 10 ações e sem teto, o peso é 1/10 = 10% cada, somando 100%. O nulo nunca vai
para caixa.

**Por que isso importa neste período específico:** entre 2011 e 2018 o CDI rendeu
**10,3% a.a.** contra **6,2%** do Ibovespa. Manter ~13% em caixa era vantagem
estrutural — retorno maior e volatilidade menor — sem qualquer relação com
topologia de rede ou momentum.

O plano-mestre já antecipava esse teste na Parte 2.5.4 e o classificava como *"o
teste mais importante do projeto para o critério de Conceito (20%)"*. Ele
simplesmente nunca foi executado.

## 1.2 Números publicados que o código não calcula

Em [`09_baseline_aleatorias.py`](../scripts/09_baseline_aleatorias.py):

```python
# linha 117
SHARPE_NEXUS = 0.10                                   # literal
# linha 119
p_value = np.mean(sharpes_macacos >= SHARPE_NEXUS)    # calculado contra 0.10
```

E no markdown que o script gera (linhas 178-179), dentro da f-string:

```python
*   **Sharpe do Nexus (Momentum L=150 + Cap 10%):** `0.122`
*   **P-Value:** `3.2%`
```

Ambos são **strings literais**, não interpolações. Consequências encadeadas:

1. O `p_value` que o script calcula nunca chega ao documento.
2. O `3.2%` que o documento publica nunca foi calculado por código.
3. O gráfico entregue à banca (`images/02_baseline_macacos_in_sample.png`) desenha
   a linha do Nexus em **0,10** — porque usa `SHARPE_NEXUS` — enquanto a tabela ao
   lado afirma **0,122**. **A figura contradiz o texto no material de entrega.**

O valor pode até estar numericamente correto. Mas num desafio julgado por rigor
metodológico, "provavelmente certo e não auditável" não é uma posição defensável.

## 1.3 Multiple testing não corrigido

O par vencedor (Pool=20, SMA=150) é o **máximo de um grid de 16 combinações**
([`10_grid_search_alpha.py:49-50`](../scripts/10_grid_search_alpha.py#L49-L50)),
comparado contra o percentil 95 de um **sorteio único**.

São distribuições diferentes. O máximo de 16 variantes correlacionadas ultrapassa
o p95 de um sorteio único com frequência muito maior que 5%. O nulo correto é a
distribuição dos **máximos** do mesmo grid — implementado como nulo N3 no
`scripts/15_monte_carlo_corrigido.py`.

## 1.4 `docs/05` não é gerado por script e não fecha

A tabela publicada:

| Variante | Fold 1 | Fold 2 | Fold 3 | In-sample total |
|---|---|---|---|---|
| SMA 150 | −0,05 | **+0,62** | **+0,68** | **+0,122** |

Três problemas independentes:

1. **Nenhum script escreve esse arquivo.** Varredura em `scripts/`: `06` escreve em
   `docs/`, `07` escreve `resumo_backtest_mvp.md`, `09` escreve `docs/06`, `10`
   escreve `docs/07`, `08` escreve `docs/08`. Ninguém escreve `docs/05`.
2. **Os números não fecham.** Dois folds acima de +0,60 e um em −0,05 não compõem
   um total de +0,122. Sharpe não agrega linearmente, mas a distância é grande
   demais para ser efeito de composição — uma média ponderada por duração daria
   algo próximo de +0,37.
3. **Os folds não são os do plano.** A Parte 3.1.1 especifica janela expansível com
   treino e validação separados; a tabela publica três sub-períodos contíguos.

## 1.5 Camada anunciada que não existe

O Filtro de Regime aparece como terceira camada da arquitetura em praticamente
todos os documentos do projeto. **Não há `src/nexus/regime.py`**, e nenhum script
usa a contração da MST para decidir exposição.

Ironicamente, é a camada com a evidência empírica mais forte que o projeto possui:
a correlação média entre as 80 ações sai de 0,10–0,22 em períodos normais para
**0,595 em maio de 2020**. E a métrica já estava implementada —
[`calcular_distancia_media_mst`](../src/nexus/mst.py#L77) existe desde o MVP e
nunca foi usada para decidir nada.

## 1.6 Out-of-sample nunca executado

Varredura em `scripts/`: nenhum arquivo referencia 2019 ou filtra datas acima de
`2018-12-31` como início de período. **Todo número publicado pelo projeto é
in-sample** — incluindo o Sharpe de +0,122, o p-value, a sensibilidade a custos e a
batalha dos filtros.

O Pacto de Integridade do plano-mestre foi cumprido à risca. Falta executá-lo.

## 1.7 Magnitude econômica não declarada

Nenhum documento afirma isto de forma direta:

> **12,1% a.a. contra 10,3% do CDI = 1,8% a.a. de excesso, com 14,9% de volatilidade.**

Um avaliador experiente faz essa conta em dez segundos. É estritamente melhor que o
número venha da equipe, com a leitura correta ao lado.

Isso torna especialmente arriscada a afirmação de `docs/10` de que o modelo opera
com *"margem de segurança de mais de 2x a 3x o custo real de mercado"*.

---

# PARTE 1B — Defeitos novos, encontrados durante a implementação

Estes não estavam no diagnóstico inicial. Apareceram ao reimplementar o loop.

## 1.8 `calcular_turnover` cobra custo fantasma

[`portfolio.py:156-157`](../src/nexus/portfolio.py#L156-L157):

```python
if pesos_antigos is None or pesos_antigos.empty:
    return 1.0
```

Dois erros distintos:

**(a) Caixa → caixa cobra giro cheio.** Quando a estratégia passa dois meses
seguidos 100% em CDI, `pesos_antigos` está vazio e a função devolve 1.0 — custo de
10 bps sobre uma carteira que não negociou nada. Isso não é hipotético: o filtro
de momentum devolve `[]` durante todo o warmup da SMA 150, e devolve `[]` de novo
em meses hostis.

**(b) Caixa → investido cobra duas pernas.** Sair de 100% caixa para 100% ações é
`soma|Δw| = 1,0`, ou seja turnover de **0,5** e custo de **uma** perna (só compra).
A função devolve 1,0, cobrando duas.

**Direção do erro:** ambos **superestimam** custos. O Sharpe de +0,122 está, nessa
dimensão, ligeiramente **subestimado** — o defeito trabalha contra a estratégia,
não a favor. A magnitude é pequena e precisa ser quantificada na execução.

Corrigido em `motor.calcular_turnover_corrigido`. A função original foi deixada
intacta de propósito, para não alterar retroativamente números já publicados.

## 1.9 O grid de SMA não é uma comparação limpa no início da amostra

[`alpha_filters.py:63`](../src/nexus/alpha_filters.py#L63) devolve `[]` enquanto
houver menos de `L` pregões de histórico. Com dados começando em 03/01/2011:

| L | Primeiro mês em que pode operar |
|---|---|
| 50 | ~mar/2011 |
| 200 | ~out/2011 |

No grid Pool × SMA, os L longos ficam **forçadamente em CDI** por vários meses a
mais que os L curtos. Como o CDI rendia ~10% a.a. no período, isso não é ruído
neutro — desloca sistematicamente a comparação nos meses iniciais.

Efeito colateral relevante: **os primeiros meses do backtest oficial são 100% CDI
por construção, não por decisão da estratégia.** Isso precisa estar declarado.

## 1.10 `dados/resultados/README.md` invertia a tese

O arquivo afirmava:

> *"Ativos com o **menor** Farness são os mais periféricos"*

Está invertido. Farness é a **soma das distâncias** do nó até todos os outros —
quanto **maior**, mais afastado do miolo. O código sempre esteve correto
([`selecionar_top_n`](../src/nexus/portfolio.py#L43) usa `ascending=False`); era o
README que contradizia a estratégia.

Baixo impacto operacional, alto impacto se a frase migrasse para o PDF: inverteria
a tese central do robô. **Já corrigido** neste ciclo.

## 1.11 Divergência na contagem de meses

`docs/08` afirma *"Novembro/2011 a Dezembro/2018 — 86 meses"*. Mas
[`08_backtest_alpha.py:193`](../scripts/08_backtest_alpha.py#L193) monta as datas
com `d <= pd.Timestamp('2018-12-31')` e itera até `len(datas_in_sample) - 1`.
Partindo de mai/2011, isso deveria dar **91** meses de retorno, não 86, e o período
começaria em maio, não em novembro.

Uma das duas afirmações está errada. Os scripts novos imprimem a contagem real e o
intervalo efetivo no cabeçalho de cada relatório, o que resolve a ambiguidade na
primeira execução.

---

# PARTE 2 — O que foi implementado

## 2.1 Módulos novos

| Arquivo | Papel |
|---|---|
| [`src/nexus/motor.py`](../src/nexus/motor.py) | Motor de simulação único. Cada experimento é uma escolha de seletor de pool, filtro, cap e regime — não uma reimplementação do loop |
| [`src/nexus/regime.py`](../src/nexus/regime.py) | Filtro de regime com percentil **expansível** (zero look-ahead) |

O motor existe por um motivo específico: os scripts `08`, `09`, `10` e `13`
reimplementam o mesmo loop mensal cada um à sua maneira, e essa duplicação **já
produziu** a divergência de contagem de meses (1.11) e o tratamento inconsistente
do cap entre tratamento e nulo (1.1). Com um caminho de código só, "MST + momentum
+ cap" e "pool aleatório + momentum + cap" passam a diferir em **uma linha** — que
é a condição para a comparação significar alguma coisa.

## 2.2 Scripts novos

| Script | Ticket | Produz |
|---|---|---|
| [`14_ablacao_atribuicao.py`](../scripts/14_ablacao_atribuicao.py) | C03 | `docs/12` — 7 variantes isolando MST, momentum e caixa |
| [`15_monte_carlo_corrigido.py`](../scripts/15_monte_carlo_corrigido.py) | C02 | `docs/13` — três nulos (clássico, pareado, máximo-do-grid) |
| [`16_calibracao_regime.py`](../scripts/16_calibracao_regime.py) | C05 | `docs/15` — calibração + teste de redundância com o cap |
| [`17_out_of_sample.py`](../scripts/17_out_of_sample.py) | C06 | `docs/14` — teste cego, execução única |
| [`18_cv_temporal.py`](../scripts/18_cv_temporal.py) | C04 | `docs/05` reescrito, agora reproduzível |

## 2.3 Duas decisões de desenho que valem menção no relatório

**O pacto de integridade virou código.** `17_out_of_sample.py` se **recusa a rodar**
se `parametros_travados.json` não existir na raiz. O arquivo precisa estar
commitado antes, e o timestamp do commit é prova verificável de que os parâmetros
não foram escolhidos depois de ver o resultado. Uma promessa que o repositório
consegue verificar sozinho vale mais que uma declaração no PDF.

**O texto dos relatórios segue o resultado.** Os vereditos de `docs/12`, `docs/13`,
`docs/14` e `docs/15` são gerados por ramificação condicional sobre os números
apurados. Se a MST não agregar, o documento **diz que não agregou** — não há caminho
em que o gerador produza uma conclusão favorável a partir de um número desfavorável.
Isso remove a tentação de reescrever a conclusão depois de ver a tabela.

## 2.4 Correções aplicadas diretamente

- `dados/resultados/README.md` — farness desinvertida (1.10)
- `scripts/09_baseline_aleatorias.py` — banner de superseded **e** bloqueio de
  execução, para que ninguém sobrescreva `docs/06` por acidente

---

# PARTE 3 — O que falta: execução

Nenhum resultado empírico pode ser reportado até que os scripts rodem. Ordem:

```bash
# C01 — congelar o snapshot (uma única vez)
python scripts/01_universo.py
python scripts/02_baixar_precos.py
python scripts/03_baixar_cdi_ibov.py
python scripts/04_montar_datasets.py
python scripts/05_validar_dados.py

# C03 — o teste que decide a narrativa. Rode este primeiro.
python scripts/14_ablacao_atribuicao.py

# C02 e C04 — paralelizáveis
python scripts/15_monte_carlo_corrigido.py
python scripts/18_cv_temporal.py

# C05 — regime
python scripts/16_calibracao_regime.py

# C06 — SÓ depois de travar e commitar os parâmetros
python scripts/17_out_of_sample.py
```

## 3.1 As três perguntas que a execução responde

| Pergunta | Onde sai | Por que decide o relatório |
|---|---|---|
| A MST agrega sobre um pool aleatório? | `docs/12`, seção 4 | Define a tese da página 1 |
| O p-value sobrevive ao nulo pareado e à correção de grid? | `docs/13`, seção 4 | Define se "significância estatística" pode ser afirmada |
| O sinal sobrevive ao teste cego? | `docs/14`, seção 3 | Define o headline de resultado |

## 3.2 Prepare-se para as duas saídas

O resultado mais provável de `docs/12`, dado o que já se sabe — que o MVP
topológico puro entregou Sharpe −0,21 e que o colchão de caixa é estruturalmente
favorável neste período — é que **a contribuição isolada da MST seja pequena ou
nula**.

Se for isso, a leitura honesta dos próprios dados da equipe é:

> **A MST é um termômetro de regime excelente e um stock picker fraco.**

Essa tese é mais forte que a original para uma banca: é contraintuitiva, é
sustentada por evidência medida (0,13 → 0,595), e fecha um arco raro de honestidade
intelectual, todo documentado no repositório:

```
Betweenness reprovada por degenerescência (41 de 80 empatadas em zero)
   → MVP topológico puro reprovado (Sharpe −0,21)
      → ML preditivo reprovado por Occam (+0,053 vs +0,122)
         → seleção por grafo demovida a filtro de universo        [docs/12]
            → MST promovida a instrumento de risco                [docs/15]
```

Quatro hipóteses da própria equipe mortas com evidência. Isso pontua em Conceito,
Análise, Conclusão **e** Uso de IA ao mesmo tempo — mais do que um Sharpe de 0,122
que a banca vai testar em dez segundos.

**Escreva a página 3 do relatório em duas versões** — uma para "a MST agregou",
outra para "não agregou" — e escolha depois de rodar `docs/12`. As páginas 1, 2 e 5
não dependem do resultado e podem ser fechadas agora.
