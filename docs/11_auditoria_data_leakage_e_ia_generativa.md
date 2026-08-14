# Auditoria de Data Leakage, Fórmulas de Sharpe e o Papel da IA Generativa

**Data de Elaboração:** 14 de Agosto de 2026  
**Finalidade:** Documentação de Rigor Científico e Atendimento aos Critérios de IA do Edital Itaú Asset 2026

---

## 1. Auditoria e Correção Transparente do Data Leakage

Em respeito absoluto às diretrizes de rigor metodológico do Desafio Itaú Asset, registramos de forma transparente a identificação e correção de um viés crítico de antecipação temporal (*look-ahead bias*):

### 1.1 O Diagnóstico do Viés Inicial
Na versão preliminar do pipeline, o modelo de Machine Learning (Regressão Logística) havia sido treinado em toda a base *In-Sample* (2011–2018) em uma única etapa e, posteriormente, colocado para prever os próprios meses em que foi treinado durante o backtest. Esse procedimento inflou artificialmente o Sharpe da Cascata para 0.481.

### 1.2 A Solução: Walk-Forward Expanding Window
Substituímos o modelo estático por uma esteira **Walk-Forward mensal**:
- No mês $T$, o classificador de Machine Learning é treinado **exclusivamente com dados observados até $T-1$**.
- O modelo faz inferência cega sobre o mês $T$.
- Quando o número de meses disponíveis no passado é inferior a 12 meses (período de *Warmup*), o modelo abstém-se de operar e a estratégia aloca em CDI ou opera com a camada de Momentum.
- O resultado honesto obtido pela Cascata foi um Sharpe de **+0.053** (revelando o ruído e o excesso de turnover induzidos pelo classificador).

---

## 2. Definição Rigorosa das Convenções de Sharpe Ratio

Para assegurar consistência matemática perante a banca examinadora, detalhamos as duas formulações calculadas nos relatórios:

### 2.1 Sharpe Clássico Anualizado (Excesso Aritmético)
Formulação teórica padrão de William Sharpe (1966, 1994):
$$\text{Sharpe}_{\text{clássico}} = \sqrt{12} \times \frac{\frac{1}{N} \sum_{t=1}^N (R_{p,t} - R_{cdi,t})}{\sqrt{\frac{1}{N-1} \sum_{t=1}^N \left((R_{p,t} - R_{cdi,t}) - \overline{R_{p} - R_{cdi}}\right)^2}}$$

*Resultado no In-Sample (Momentum Puro):* **+0.184**

### 2.2 Sharpe Geométrico (CAGR Excess sobre Volatilidade)
Formulação baseada na taxa composta anual de crescimento do capital (CAGR):
$$\text{Sharpe}_{\text{geométrico}} = \frac{\text{CAGR}_{\text{portfólio}} - \text{CAGR}_{\text{cdi}}}{\sigma_{\text{anualizada}}}$$
onde $\text{CAGR} = \left(\prod_{t=1}^N (1 + R_t)\right)^{12/N} - 1$ e $\sigma_{\text{anualizada}} = \sigma_{\text{mensal}} \times \sqrt{12}$.

*Resultado no In-Sample (Momentum Puro):* **+0.122** (superando o benchmark de Monte Carlo de **+0.107** com p-value = 3.2%).

---

## 3. O Descarte do Machine Learning como Vitória Metodológica (Estudo Negativo)

Um dos maiores diferenciais de uma equipe quantitativa de alto nível é a **recusa em aceitar complexidade sem benefício comprovado**.

A tentativa de adicionar a camada preditiva gerou:
1. Queda no Sharpe Geométrico de **+0.122** (Momentum) para **+0.053** (Cascata).
2. Aumento de custos de turnover sem melhora na taxa de acerto direcional.

**Controle de Overfitting e Capacidade do Modelo:**
É importante ressaltar que os modelos de Machine Learning testados (como XGBoost e Random Forest) tiveram seus hiperparâmetros severamente restritos (ex: árvores de baixa profundidade, taxa de aprendizado reduzida e forte regularização). Essa limitação intencional foi aplicada porque algoritmos de alta capacidade conseguem facilmente "decorar" o ruído predominante em dados financeiros (baixo sinal-ruído), falhando drasticamente ao tentar generalizar para dados *out-of-sample*. Mesmo com esse rigoroso controle para conter o *overfitting*, os modelos não conseguiram extrair um sinal superior à simples e robusta média móvel.

Pela **Navalha de Occam**, o Machine Learning preditivo foi descartado da esteira final de execução. Este **Estudo Negativo (*Negative Result*)** é um dos maiores testemunhos de integridade e sobriedade científica do projeto Nexus.

---

## 4. O Papel Estruturante da IA Generativa no Projeto Nexus (Peso 15%)

A exigência do edital do Desafio Itaú Asset quanto ao uso de **Inteligência Artificial Generativa** foi atendida de maneira profunda, atuando como co-piloto intelectual e técnico em **5 pilares centrais**:

```
                              ┌───────────────────────────────┐
                              │  IA GENERATIVA (GEMINI / AGY) │
                              │   Co-piloto Quantitativo      │
                              └───────────────┬───────────────┘
                                              │
         ┌──────────────────┬─────────────────┼─────────────────┬──────────────────┐
         │                  │                 │                 │                  │
         ▼                  ▼                 ▼                 ▼                  ▼
┌─────────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌────────────────┐
│   1. IDEIAÇÃO   │ │ 2. ENGENHARIA │ │ 3. AUDITORIA  │ │ 4. GESTÃO DE  │ │  5. BRANDING & │
│   TOPOLÓGICA    │ │   DE CÓDIGO   │ │  METODOLÓGICA │ │  RISCO (CVM)  │ │   IDENTIDADE   │
└─────────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └────────────────┘
```

### 1. Ideação Conceitual & Topologia
- Formulação da tese de seleção de ativos periféricos via *Farness* em Árvores Geradoras Mínimas (MST).
- Dedução da distância ultramétrica de Mantegna ($d_{ij} = \sqrt{2(1 - \rho_{ij})}$) e implementação com encolhimento de covariância de Ledoit-Wolf.

### 2. Engenharia de Software Quantitativo (MLOps)
- Desenvolvimento modular de toda a biblioteca em Python (`src/nexus/`: `mst.py`, `portfolio.py`, `alpha_filters.py`, `config.py`).
- Automação da esteira de dados brutos e processados em formato Parquet de alta performance.

### 3. Auditoria Crítica e Detecção de Vieses
- Diagnóstico autônomo do *Data Leakage* temporal no treinamento estático de ML.
- Concepção e codificação da esteira *Walk-Forward Expanding Window* com estrita separação temporal em $T-1$.

### 4. Modelagem de Gestão de Risco e Regulação
- Identificação do perigo de hiperconcentração (50% em 2 ativos).
- Formulação matemática e implementação da **Regra de CAP de 10% por ativo**, assegurando estrita aderência à **Resolução CVM 175**.

### 5. Identidade, Persona e Relatórios Automatizados
- Concepção da identidade conceitual do Robô Nexus ("o navegador das teias de correlação").
- Geração automatizada de gráficos em alta resolução e elaboração de relatórios técnicos institucionais em Markdown e PDF.
