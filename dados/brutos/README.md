# Dados Brutos (Raw Data)

**Regra de Ouro:** O conteúdo desta pasta é IMUTÁVEL (Read-Only).

Aqui residem os dados primários que alimentam o pipeline do Projeto Nexus. Qualquer anomalia, split, agrupamento ou *outlier* contido aqui deve ser tratado exclusivamente na camada de processamento (`src/nexus/data_loader.py` ou scripts de feature engineering), preservando a sujeira original para efeitos de auditoria da banca.

## Arquivos Esperados
* `ibov_composicao.csv` / `.parquet`: Composição histórica da carteira teórica do Ibovespa (nosso universo original).
* `cotacoes_b3.parquet`: Base de preços, volumes e ajustes diários de todas as ações elegíveis.
* `taxa_cdi.parquet`: Histórico da taxa livre de risco brasileira para cálculo do Sharpe Ratio e custo de oportunidade de caixa.
* Indicadores macroeconômicos brutos (para uso futuro no Filtro de Regime de Mercado).
