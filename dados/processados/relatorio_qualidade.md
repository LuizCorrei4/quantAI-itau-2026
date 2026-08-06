# Relatório de Qualidade dos Dados — Robô Nexus

Gerado a partir de `dados/processados/`. Período coletado: 2011-01-03 a 2026-08-05.

## 1. Calendário de pregão

- Pregões no painel: **3875** (2011-01-03 a 2026-08-05)
- Pregões na série do Ibovespa: **3866**
- Datas no painel ausentes no IBOV: 9
- Datas no IBOV ausentes no painel: 0

A convergência com o calendário do Ibovespa valida o filtro de datas fantasma (feriados da B3 em que o Yahoo publica cotação para poucos tickers).

## 2. Retornos diários

- Observações válidas: **945,500**
- Média: -0.00009 | Desvio padrão: 0.0305
- Assimetria: 0.11 | Curtose: 24.8
- Retornos com |r| > 25%: 734 (0.0776% das observações)

Caudas gordas (curtose alta) são a norma em retornos diários de ações e não indicam erro de dados. Tickers concentrando extremos:

| Ticker | Nº de retornos > 25% |
|---|---|
| RCSL4 | 110 |
| VIVR3 | 81 |
| OGXP3 | 33 |
| PDGR3 | 29 |
| CTAX3 | 23 |
| LUPA3 | 20 |
| OIBR3 | 17 |
| CEDO4 | 16 |

## 3. Universo mensal (80 mais líquidas)

- Rebalanceamentos: **184** (2011-05-02 a 2026-08-03)
- Ações por rebalanceamento: 80 a 80
- Tickers distintos que já passaram pelo universo: **157**
- Empresas distintas (radical de 4 letras): **156**
- Renovação média do universo: **1.7 ações/mês** (2.2%)
- Renovação máxima num único mês: 5 ações

A renovação do universo é do *filtro de liquidez*, não da carteira. O turnover da carteira do Nexus é medido separadamente no backtest.

## 4. Survivorship bias — o que temos e o que falta

O universo tem **157** tickers distintos ao longo de 184 rebalanceamentos. Destes, **6** são séries que terminam antes do último pregão (2026-08-05) — ou seja, empresas que saíram da bolsa e cujo histórico está preservado no backtest.

**Séries encerradas presentes no universo:**

| Ticker | Empresa | Fim da série | Meses no universo |
|---|---|---|---|
| PRML3 | Prumo Logística | 2018-03-09 | 40 |
| ELPL4 | Eletropaulo | 2018-03-12 | 81 |
| VVAR11 | Via Varejo units | 2018-11-23 | 56 |
| FIBR3 | Fibria | 2019-01-02 | 91 |
| OGXP3 | OGX Petróleo | 2019-01-10 | 37 |
| BRPR3 | BR Properties | 2024-08-06 | 83 |

**Buracos remanescentes (26 empresas):** códigos deslistados sem ticker sucessor e sem dados no Yahoo Finance. São a parcela irrecuperável do viés de sobrevivência com fontes gratuitas:

> ABRE11, ALLL3, BISA3, CIEL3, CPLE5, CRDE3, CRUZ3, CTIP3, ELET6, ELPL3, ENBR3, GPCP3, IDNT3, LINX3, MAGG3, MMXM3, MOSI3, MPLU3, NETC4, SEDU3, SGPS3, SMLE3, SQIA3, SSBR3, TAMM4, TCNO4

**Casos de renomeação não são buraco.** O Yahoo reescreve o histórico completo sob o ticker sucessor — verificado empiricamente para BHIA3 (ex-VVAR3, dados desde 2010), COGN3 (ex-KROT3), MOTV3 (ex-CCRO3), AZZA3 (ex-ARZZ3), DXCO3 (ex-DTEX3), PCAR3, TIMS3, VIVT3, YDUQ3, B3SA3 e AMER3. Ver `dados/processados/disponibilidade.csv`.

## 5. Benchmarks e taxa livre de risco

| Série | Obs. | Acumulado | Anualizado | Vol. anualizada |
|---|---|---|---|---|
| Ibovespa | 3866 | 2.54x | 6.16% | 23.24% |
| BOVA11 | 3874 | 2.52x | 6.12% | 23.53% |
| CDI | 3916 | 4.34x | 9.87% | — |

Período de referência: 2011-01-03 a 2026-08-05 (15.6 anos).

## 6. Checagem de look-ahead na formação do universo

- Ações selecionadas sem nenhum dado na janela anterior à decisão: **0**
- A janela de liquidez usa exclusivamente pregões com índice `< data_rebalanceamento`.
- O ranking de liquidez usa `Close` e `Volume` brutos do passado, nunca ajustados por eventos posteriores em quantidade de ações.
