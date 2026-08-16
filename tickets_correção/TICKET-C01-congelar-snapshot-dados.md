# TICKET-C01 — Congelar o snapshot de dados

**Prioridade:** 🔴 Crítica (bloqueia todos os outros tickets)
**Estimativa:** 1h (45 min disso é download)
**Critério afetado:** Backtest (15%) — reprodutibilidade

---

## Contexto

`dados/processados/*.parquet` está no `.gitignore`. Quem clonar o repositório não
tem os dados, e precisa rodar `scripts/01` a `04` para regerá-los.

O problema é o alerta que o próprio plano-mestre registra (Parte 2.2.0):

> *"O Yahoo revisa dados retroativamente e as carteiras da B3 mudam a cada
> quadrimestre. Rodar numa data futura produz arquivos ligeiramente diferentes.
> Todos os números deste plano são da coleta de 06/08/2026."*

Ou seja: **regerar os dados hoje muda todos os números já publicados em `docs/03`
a `docs/11`.** Se parte dos números do PDF vier da coleta de 06/ago e parte de uma
coleta de 15/ago, o relatório fica internamente inconsistente — e é o tipo de
inconsistência que uma banca detecta somando uma coluna.

## O que fazer

1. **Uma única regeração**, na máquina de quem vai executar os tickets:

   ```bash
   python scripts/01_universo.py
   python scripts/02_baixar_precos.py
   python scripts/03_baixar_cdi_ibov.py
   python scripts/04_montar_datasets.py
   python scripts/05_validar_dados.py
   ```

2. **Congelar.** Copiar `dados/processados/` inteiro para um backup fora da árvore
   de trabalho. Nenhum script depois de C01 pode rodar `01`–`04` de novo.

3. **Registrar a proveniência** em `dados/processados/SNAPSHOT.md`:
   - data e hora da coleta;
   - `python scripts/05_validar_dados.py` — colar a saída;
   - contagem de pregões, de tickers e de rebalanceamentos;
   - primeira e última data do painel.

4. **Re-rodar todo o downstream a partir desse snapshot** — `07`, `08`, `10`, `11`,
   `12`, `13`. Os números de `docs/03` a `docs/11` passam a valer para o snapshot novo.

## Armadilha conhecida

Existe uma divergência de contagem que precisa ser resolvida aqui, não depois:

- O plano diz que o in-sample vai de **mai/2011 a dez/2018**, o que dá
  **92 datas de rebalanceamento** (91 meses de retorno).
- `docs/08_batalha_dos_filtros_alpha.md` afirma **"Novembro/2011 a Dezembro/2018 —
  86 meses"**.

`08_backtest_alpha.py` monta as datas com
`[d for d in datas_rebalanceamento if d <= pd.Timestamp('2018-12-31')]` e itera até
`len(datas_in_sample) - 1`, o que deveria dar 91 meses, não 86. Uma das duas
afirmações está errada.

Além disso, o filtro de momentum retorna `[]` enquanto houver menos de `L=150`
pregões de histórico ([`alpha_filters.py:63`](../src/nexus/alpha_filters.py#L63)).
Com dados começando em 03/01/2011, os rebalanceamentos de **mai, jun, jul e ago/2011
são 100% CDI por construção** — não por decisão da estratégia. Isso infla o Sharpe
inicial e precisa estar declarado.

## Critério de aceite

- [ ] `dados/processados/SNAPSHOT.md` existe e traz a saída do script `05`
- [ ] Backup do snapshot feito fora da árvore de trabalho
- [ ] Número real de meses in-sample apurado e anotado (91? 86? outro?)
- [ ] Número de meses iniciais forçados a 100% CDI pelo warmup da SMA apurado
- [ ] Scripts `07`, `08`, `10`, `13` re-rodados sobre o snapshot congelado
