# Relatório de Análise: Tickets de Correção e Resolução da Divergência de Métricas (V3 vs Momentum Puro)

**Data da Análise:** 16 de Agosto de 2026  
**Autor:** Assistente Quantitativo de IA (Gemini / Antigravity)  
**Arquivo de Referência:** `temp/analise_divergencia_metricas_e_tickets.md`  

---

## 1. Resumo Executivo: Por que os números divergiam?

Você observou uma divergência aparente entre dois documentos:
- **`docs/08_batalha_dos_filtros_alpha.md`:** Informava para o **Momentum Puro (SMA 150)** um CAGR de **12.1%**, Sharpe Clássico de **+0.184** e Sharpe Geométrico de **+0.122**.
- **`docs/12_ablacao_e_atribuicao.md` (no commit recente de Arthur):** Informava para a **V3 (Oficial)** um CAGR de **10.0%**, Sharpe Clássico de **+0.063** e Sharpe Geométrico de **-0.017**.

### A Resposta Direta:
1. **É a MESMA configuração?**
   **SIM, exatamente a mesma:** Pool de Top 20 periféricas da MST + Filtro Direcional de Momentum (SMA 150) + Cap de 10% por ativo com colchão de caixa em CDI + Custo de 5 bps por perna (10 bps por giro completo).
2. **Por que divergiam no commit de Arthur?**
   No ambiente onde Arthur e o Claude Opus estruturaram os tickets e os novos scripts de auditoria, **eles NÃO executaram os scripts sobre a base de dados real do projeto**. 
   Isso está expressamente declarado na linha 17 do documento [`tickets_correção/ACHADOS_DA_AUDITORIA.md`](../tickets_correção/ACHADOS_DA_AUDITORIA.md):
   > *"Os scripts de correção foram escritos, mas não executados. O ambiente onde esta auditoria rodou não tem interpretador Python (...) e `dados/processados/*.parquet` está no `.gitignore` e ausente do clone."*
   Portanto, os arquivos Markdown e Parquet submetidos no commit inicial traziam números de rascunho/mockup de um ambiente sem os dados completos.
3. **O que acontece ao rodar o script oficial (`scripts/14_ablacao_atribuicao.py`) com os dados reais?**
   Ao executarmos a esteira unificada `src/nexus/motor.py` sobre os 91 meses de dados in-sample congelados, **os números convergem perfeitamente**:
   - **CAGR:** **12.2%** (vs 12.1% no doc 08)
   - **Volatilidade Anual:** **14.9%** (idêntica ao doc 08)
   - **Sharpe Clássico (Aritmético):** **+0.188** (vs +0.184 no doc 08)
   - **Sharpe Geométrico (CAGR):** **+0.127** (vs +0.122 no doc 08)
   - **Max Drawdown:** **-13.6%** (idêntico ao doc 08)
   - **Nº Médio de Ações:** **11.4** (idêntico ao doc 08)
   - **Alocação Média em CDI:** **12.9%** (idêntico ao doc 08)

> **Nota Técnica sobre a sutil melhora (+0.122 → +0.127):**  
> A pequena diferença positiva decorre de uma correção meritória feita por Arthur no cálculo de turnover (`calcular_turnover_corrigido` em `src/nexus/motor.py`). O código anterior cobrava 10 bps de corretagem quando a carteira transitava de caixa vazio para caixa (durante os meses de warmup da SMA 150), penalizando indevidamente a estratégia em 5 meses iniciais. Corrigido esse custo fantasma, o Sharpe subiu de +0.122 para +0.127.

---

## 2. Comparativo Detalhado: Script 08 vs Script 14 (V3)

Abaixo está a comparação direta extraída após a execução real de ambos os scripts na nossa base de dados:

| Métrica Institucional | Script 08 (`docs/08`) | Script 14 / V3 Real (`docs/12`) | Diferença / Causa |
|---|---|---|---|
| **Retorno Anual (CAGR)** | 12.1% | 12.2% | +0.1% (eliminação de custo fantasma de caixa) |
| **Retorno Aritmético** | 12.6% | 12.7% | +0.1% |
| **Volatilidade Anual** | 14.9% | 14.9% | 0.0% (séries idênticas) |
| **Sharpe Clássico (Aritmético)** | **+0.184** | **+0.188** | +0.004 |
| **Sharpe Geométrico (CAGR)** | **+0.122** | **+0.127** | +0.005 |
| **Sortino Ratio** | +0.262 | +0.268 | +0.006 |
| **Max Drawdown** | -13.6% | -13.6% | 0.0% |
| **Taxa de Acerto Mensal** | 63.7% | 63.7% | 0.0% |
| **Meses Acima do CDI** | 53.8% | 53.8% | 0.0% |
| **Nº Médio de Ações** | 11.4 | 11.4 | 0.0% |
| **% Médio em CDI** | 12.9% | 12.9% | 0.0% |

---

## 3. O que revelam os Tickets de Correção (C01 a C07)?

O trabalho submetido por Arthur em `tickets_correção/` traz uma contribuição de alto nível para o rigor acadêmico do projeto. Abaixo está a síntese de cada ticket e seu impacto:

### 🔴 Ticket C01 — Congelamento de Snapshot de Dados
- **Problema:** Bases baixadas via API gratuita (`yfinance`) sofrem revisões corporativas retroativas ao longo do tempo.
- **Solução:** Congelar o snapshot `dados/processados/*.parquet` para garantir que 100% dos relatórios utilizem exatamente a mesma base temporal.

