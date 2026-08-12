# A História por trás dos Números: O que o nosso 1º Teste nos ensinou?

**Para:** Toda a Equipe (Especialmente a Pessoa 2, que vai pegar o bastão do MVP e levar a estratégia para o próximo nível).  
**Objetivo:** Traduzir os resultados técnicos do MVP (`resumo_backtest_mvp.md`) para uma linguagem simples e humana, criando a ponte para a próxima etapa do projeto.

---

## 1. O Choque de Realidade (A Curva de Dinheiro)

Imagine que, em 2011, você tivesse 100 reais para investir e pediu para o nosso **Robô Nexus** administrar esse dinheiro durante 15 anos, comprando sempre as ações mais "afastadas" (periféricas) do mercado.

O que aconteceu com esses 100 reais?
- Eles viraram **R$ 222** (um lucro total de 122%).

Parece bom, certo? **Errado.**
Se você tivesse sido preguiçoso e apenas deixado esses 100 reais rendendo na conta do banco (no CDI, que é a renda fixa mais segura que existe no Brasil), sem correr risco nenhum, você teria hoje **R$ 418** (lucro de 318%).

**O Veredito:** Nosso robô assumiu o risco das montanhas-russas da bolsa de valores, sofreu estresse, e no final entregou quase 3 vezes menos dinheiro do que a tranquilidade da renda fixa. *(É isso que aquele "Sharpe Negativo de -0.21" no relatório significa: o risco não compensou).*

---

## 2. O Ralo Invisível (Por que rendeu tão pouco?)

Olhando os gráficos do relatório, nós descobrimos dois grandes vilões que roubaram o dinheiro do robô:

### Vilão A: A Conta da Corretora (Turnover)
Nosso robô foi programado para escolher 10 ações todo mês. O problema é que, no Brasil, o mercado é tão caótico que o nosso cálculo matemático mudava de ideia freneticamente. Em média, o robô vendia 7 ações e comprava outras 7 **todo santo mês** (é o chamado Turnover de 67%).

Cada vez que o robô compra ou vende, a B3 e a corretora cobram um pedágio ("custo de transação"). Como ele mudava de ideia muitas vezes, o lucro foi lentamente corroído por essas taxinhas ao longo de 183 meses.

### Vilão B: A Falha da Periferia na Crise (Drawdown)
Nossa tese original era: *"Se comprarmos ações isoladas na periferia da árvore, estaremos protegidos quando o núcleo do mercado despencar."*

Acontece que isso é verdade para crises **pequenas**. Mas, quando vem uma crise gigantesca (como a greve dos caminhoneiros ou a pandemia), o pânico é tão forte que os investidores vendem TUDO. A rede inteira se esmaga. A periferia deixa de existir e cai no mesmo buraco que o resto. 

Prova disso é o **Drawdown de -48,2%**. Isso significa que, em determinado momento, nosso robô viu quase metade do dinheiro desaparecer da conta. 

---

## 3. Por que o MVP falhou e o que isso nos ensina

Antes de falar de soluções, precisamos entender que o MVP não falhou por **um** motivo. Ele falhou por **dois problemas independentes**, e cada um precisa de uma solução diferente:

| Problema | O que aconteceu | Métrica que comprova |
|---|---|---|
| **Sangria lenta (Turnover)** | O robô girava ~67% da carteira todo mês, pagando pedágio à B3 sem parar | Turnover médio: 67% |
| **Sangria aguda (Crise)** | Nas crises sistêmicas, a periferia da árvore afundou junto com o centro | Max Drawdown: -48,2% |

O Filtro de Regime ataca o **Problema 2** (crises). Mas ele sozinho **não resolve** o Problema 1 (custos de giro). Precisamos de ambas as frentes.

---

## 4. O Filtro de Regime: Muito Mais do que um "Botão do Pânico"

### 4.1 A Ideia Central (Explicada de Forma Simples)

A MST (nossa Teia de Aranha) muda de forma todo mês. Quando o mercado está calmo, ela fica **esticada** — os fios são longos, as ações estão espalhadas, cada uma se comportando do seu jeito. Quando uma crise se aproxima, ela **encolhe** — os fios ficam curtos, tudo se move junto, todo mundo vendendo em pânico.

