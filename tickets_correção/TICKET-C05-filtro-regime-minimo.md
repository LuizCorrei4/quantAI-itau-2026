# TICKET-C05 — Filtro de regime mínimo (1 parâmetro)

**Prioridade:** 🟡 Importante
**Estimativa:** 3h (time-box duro)
**Critério afetado:** Modelagem (20%)
**Entregável:** `src/nexus/regime.py`, `scripts/16_calibracao_regime.py`

---

## Contexto

O Filtro de Regime é a terceira camada da arquitetura anunciada em todos os
documentos do projeto — **e não existe no código.** Não há `src/nexus/regime.py`,
e nenhum script referencia contração da MST como sinal de crise.

É também a camada com a evidência empírica mais forte que o projeto tem:

> A correlação média entre as 80 ações fica entre **0,10 e 0,22** em períodos normais
> e salta para **0,595 em maio de 2020**.

Isso não é sutileza estatística — é um sinal grande, medido nos próprios dados da
equipe. E a métrica já está implementada:
[`calcular_distancia_media_mst`](../src/nexus/mst.py#L77) existe e já é gravada como
coluna `dist_media_mst` pelo backtest do MVP.

## O que fazer

### Escopo reduzido, deliberadamente

**Não implementar a escada de 3 degraus** descrita em `docs/04` (🟢 100% / 🟡 50% /
🔴 20%). São **dois** percentis a calibrar, em 91 meses de amostra, com o
out-of-sample já comprometido pelo prazo. Superfície de overfitting grande demais
para o retorno.

Versão mínima, **um parâmetro**:

```
Se dist_media_mst(t) < percentil_p(histórico até t-1):
    exposição em ações = 30%,  resto em CDI
Senão:
    exposição = 100% do que o cap já determinou
```

- O percentil é calculado sobre o histórico **expansível até t−1** — nunca sobre a
  série inteira (isso seria look-ahead).
- Calibrar `p ∈ {5, 10, 15, 20}` no in-sample, **reportar os quatro**, travar um.

### O teste que precisa acompanhar: redundância com o cap

O cap de 10% **já é** um mecanismo pró-cíclico de caixa: momentum falha → poucas
ações passam → capital vai para o CDI. É bem possível que o filtro de regime esteja
medindo a mesma coisa por outro caminho.

Rodar e reportar:

| Variante | Exposição média em caixa | Sharpe | MDD |
|---|---|---|---|
| V3 (cap, sem regime) | | | |
| V3 + regime | | | |
| V2 (sem cap) + regime | | | |

Se `V3 + regime ≈ V3`, o filtro é redundante — **e isso é um achado publicável**,
não um fracasso. Mostra que a equipe testou a interação entre as próprias camadas
em vez de empilhá-las e torcer.

### Enquadramento honesto

O filtro de regime é **instrumento de risco, não de alpha**. Ele pode legitimamente
não melhorar o retorno e ainda assim ser um sucesso, se cortar o drawdown. Declarar
isso no documento evita que ele seja julgado pela métrica errada.

Declarar também a limitação estrutural que o plano já reconhece (Parte 2.7): janela
trailing de 63 pregões avaliada uma vez por mês **reage depois do estrago** num
crash de dias como março de 2020. Quantificar o atraso, não escondê-lo.

## Critério de aceite

- [ ] `src/nexus/regime.py` com percentil expansível (zero look-ahead)
- [ ] Os quatro percentis testados aparecem no documento, não só o vencedor
- [ ] Tabela de redundância cap × regime preenchida
- [ ] Atraso de reação em março/2020 quantificado em meses
- [ ] Se redundante: dito com todas as letras
