# TICKET-C03 — Tabela de atribuição (ablação por camada)

**Prioridade:** 🔴 Crítica — **maior retorno por hora do projeto inteiro**
**Estimativa:** 4-5h
**Critério afetado:** **Conceito (20%)** e Análise (15%)
**Entregável:** `scripts/14_ablacao_atribuicao.py`, `docs/12_ablacao_e_atribuicao.md`

---

## Contexto

O plano-mestre define este teste na Parte 2.5.4 e o classifica assim:

> *"Esta é a pergunta que a banca vai fazer: **'por que precisa de grafo?'** Se um
> cálculo trivial produzir a mesma carteira, a MST é enfeite. (...) Este é o teste
> mais importante do projeto para o critério de Conceito (20%)."*

**Ele nunca foi rodado.** Nenhum script compara a seleção por farness contra um
pool alternativo sob condições idênticas.

Sem ele, o projeto afirma um Sharpe de +0,122 sem saber qual das três camadas o
produziu — topologia, momentum ou colchão de caixa. As três foram introduzidas
juntas e medidas juntas.

## O que fazer

Um script que roda o mesmo loop mensal in-sample para 7 variantes, com todos os
parâmetros travados (Pool=20, SMA=150, cap=10%, custo=5 bps/perna):

| # | Pool (onde olhar) | Momentum | Cap/caixa | O que isola |
|---|---|---|---|---|
| **V0** | 80 do universo | — | — | piso de mercado (equal-weight total) |
| **V1** | MST top-20 farness | — | cap 10% | topologia pura, sem direção |
| **V2** | MST top-20 farness | SMA 150 | **sem cap** (renormaliza p/ 100%) | momentum **sem** colchão de caixa |
| **V3** | MST top-20 farness | SMA 150 | cap 10% | **variante oficial** |
| **V4** | **20 aleatórias × 200 sorteios** | SMA 150 | cap 10% | **contribuição da MST** |
| **V5** | 20 de menor correlação média | SMA 150 | cap 10% | controle sem grafo (plano 2.5.4) |
| **V6** | 20 de menor \|beta\| vs. IBOV | SMA 150 | cap 10% | controle sem grafo (plano 2.5.4) |

### As três leituras que a tabela produz

| Comparação | Mede | Se der ≈ 0 |
|---|---|---|
| **V3 − V4** | contribuição da MST | a topologia não seleciona alpha |
| **V3 − V2** | contribuição do colchão de caixa | o cap é o que gerou o Sharpe |
| **V3 − V1** | contribuição do momentum | o filtro direcional não agrega |

**V3 vs. V4 é o teste central.** Se o V3 cair dentro do intervalo interquartil da
distribuição do V4, a MST não contribui para a seleção — e isso precisa ser
descoberto agora, não na pergunta da banca.

### Detalhes de implementação

- **Uma única MST por mês**, reaproveitada por todas as variantes (o loop de
  `10_grid_search_alpha.py` já faz isso).
- **Correlação média** por ativo sai da própria matriz já calculada:
  `(corr.sum(axis=1) - 1) / (n - 1)`.
- **Beta** vs. IBOV: `cov(r_i, r_ibov) / var(r_ibov)` na mesma janela de 63 pregões,
  usando a coluna `ret_ibov` de `benchmarks.parquet`.
- **V2 renormaliza:** `pesos = 1/M` para as M aprovadas, somando sempre 100%. Se
  M=0, fica 100% CDI (não há alternativa).
- **V4 usa seed fixo por trajetória** (`rng = np.random.default_rng(1000 + k)`) para
  ser reproduzível.
- Salvar a série de retornos de cada variante em `dados/resultados/ablacao/`.

## Critério de aceite

- [ ] Tabela com as 7 variantes: CAGR, vol, Sharpe geométrico e clássico, MDD, turnover, % médio em caixa
- [ ] Percentil do V3 dentro da distribuição do V4 explicitamente reportado
- [ ] As três diferenças (V3−V4, V3−V2, V3−V1) calculadas e comentadas
- [ ] Histograma do V4 com V3, V5 e V6 marcados
- [ ] Séries salvas em `dados/resultados/ablacao/`
- [ ] **O documento reporta o resultado que saiu**, favorável ou não à tese
