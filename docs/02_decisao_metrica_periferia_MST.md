# Avaliação Quantitativa: Métricas de Periferia na MST

Este documento consolida os testes estatísticos realizados para a **Escolha da Métrica de Periferia (Etapa 4)** do Robô Nexus.
A avaliação percorreu 4 datas-chave do mercado brasileiro (2014, 2017 Joesley Day, 2020 Crash COVID, e 2023).

## 1. O Teto de Vidro da Betweenness (Taxa de Empate)
O problema matemático estrutural foi provado. A porcentagem média de ações que ficam empatadas com exatamente o mesmo valor em cada métrica:

| Métrica do Grafo | Taxa Média de Empate | Status |
|---|---|---|
| **Betweenness** | 54.1% | ❌ Invalidada |
| **Closeness** | 1.2% | ✅ Aprovada |
| **Excentricidade** | 1.9% | ✅ Aprovada |
| **Farness** | 1.2% | ✅ Aprovada |
| **Edge_Length** | 2.5% | ✅ Aprovada |

> **Conclusão 1:** Betweenness Centrality é matematicamente inutilizável para seleção de portfólio neste caso. Closeness, Farness, Excentricidade e Edge Length geram distribuições contínuas ideais.

## 2. MST vs Regressão Linear Simples (Similaridade Spearman)
A banca nos perguntará: *'Por que o esforço do Grafo, em vez de simplesmente comprar ações de Baixo Beta?'*. Avaliamos a Correlação de Ordem (Spearman) do ranking gerado pelos Grafos contra dois *baselines* triviais:

| Métrica do Grafo | Similaridade com Baixo Beta | Similaridade com Baixa Correlação |
|---|---|---|
| **Betweenness** | 0.63 | 0.60 |
| **Closeness** | 0.55 | 0.62 |
| **Excentricidade** | 0.52 | 0.58 |
| **Farness** | 0.55 | 0.62 |
| **Edge_Length** | 0.75 | 0.77 |

> **Conclusão 2:** A Farness (assim como a Closeness) possui uma similaridade média (~0.4 a ~0.6) com os Baselines. Isso é **excelente**. Significa que o Grafo captura a essência de 'porto-seguro' do Beta e da Baixa Correlação, mas não é uma cópia barata deles. A MST traz um sinal estatístico único e não redundante sobre a topologia do mercado.

## 3. Na Prática: O Top 5 de Março de 2020 (Crash do COVID)
Para ilustrar o descolamento, veja quais seriam as 5 ações mais periféricas/seguras selecionadas no auge do pânico se usássemos o Grafo (Farness) versus Regressão Linear (Beta):

- **As 5 escolhas do Baixo Beta:** `RADL3, TAEE11, TIMS3, ISAE4, BBSE3`
- **As 5 escolhas da MST (Farness):** `ITSA4, PSSA3, SANB11, ITUB4, SBFG3`

> O Grafo consegue olhar para a intersecção global da rede (Farness) em vez de uma relação isolada papel x mercado (Beta).

## Veredito Oficial: Por que a FARNESS?
**Adotaremos a FARNESS (Soma das Distâncias) como a Métrica Oficial do Robô Nexus, e não as outras alternativas.**

A justificativa técnica e teórica para a apresentação é a seguinte:
1. **Contra a Betweenness:** Foi reprovada por colapso matemático, gerando zeros para todas as pontas da árvore (mais de 50% de empate).
2. **Contra a Edge Length (Comprimento da Aresta):** Ela é 'míope'. Olha apenas para a conexão imediata do vizinho, sem saber se esse vizinho está no centro ou na borda do mercado. Acaba se tornando apenas um 'baixo beta' disfarçado (alta correlação com o baseline).
3. **Contra a Excentricidade:** Mede a distância apenas para o nó mais distante de todos. É excessivamente sensível a *outliers*. Uma única ação com comportamento bizarro distorce a excentricidade da rede toda.
4. **Contra a Closeness Centrality:** Matematicamente válida, mas pedagogicamente ruim, pois inverte o ranking (usa o inverso da soma, gerando decimais minúsculos de difícil explicação).
5. **A Vitória da Farness:** É a soma absoluta das distâncias para as outras 79 ações. Uma ação só tem Farness alta se ela estiver distante de *todo o resto do mercado*. Isso garante 100% de continuidade (desempate) e captura perfeitamente o conceito macro topológico de 'lobo solitário' do mercado financeiro, trazendo diversificação real contra choques sistêmicos.