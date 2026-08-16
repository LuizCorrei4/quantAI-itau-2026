# Contexto de Transição: Estado Consolidado do Projeto Nexus, Auditorias, Caderno de Resultados e Roteiro de Finalização

**Data de Atualização:** 16 de Agosto de 2026 (Reta Final do Desafio)  
**Status Global:** Pós-Auditoria Metodológica, Ablação por Camadas (V0 a V6), Caderno de Resultados Empíricos (`notebooks/nexus_resultados.ipynb`) e Preparação do Relatório Final (PDF 5 Páginas)  
**Objetivo deste Documento:** Servir como o **guia-mestre e memória institucional completa** para a próxima sessão de trabalho com LLM/Agente, reunindo o histórico, todas as vulnerabilidades mapeadas, os achados empíricos do notebook e as diretrizes de entrega.

---

## 1. Onde Estamos: Linha do Tempo e Evolução do Projeto

O projeto **Robô Nexus** (Desafio Itaú Asset Quant AI 2026) passou por ciclos profundos de amadurecimento científico:

1. **Fase 1 — MVP Topológico Puro:** A seleção de ações periféricas via MST (*Farness*) isoladamente gerou Sharpe negativo (-0.21) e turnover excessivo (67%).
2. **Fase 2 — Filtros de Alpha & Veredito de Occam:** 
   - Adicionamos a camada de **Momentum (SMA 150)** e testamos modelos de **Machine Learning** (Regressão Logística, Random Forest, XGBoost).
   - O ML foi auditado com esteira *Walk-Forward Expanding Window* (eliminando o *data leakage* temporal do treinamento estático) e com hiperparâmetros limitados para evitar *overfitting* de ruído.
   - **Resultado:** A Cascata com ML entregou Sharpe In-Sample de **0.053**, enquanto o **Momentum Puro (SMA 150)** entregou Sharpe In-Sample de **+0.122** (CAGR 12.1%, Vol 14.9%, Max DD -13.6%). Pela **Navalha de Occam**, o ML preditivo foi descartado da execução final.
   - Foi introduzida a **Regra do CAP de 10% por ativo (Resolução CVM 175)**, com a sobra de capital alocada em CDI.
3. **Fase 3 — Auditoria e Caderno de Resultados do Arthur (Commit `a066865`):**
   - Criação do módulo `src/nexus/motor.py` (motor de simulação centralizado), `src/nexus/regime.py` (filtro de regime topológico) e novos scripts (`scripts/14` a `18`).
   - Execução completa da bateria de testes no caderno Jupyter `notebooks/nexus_resultados.ipynb` cobrindo ablação, nulos pareados, estabilidade de CV temporal, filtro de regime e o teste cego *Out-of-Sample* (2019–2026).

---

## 2. A Descoberta Chave da Auditoria: Por Que os Números Divergiam?

A equipe de auditoria investigou a fundo as discrepâncias entre relatórios anteriores e a re-execução dos scripts:

### O Mistério Resolvido: Correção de Turnover e Efeito *Data Vintage*
- **Ajuste de Custos (Turnover Caixa→Caixa):** O motor unificado corrigiu um bug em `calcular_turnover` que cobrava corretagem de 10 bps mesmo em meses consecutivos de caixa 100% em CDI. Essa correção elevou o Sharpe In-Sample do V3 de **+0.122 para +0.127** (CAGR 12.2%, Vol 14.9%, Max DD -13.6%).
- **Efeito Data Vintage:** Re-coletas retroativas via `yfinance` ajustam dividendos de anos passados e alteram marginalmente rankings de liquidez, mudando a MST e gerando oscilações de Sharpe (de +0.127 para -0.017 no vintage alternativo).
- **A Solução Definitiva:** Congelamento obrigatório dos hashes SHA-256 no manifesto `dados/CHECKSUMS.sha256` e validação mecânica em `src/nexus/motor.py`.

---

## 3. Os 7 Grandes Achados Empíricos Consolidados

A bateria unificada de simulações e auditoria sintetiza o projeto em 7 eixos:

### 📌 Achado 1 — Integridade e Congelamento dos Dados
O snapshot canônico foi congelado com hashes SHA-256 e validação mecânica em `parametros_travados.json`, eliminando qualquer oscilação espúria por revisões da API do Yahoo Finance.