O Filtro de Regime mede exatamente isso: **o comprimento médio dos fios da teia**. Se os fios encolherem abaixo de um limite crítico, o robô reduz a exposição em ações e foge para o CDI.

### 4.2 Por que NÃO deve ser binário (Tudo ou Nada)

Um botão simples de "liga/desliga" (100% ações → 0% ações) tem dois defeitos graves:

1. **Whipsaw (Chicote):** Se a distância média oscilar em volta do limiar, o robô vai ficar comprando e vendendo toda hora, gerando mais custo de transação (o mesmo problema do turnover!).
2. **Excesso de cautela:** Nem toda contração da rede é uma crise real. Às vezes a rede encolhe um pouco e depois volta ao normal sem nenhum crash.

### 4.3 Proposta: Thresholds Contínuos (Escada de Defesa)

Em vez de um único botão, propomos uma **escada com degraus de exposição**:

| Nível de Alerta | Condição (Distância Média) | Exposição em Ações | Exposição em CDI |
|---|---|---|---|
| 🟢 Normal | Acima do percentil 15% | 100% | 0% |
| 🟡 Atenção | Entre percentil 10% e 15% | 50% | 50% |
| 🔴 Crise | Abaixo do percentil 10% | 20% | 80% |

**O que isso significa na prática:**
- No nível **Normal**, o robô opera normalmente comprando as 10 ações periféricas.
- No nível **Atenção**, ele começa a recuar. Vende metade da posição e coloca no CDI. Se a crise se confirmar, ele já está parcialmente protegido. Se for alarme falso, ele não perdeu tanta alta.
- No nível **Crise**, ele quase zera. Mantém só 20% em ações (2 posições) e protege 80% no CDI.

### 4.4 Como Calibrar SEM Cometer Overfitting

Esse é o ponto mais delicado e mais importante para a nota da banca:

**Regra de Ouro:** Os percentis (10%, 15%) são escolhidos **apenas** olhando para os dados de **Mai/2011 a Dez/2018** (o período chamado "In-Sample"). Depois que escolhemos, **travamos** esses números e **nunca mais tocamos neles**. Aplicamos cegamente de **Jan/2019 a Jul/2026** (o "Out-of-Sample").

O roteiro prático é:

```
FASE 1: Calibração (In-Sample: 2011–2018)
  Para cada combinação de percentis (ex: 5/10, 10/15, 10/20):
    → Rodar o backtest de 2011 a 2018
    → Medir o Sharpe resultante
    → Anotar TUDO numa tabela (não só o melhor!)

FASE 2: Decisão
  → Escolher a combinação com melhor Sharpe no in-sample
  → Travar os percentis. Nunca mais alterar.

FASE 3: Teste Cego (Out-of-Sample: 2019–2026)
  → Rodar o backtest de 2019 a 2026 com os percentis travados
  → Se o Sharpe sobreviver positivo, o filtro é válido
  → Se desabar, o filtro era overfitting e precisamos ser honestos
```

> **Transparência para a Banca:** O plano exige que reportemos **TODAS** as combinações testadas no in-sample. Se testarmos 10 variantes e mostrarmos só a melhor, pareceremos desonestos. Mostrar todas e justificar a escolha vale muito mais pontos.

### 4.5 A Limitação Estrutural (Declarar no Relatório!)

A distância média vem de uma janela de 63 dias e é avaliada apenas **uma vez por mês**. Num crash que se desenvolve em **dias** (como março de 2020), o filtro reage **depois do estrago**. Ele protege contra crises que se arrastam (tipo a crise europeia de 2011-2012), não contra choques súbitos tipo um "circuit breaker" na B3.

Precisamos quantificar exatamente quantos dias de atraso o filtro teve em cada crise e mostrar isso no relatório. Esconder essa fraqueza é pior do que declará-la.

---

## 5. Será que o Filtro de Regime Sozinho é Suficiente?

**Provavelmente não.** E aqui está o porquê:

