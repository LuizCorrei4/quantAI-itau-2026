# TICKET-C06 — Out-of-sample cego (execução única)

**Prioridade:** 🔴 Crítica
**Estimativa:** 2h
**Critério afetado:** Backtest (15%) + Análise (15%) = **30% da nota**
**Entregável:** `scripts/17_out_of_sample.py`, `docs/14_out_of_sample.md`
**Depende de:** C02, C03, C04, C05 fechados

---

## Contexto

**O out-of-sample nunca foi rodado.** Varredura em `scripts/`: nenhum arquivo
referencia 2019, nenhum filtra datas acima de `2018-12-31`. Todo número publicado
pelo projeto — o Sharpe de +0,122, o p-value, a sensibilidade a custos, a batalha
dos filtros — é **in-sample**.

O plano-mestre reserva 91 meses (jan/2019 a jul/2026) para teste cego e registra
um compromisso explícito:

> *"Pacto de Integridade do Out-of-Sample: estamos absolutamente **proibidos** de
> testar qualquer coisa na base Out-Of-Sample até estarmos completamente certos da
> arquitetura final pelo In-Sample."*

O pacto foi cumprido. Agora ele precisa ser **executado** — um backtest sem
out-of-sample, num desafio julgado por rigor, é uma entrega pela metade.

## O que fazer

### Antes de rodar: travar por escrito

Criar `docs/PARAMETROS_TRAVADOS.md` **antes** de executar qualquer coisa, com:

| Parâmetro | Valor travado | Origem |
|---|---|---|
| Pool (Top N farness) | 20 | grid in-sample |
| SMA (L) | 150 | grid in-sample |
| Cap por ativo | 10% | CVM 175 / C05 |
| Percentil de regime | (de C05) | CV in-sample |
| Custo por perna | 5 bps | premissa |
| Janela de correlação | 63 pregões | literatura |

Commitar esse arquivo **antes** da execução. O timestamp do commit é a prova de que
os parâmetros não foram escolhidos depois de ver o resultado.

### Rodar uma vez

`scripts/17_out_of_sample.py` sobre jan/2019 – jul/2026, produzindo:

- **V3 (oficial)** — MST + SMA150 + cap
- **V3 + regime** — se C05 concluir que agrega
- **V4 (nulo pareado)** — 200 sorteios de pool aleatório + SMA150 + cap
- Benchmarks: CDI, Ibovespa, BOVA11

O V4 precisa acompanhar no OOS: sem ele, a comparação in-sample fica órfã justamente
no período que vale.

### Regra inegociável

> **Nenhum ajuste de parâmetro depois de olhar o out-of-sample.**

Se o resultado for ruim, o resultado ruim **é a entrega**. Uma queda de +0,122
in-sample para algo próximo de zero out-of-sample é o achado mais informativo que
este projeto pode produzir — e é exatamente o que a literatura de momentum prevê
quando o sinal é fraco. Maquiar isso é o único erro irrecuperável.

Sinal de alerta para a banca: um projeto cujo out-of-sample bate o in-sample sem
explicação levanta mais suspeita do que um que degrada honestamente.

## Critério de aceite

- [ ] `docs/PARAMETROS_TRAVADOS.md` commitado **antes** da execução do OOS
- [ ] Execução única, registrada com data/hora
- [ ] Comparação in-sample vs. out-of-sample lado a lado, mesma tabela de métricas
- [ ] V4 (nulo pareado) rodado também no OOS
- [ ] Gráfico de equity 2019-2026 vs. CDI e BOVA11
- [ ] Degradação in→out comentada com hipótese explicativa