### 📌 Achado 2 — Ablação por Camadas: De Onde Vem o Retorno?
Isolando cada componente no In-Sample (91 meses, `docs/12_ablacao_e_atribuicao.md`):
- **V0 (Universo 80):** Sharpe **-0.118** | CAGR 7.9% | MDD -39.1%
- **V1 (MST Top-20 SEM Momentum):** Sharpe **-0.347** | CAGR 3.9% | MDD -44.4% (topologia pura destrói capital)
- **V2 (MST Top-20 + Momentum SEM Cap):** Sharpe **+0.101** | CAGR 12.0% | MDD -14.2%
- **V3 (Oficial: MST + Momentum + Cap 10%):** Sharpe **+0.127** | CAGR 12.2% | MDD -13.6%
- **V4 (Nulo Pareado de 20 aleatórias + Mom + Cap):** Mediana de Sharpe **+0.133** (p95 = +0.428)
- **Atribuição:**
  - Contribuição do **Momentum:** **+0.473** (o motor essencial de retorno direcional).
  - Contribuição do **Colchão de Caixa (Cap 10%):** **+0.026** (estabilidade de cauda).
  - Contribuição da **MST:** **-0.007** (empata com a mediana de um sorteio aleatório, percentil 49%).
- **Conclusão:** A seleção por MST empata estatisticamente com um sorteio aleatório pareado. Além disso, o controle sem grafo "Menor Correlação Média" (**V5**) entregou Sharpe de **+0.274** (CAGR 14.2%, MDD -12.3%, Turnover 35.2%), demonstrando que o estimador direto de correlação sofre menos com o ruído de estimação da MST.

### 📌 Achado 3 — Monte Carlo Rigoroso (Três Nulos)
O Sharpe da estratégia oficial foi submetido aos 3 testes de significância (`docs/13_monte_carlo_corrigido.md`):
1. **N1 (Macaco Clássico 100% ações):** Sharpe Mediana = **-0.196** | p-value = **8.0%**
2. **N2 (Nulo Pareado com Momentum e Cap):** Sharpe Mediana = **+0.133** | p-value = **51.0%** (Percentil 49%)
3. **N3 (Máximo do Grid Search corrigindo Multiple Testing):** Sharpe Mediana = **+0.341** | p-value = **96.0%**
- **Conclusão:** Quando o nulo recebe as mesmas regras de momentum e caixa do tratamento, a MST não apresenta significância estatística sobre o sorteio aleatório (p = 51%).

### 📌 Achado 4 — Validação Cruzada Temporal: Instabilidade dos Parâmetros
Ao testar a estabilidade do par (Pool, SMA) nos 3 folds temporais expansíveis (`docs/05_calibracao_momentum_cv.md`):
- **Fold 1:** Melhor no treino (25, 150) valida com Sharpe **-0.380**.
- **Fold 2:** Melhor no treino (20, 150) valida com Sharpe **+0.733**.
- **Fold 3:** Melhor no treino (10, 100) valida com Sharpe **-0.141**.
- **Conclusão:** O par vencedor varia a cada ciclo, refletindo regimes macroeconômicos distintos.

### 📌 Achado 5 — Filtro de Regime: Comportamento no In-Sample
A contração da distância média da MST foi calibrada com percentil expansível (`docs/15_filtro_regime.md`):
- O percentil 10% (*p10*) melhorou o Sharpe de **+0.127 para +0.195** (CAGR 13.2%, MDD -13.6%).
- O ganho apoiava-se em **5 meses de acionamento** (5.5% do tempo), funcionando como mitigador pontual de choque sistêmico.

### 📌 Achado 6 — Teste Cego Out-of-Sample (2019–2026 — 91 meses)
O teste cego definitivo com parâmetros travados (`docs/14_out_of_sample.md`):
- **CDI no período:** Rendimento de **9.4% a.a.** (MDD 0.0%)
- **Ibovespa / BOVA11:** Rendimento de **9.2% a 9.5% a.a.** (MDD -40.3%)
- **Nexus V3 (MST Oficial):** CAGR de **0.0% a.a.** | Vol de **22.0%** | Sharpe **-0.427** | Max Drawdown **-43.1%**
- **Nexus V3 + Regime:** CAGR de **1.7% a.a.** | Vol de **20.5%** | Sharpe **-0.378** | Max Drawdown **-43.0%**
- **Nexus V5 (Menor Corr. Média):** CAGR de **9.7% a.a.** | Vol de **21.6%** | Sharpe **+0.014** | Max Drawdown **-35.6%** | Percentil no Nulo = **100.0%**
- **Nexus V5 + Regime (Completo):** CAGR de **9.5% a.a.** | Vol de **19.5%** | Sharpe **+0.005** | Max Drawdown **-35.6%**
- **Diagnóstico:** A variante baseada na MST (V3) sofreu com turnover excessivo (57.3%) decorrente do *pruning* de 97.5% das arestas. A variante **Nexus V5 (Menor Correlação)** superou o CDI e o Ibovespa no OOS, enquanto o **Filtro de Regime Topológico** reduziu a volatilidade em **-2.1 p.p.** durante a crise.

