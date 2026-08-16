# TICKET-C04 — CV temporal reprodutível (ou remoção de `docs/05`)

**Prioridade:** 🟡 Importante
**Estimativa:** 2h
**Critério afetado:** Backtest (15%)
**Entregável:** `scripts/18_cv_temporal.py` reescrevendo `docs/05_calibracao_momentum_cv.md`

---

## Contexto

`docs/05_calibracao_momentum_cv.md` publica esta tabela:

| Variante | Fold 1 (2011–2014) | Fold 2 (2014–2016) | Fold 3 (2016–2018) | In-sample total |
|---|---|---|---|---|
| SMA 150 | −0,05 | **+0,62** | **+0,68** | **+0,122** |

Três problemas:

1. **Nenhum script gera este arquivo.** Varredura em `scripts/`: o `06` escreve em
   `docs/`, o `07` escreve `resumo_backtest_mvp.md`, o `09` escreve `docs/06`, o `10`
   escreve `docs/07`, o `08` escreve `docs/08`. Ninguém escreve `docs/05`.

2. **Os números não fecham.** Dois folds a +0,62 e +0,68, um a −0,05, e o total
   in-sample dá +0,122. Sharpe não agrega linearmente, mas a distância é grande
   demais para ser efeito de composição: uma média ponderada por duração daria algo
   próximo de +0,37.

3. **Os folds não são os do plano.** A Parte 3.1.1 especifica janela expansível com
   treino e validação separados (treino 2011-2014 → valida 2015-2016, etc.). A tabela
   publica três sub-períodos contíguos, que é outra coisa.

Uma tabela não reproduzível dentro de um relatório julgado por rigor metodológico é
um risco assimétrico: ganha pouco se ninguém olhar, perde muito se alguém puxar o fio.

## O que fazer

**Decisão binária — as duas saídas são aceitáveis:**

### Opção A (preferida, se houver tempo): gerar de verdade

`scripts/18_cv_temporal.py` que roda o grid Pool × SMA nos folds do plano:

```
Fold 1: valida 2015-2016
Fold 2: valida 2016-2017
Fold 3: valida 2017-2018
```

Como o filtro de momentum **não tem parâmetros ajustados por treino** (é uma regra
binária: preço > SMA), "treinar" aqui significa apenas *escolher L e Pool*. Então o
que a CV mede é: **o L vencedor é o mesmo nos três folds de validação?**

O critério do plano (Parte 3.1.1) é explícito:

> *"Se cada fold elege um L diferente → o sinal é fraco e deve ser reportado honestamente."*

### Opção B (se o tempo apertar): apagar

Deletar `docs/05_calibracao_momentum_cv.md` e remover as referências a ele. Um
documento a menos é infinitamente melhor que um documento com números órfãos.

## Critério de aceite

- [ ] Ou `docs/05` é gerado por script, ou `docs/05` não existe mais
- [ ] Se gerado: o L vencedor de cada fold aparece explicitamente
- [ ] Se gerado: reportar se o vencedor é estável ou muda por fold
- [ ] Nenhuma referência pendente a `docs/05` em outros arquivos
