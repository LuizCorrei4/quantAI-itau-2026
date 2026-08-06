# ✅ RESOLVIDO (06/08/2026) — Validação do Universo de Dados

> **Status:** Fechado. As conclusões estão incorporadas na Parte 2.2.7 do
> [`plano_final_nexus.md`](plano_final_nexus.md) e a evidência bruta está em
> [`dados/processados/disponibilidade.csv`](../dados/processados/disponibilidade.csv).

## A pendência original

A validação empírica que motivou o pivô para "sobreviventes por liquidez" não tinha sido
suficientemente checada. Pelo menos um ticker citado como evidência de falha (`SOUZ3`) não
corresponde a um código real da B3 — o ticker da Souza Cruz é `CRUZ3` —, e outro (`VVAR3`) não
era caso de deslistagem, mas de troca de ticker. A decisão de pivotar para sobreviventes podia
ter sido tomada com evidência incompleta.

**Era exatamente isso que estava acontecendo.**

## O que foi feito

Construída a tabela de mapeamento pedida ([`src/nexus/historicos.py`](../src/nexus/historicos.py)):
113 tickers históricos com motivo de saída e sucessor. Somados aos 225 ativos das carteiras
vigentes de IBOV, IBXX, IBRA, SMLL e IGCX, os **317 códigos** foram testados um a um no yfinance
por [`scripts/01_universo.py`](../scripts/01_universo.py).

## O que foi descoberto

**1. Renomeação não é buraco de dados — 47 casos recuperados.**
O Yahoo reescreve o histórico completo sob o ticker sucessor. `BHIA3` (ex-VVAR3) tem dados desde
2010, `COGN3` (ex-KROT3) desde 2012, e o mesmo vale para MOTV3, AZZA3, ALOS3, DXCO3, AMER3,
PCAR3, TIMS3, VIVT3, YDUQ3, B3SA3, SUZB3, PRIO3, ENEV3 e RENT3. A premissa da v1.2 do plano
estava errada.

**2. Deslistagens reais confirmadas — mas parcialmente recuperáveis.**
`CRUZ3` (o ticker correto), BTOW3, KROT3, HGTX3 e VVAR3 de fato retornam vazio. Porém o Yahoo
preserva 19 séries encerradas, e **6 delas entram no universo do backtest** com presença longa:
FIBR3 (91 meses), BRPR3 (83), ELPL4 (81), VVAR11 (56), PRML3 (40) e OGXP3 (37).

**3. Buracos irrecuperáveis — 26 empresas, nomeadas.**
ABRE11, ALLL3, BISA3, CIEL3, CPLE5, CRDE3, CRUZ3, CTIP3, ELET6, ELPL3, ENBR3, GPCP3, IDNT3,
LINX3, MAGG3, MMXM3, MOSI3, MPLU3, NETC4, SEDU3, SGPS3, SMLE3, SQIA3, SSBR3, TAMM4, TCNO4.

## Consequência para o projeto

O universo deixou de ser "só sobreviventes". É **"universo de liquidez com séries mortas
recuperadas e buracos nomeados"** — posição bem mais defensável diante da banca. Um teste de
robustez adicional foi incluído no plano (item 10 da Parte 3.5): rodar o backtest com e sem as
6 séries encerradas, para medir o viés residual em vez de especular sobre ele.

## Lição registrada para a seção de IA do relatório

O erro original (`SOUZ3`) foi uma alucinação de identificador por IA generativa, aceita sem
verificação. **Nenhum código de ativo deve entrar no pipeline sem teste automático de
existência.** Essa lição está documentada na Parte 5.3 do plano como exemplo honesto de
limitação da ferramenta.