### 📌 Achado 7 — Síntese: O Arco Completo de Falsificação Científica
O projeto produziu um caso exemplar de **Falsificação Científica e Honestidade Intelectual**:

```
Betweenness reprovada por degenerescência (41 de 80 nós empatados em zero)
   └─> MVP topológico puro reprovado (Sharpe −0,347)
        └─> ML preditivo descartado por Occam (+0,053 vs +0,127 do momentum simples)
             └─> Correção de turnover consolida Sharpe In-Sample (+0,127)
                  └─> MST empata com nulo pareado (percentil 49% / p-value 51%)
                       └─> Menor Correlação Média supera MST com 20 p.p. menos turnover
                            └─> OOS Cego revela a divisão de trabalho perfeita:
                                 • Micro (Seleção): Menor Corr. Média bate CDI (9,7% a.a., p100% no nulo)
                                 • Macro (Risco): Regime MST corta volatilidade (-2,1 p.p. de risco)
```

---

## 4. A Narrativa Vencedora para o Relatório Final (5 Páginas)

A banca examinadora do Itaú Asset é formada por gestores e pesquisadores quantitativos seniores. Apresentar um "Sharpe milagroso maquiado" é garantia de desclassificação. 

Por outro lado, apresentar um **Arco Completo de Auditoria Crítica e Falseamento de Hipóteses** é o que define uma equipe de padrão institucional:

```
Página 1: A Tese & Ideação — Topologia de Redes (MST) para Diversificação Idiossincrática
Página 2: A Modelagem Sistemática — Arquitetura em Cascata (MST -> Momentum -> Cap CVM 175 -> Regime)
Página 3: A Bateria de Testes In-Sample & Ablação — Isolando o papel de cada camada (Occam descarte ML)
Página 4: O Teste Cego Out-of-Sample & Análise Crítica — Diagnóstico honesto da perda de sinal e atritos
Página 5: Conclusões, Lições Aprendidas & O Papel da IA Generativa (15% da nota)
```

### Por Que Essa Narrativa Pontua no Topo:
- **Conceito (20%):** Hipótese elegante baseada em Mantegna e teoria de redes.
- **Modelagem (20%):** Pipeline rigoroso, modular, sem *look-ahead*, aderente à CVM 175.
- **Backtest (15%):** Nulo pareado, correção de *multiple testing*, teste cego OOS com parâmetros travados.
- **Análise Crítica (15%):** Reconhecimento lúcido de que a MST funciona como *termômetro descritivo de correlação*, mas não como gerador de alpha direcional.
- **Uso de IA Generativa (15%):** Uso intensivo do LLM não para "inventar código", mas para auditoria crítica, falseamento de hipóteses e engenharia de software financeiro.
- **Identidade do Robô (5%):** Robô Nexus como o "Navegador de Redes Complexas".

---

## 5. Checklist de Entrega para a Próxima Sessão

- [ ] **1. Esqueleto dos Slides / PDF (Formato 16:9):** Estruturar exatamente 5 páginas.
- [ ] **2. Anonimato Total:** Garantir zero menções a nomes de integrantes, equipe ou universidade.
- [ ] **3. Restrição de Texto:** Manter o total do relatório estritamente abaixo de **750 palavras**, priorizando gráficos institucionais de alta resolução (`images/08` a `images/14`).
- [ ] **4. Gráficos-Chave a Inserir:**
  - Grafo comparativo da MST (Mercado Calmo vs Crise de 2020).
  - Tabela visual de Ablação por Camadas (V0 a V6).
  - Distribuição do Nulo Pareado de Monte Carlo.
  - Curva de Equity In-Sample e Out-of-Sample vs CDI e Ibovespa.
  - Diagrama dos 5 Pilares de Uso de IA Generativa.
- [ ] **5. Revisão Final e Submissão:** Exportação do PDF no prazo com buffer de segurança.
