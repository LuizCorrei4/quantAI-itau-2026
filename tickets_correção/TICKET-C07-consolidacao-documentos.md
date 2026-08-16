# TICKET-C07 — Consolidação dos documentos

**Prioridade:** 🔴 Crítica
**Estimativa:** 3h
**Critério afetado:** Análise (15%) + Conclusão (10%) + Uso de IA (15%)
**Depende de:** todos os anteriores

---

## Contexto

Depois de C01–C06, vários números publicados em `docs/03` a `docs/11` estarão
desatualizados ou contraditos. Este ticket alinha a documentação ao que os scripts
de fato produzem — e prepara o material das 5 páginas.

## O que corrigir, item a item

### 1. Números que mudam

| Documento | O que revisar |
|---|---|
| `docs/06` | substituído por `docs/13` (C02); marcar como superseded |
| `docs/07` | o Sharpe de +0,122 continua válido, mas passa a ser "máximo de um grid de 16" |
| `docs/08` | corrigir a contagem de meses (86 vs. 91 — ver C01) |
| `docs/09` | rever a afirmação de que o cap "reduziu o drawdown de −48,2% para −13,6%": parte disso é o momentum, não o cap. C03 separa os dois |
| `docs/10` | suavizar "margem de segurança de 2x a 3x" — é forte demais para um excesso de 1,8% a.a. |
| `docs/11` | manter; o relato do data leakage é o melhor material de IA do projeto |

### 2. Erro factual em `dados/resultados/README.md`

O arquivo afirma:

> *"Ativos com o **menor** Farness são os mais periféricos"*

Está invertido. Farness é a **soma das distâncias** até todos os outros nós — quanto
**maior**, mais afastado do miolo da rede. O código está certo
([`selecionar_top_n`](../src/nexus/portfolio.py#L43) ordena `ascending=False`); o
README é que está errado. Se essa frase vazar para o PDF, inverte a tese inteira.

### 3. Reivindicações a calibrar

| Afirmação atual | Problema |
|---|---|
| "superando com significância estatística" | depende do p corrigido de C02 |
| "Sharpe +0,122" apresentado como resultado da estratégia | é o **máximo de 16 combinações**, in-sample |
| "margem de segurança de mais de 2x a 3x o custo real" | o excesso sobre o CDI é de 1,8% a.a. |
| `docs/03`: "Turnover 67% (...) segurando posições por mais de um semestre" | 67% ao mês é o oposto de segurar por um semestre — a frase se contradiz |

### 4. A magnitude econômica precisa aparecer

Nenhum documento diz isto de forma direta:

> **12,1% a.a. contra 10,3% do CDI = 1,8% a.a. de excesso, com 14,9% de volatilidade.**

Declarar isso explicitamente é mais forte que omitir. Um avaliador experiente faz
essa conta em dez segundos; melhor que o número venha da equipe, com a leitura certa
ao lado, do que ele o descubra sozinho.

## A narrativa que os dados sustentam

Depois de C03 e C06, provavelmente haverá material para o arco abaixo — que é mais
interessante que a tese original, porque é contraintuitivo **e** medido:

> A MST é um **termômetro de regime** excelente e um **stock picker** fraco.

Evidência a favor: a correlação média vai de 0,13 a 0,595 em maio de 2020 (sinal
enorme, medido nos dados da equipe), enquanto a seleção por periferia entregou
Sharpe −0,21 sozinha.

E fecha um arco raro de honestidade intelectual, todo documentado:

```
Betweenness reprovada por degenerescência (41 de 80 empatadas em zero)
   → MVP topológico puro reprovado (Sharpe −0,21)
      → ML preditivo reprovado por Occam (+0,053 vs +0,122)
         → seleção por grafo demovida a filtro de universo [C03]
            → MST promovida a instrumento de risco [C05]
```

Quatro hipóteses da própria equipe mortas com evidência. Isso pontua em Conceito,
Análise, Conclusão **e** Uso de IA simultaneamente — mais do que um Sharpe de 0,122
que a banca vai testar em dez segundos.

## Critério de aceite

- [ ] Todo número em `docs/` rastreável a um script
- [ ] `dados/resultados/README.md` com a farness corrigida
- [ ] Contradição do turnover em `docs/03` resolvida
- [ ] Excesso de 1,8% a.a. declarado explicitamente
- [ ] `docs/06` marcado como superseded
- [ ] Esqueleto das 5 páginas com a narrativa escolhida
