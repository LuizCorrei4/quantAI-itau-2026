# Robô Nexus - Desafio Itaú Asset Quant AI 2026

Este repositório contém todo o material, documentação e código necessários para a entrega final do desafio. O objetivo do projeto é desenvolver, testar e apresentar uma estratégia quantitativa competitiva baseada em Teoria de Grafos e Finanças.

## Estrutura Atual do Repositório

- **nexus_contexto_planejamento/**: Contém o `plano_final_nexus.md`, o guia-mestre do projeto, com a tese completa, cronograma, modelagem quantitativa, estrutura de backtest e métricas.
- **contexto_geracao_ideias/**: Documentos e pesquisas iniciais, incluindo lições dos últimos vencedores e alternativas de estratégias estudadas antes de decidirmos pelo modelo Nexus.
- **documentos_desafio/**: Diretrizes oficiais e materiais de referência fornecidos para a competição.
- **GEMINI.md e CLAUDE.md**: Documentações auxiliares elaboradas para prover contexto focado para os agentes de Inteligência Artificial que auxiliam no projeto (Agy e Claude).

## Próximos Passos (MVP)

A equipe focará na implementação de um Produto Viável Mínimo (MVP) do backtest, incluindo:
1. Extração de preços ajustados e volume via yfinance.
2. Cálculo de correlações com estimador de Ledoit-Wolf.
3. Construção da Minimum Spanning Tree (MST).
4. Alocação top 10 com base em centralidade (Betweenness).

Consulte o `plano_final_nexus.md` para o cronograma atualizado e as métricas definidas para avaliação.