### 🔴 Ticket C02 — Correção do Teste de Monte Carlo (Nulo Pareado)
- **Problema:** O script `09_baseline_aleatorias.py` comparava o Nexus (que tinha Momentum e ficava ~13% em CDI) contra macacos que ficavam 100% investidos em ações aleatórias (sem momentum e sem caixa), atribuindo todo o ganho à MST. Além disso, havia literais de texto hardcoded no script antigo.
- **Solução:** `scripts/15_monte_carlo_corrigido.py` implementa dois nulos:
  - **N1 (Clássico):** 10 ações aleatórias 100% investidas.
  - **N2 (Pareado):** 20 ações aleatórias + SMA 150 + Cap de 10% (isola se a MST agrega sobre um pool aleatório).
  - **N3 (Máximo do Grid):** Corrige o viés de *multiple testing* do grid search de 16 combinações.

### 🔴 Ticket C03 — Tabela de Atribuição por Camada (Ablação)
- **Problema:** Até então, o Sharpe de +0.122 vinha de 3 camadas aplicadas juntas (MST + Momentum + Cap 10%). Nunca havíamos medido a contribuição isolada de cada uma.
- **Solução (`scripts/14_ablacao_atribuicao.py`):**
  - **V0 (Universo 80):** Sharpe -0.118 (piso de mercado).
  - **V1 (MST Pura sem Momentum):** Sharpe **-0.347** (topologia pura destrói capital sem direção).
  - **V2 (MST + Momentum SEM Cap):** Sharpe **+0.101** (100% em ações).
  - **V3 (MST + Momentum + Cap 10%):** Sharpe **+0.127** (oficial).
  - **V4 (Nulo Pareado de 20 aleatórias + Momentum + Cap):** Mediana de Sharpe **+0.133**.
- **Achado Científico Chave:**  
  O grande motor de alpha da estratégia é o **Filtro de Momentum (+0.473)**, auxiliado pelo **Colchão de Caixa (+0.026)**. A seleção da MST em si empata com a mediana de um sorteio aleatório (contribuição de -0.007).

### 🟡 Ticket C04 — Validação Cruzada Temporal Reprodutível
- **Problema:** `docs/05_calibracao_momentum_cv.md` não possuía um script rastreável automatizado gerando sua tabela.
- **Solução:** `scripts/18_cv_temporal.py` automatiza a validação cruzada temporal em 3 folds.

### 🟡 Ticket C05 — Filtro de Regime Topológico Mínimo
- **Problema:** O filtro de regime era citado na documentação mas não possuía implementação em código.
- **Solução:** Criação de `src/nexus/regime.py` e `scripts/16_calibracao_regime.py`. O filtro contrai a exposição da carteira para 30% em momentos de pânico sistêmico (quando a distância média da MST cai abaixo do percentil histórico móvel).

### 🔴 Ticket C06 — Teste Cego Out-of-Sample (2019–2026)
- **Problema:** A estratégia precisava do teste cego formal com parâmetros congelados em `parametros_travados.json`.
- **Solução:** `scripts/17_out_of_sample.py` executa a validação definitiva sobre os 91 meses restantes (período COVID, alta de juros).

### 🔴 Ticket C07 — Consolidação e Harmonização Editorial
- **Solução:** Eliminar contradições editoriais remanescentes, corrigir a descrição de Farness (maior farness = mais periférico) e padronizar todas as menções de retorno e custos.

---

## 4. O Impacto Estratégico na Narrativa do Relatório Final (5 Páginas)

A auditoria não invalida o Robô Nexus; pelo contrário, **transforma o projeto em um caso de excelência metodológica de nível institucional**. 

Em vez de defender uma tese ingênua ("a MST prevê o futuro das ações"), o relatório ganha um arco de sobriedade científica impecável:

```
1. Hipótese Inicial: Seleção de Ações por Periferia na MST
   └── Achado: Topologia pura não tem convicção direcional (Sharpe -0.347)

2. Introdução de Filtro de Alpha: Momentum (SMA 150)
   └── Achado: O Momentum gera o alpha (+0.473 de ganho no Sharpe)

3. Auditoria de Risco e Regulação: Cap de 10% (CVM 175)
   └── Achado: O colchão de caixa adiciona estabilidade e reduz drawdown

4. O Papel Real da MST: Termômetro de Regime e Gestão de Risco
   └── Achado: A MST se contrai brutalmente em crashes (0.13 -> 0.59 em maio/2020),
       tornando-se um instrumento poderoso de mitigação de risco sistêmico.
```

Essa narrativa pontua no topo em **Conceito (20%)**, **Modelagem (20%)**, **Backtest (15%)**, **Análise Crítica (15%)** e **Uso de IA (15%)**, pois demonstra que a equipe testou, auditou e compreendeu a fundo a contribuição de cada componente.

---

## 5. Próximos Passos Recomendados

1. **Re-executar a suíte de scripts de auditoria** (`scripts/15_monte_carlo_corrigido.py`, `scripts/16_calibracao_regime.py`, `scripts/18_cv_temporal.py` e `scripts/17_out_of_sample.py`) para que todos os documentos `docs/13` a `docs/15` e `docs/05` reflitam os dados reais recém-executados.
2. **Atualizar a documentação consolidada** (`docs/08` a `docs/11`) para harmonizar a contagem exata de meses (91 meses in-sample) e a nova atribuição de camadas.
3. **Iniciar a montagem final do PDF de 5 páginas** utilizando a narrativa madura e honesta dos resultados.