O MVP teve dois problemas (crise + turnover). O Filtro de Regime resolve o problema das crises, mas o **giro de 67% ao mês** continua corroendo o retorno nos meses normais. Precisamos atacar ambas as frentes.

### 5.1 Frente 2: Reduzir o Turnover (Ideias Concretas)

| Ideia | Como Funciona | Impacto Esperado |
|---|---|---|
| **Janela mais longa (126 dias)** | Em vez de olhar os últimos 3 meses de mercado para montar a rede, olhar os últimos 6. Isso estabiliza a árvore e muda menos ações por mês. | Turnover cai, mas a resposta a mudanças de mercado fica mais lenta |
| **Rebalanceamento trimestral** | Manter a mesma carteira por 3 meses em vez de trocar todo mês | Turnover cai para ~1/3, mas perde oportunidades de ajuste |
| **Teto por setor** | Limitar a no máximo 3 ações do mesmo setor. Evita que o robô concentre tudo em elétricas ou bancos por acidente | Reduz risco de concentração setorial acidental |
| **Buffer de permanência** | Se uma ação está no Top 10 e cai para a posição 12, ela permanece (só sai se cair abaixo do 15). Evita "chicotear" ações que estão na fronteira | Reduz trocas marginais que geram custo sem benefício |

### 5.2 Frente 3: Benchmarks Adicionais (Provar que o Grafo Funciona)

Os resultados do MVP ainda não respondem uma pergunta crucial: **a seleção por Farness é melhor do que escolher 10 ações aleatórias?**

Dois testes obrigatórios que a Pessoa 2 deve implementar:

1. **Equal-weight das 80 ações do universo:** Se comprarmos TODAS as 80 ações elegíveis com peso igual, o retorno é melhor ou pior que o Nexus? Se for melhor, nosso filtro de seleção está atrapalhando em vez de ajudar.

2. **200 carteiras aleatórias:** Sortear 200 vezes, 10 ações aleatórias das 80 elegíveis, e medir o Sharpe de cada uma. Depois plotar um histograma e marcar onde o Nexus caiu. Se o Nexus ficar acima do percentil 75%, a seleção por grafo está funcionando. Se ficar na mediana, é puro acaso.

---

## 6. Roteiro Completo para a Pessoa 2

### O que você já tem pronto (cortesia da Pessoa 1):
- `dados/resultados/serie_retornos_nexus.parquet` — Série de retornos mensais brutos e líquidos
- `dados/resultados/farness_completa.parquet` — Farness de todas as 80 ações em todos os meses
- `dados/resultados/carteiras_mensais.parquet` — Exatamente quais ações o robô comprou em cada mês
- A coluna `dist_media_mst` na série de retornos — **Esse é o termômetro do filtro de regime!**

### O que você precisa fazer (por ordem de prioridade):

| # | Tarefa | Prioridade | Referência |
|---|---|---|---|
| 1 | Implementar o Filtro de Regime com escada de degraus (seção 4.3 acima) | 🔴 Crítica | Seção 2.7 do plano mestre |
| 2 | Calibrar os percentis no in-sample (2011-2018) e testar no out-of-sample (2019-2026) | 🔴 Crítica | Seção 4.4 acima |
| 3 | Testar sensibilidade: janela de 126 dias e/ou rebalanceamento trimestral para reduzir turnover | 🟡 Importante | Testes 1 e 7 da Parte 3.5 do plano |
| 4 | Rodar os 200 sorteios aleatórios e o equal-weight das 80 como benchmarks | 🟡 Importante | Seção 3.2 do plano |
| 5 | Quantificar o atraso do filtro em cada crise (quantos dias/meses demorou para reagir) | 🟢 Desejável | Seção 4.5 acima |

> **Lembrete Final:** O objetivo real não é "fazer o robô dar lucro a qualquer custo". É construir uma estratégia **honesta, bem fundamentada e que reconheça seus limites**. A banca do Itaú vai valorizar muito mais uma equipe que diz *"nosso modelo não bateu o CDI, mas eis exatamente o porquê e o que faríamos diferente"* do que uma que manipula números para parecer que ganhou.
