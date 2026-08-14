"""
===============================================================================
PROJETO NEXUS - DESAFIO ITAÚ ASSET QUANT AI 2026
Configurações Globais do Sistema e Parâmetros Operacionais
Arquivo: src/nexus/config.py
===============================================================================

Este arquivo centraliza todos os diretórios, constantes de mercado, taxas,
janelas temporais e parâmetros de gestão de risco utilizados pelos módulos do
robô Nexus ao longo de todo o pipeline (MVP, Filtros Alpha, Regime e Portfólio).
===============================================================================
"""

from pathlib import Path

# Raiz do repositório
RAIZ = Path(__file__).resolve().parents[2]

# Diretórios de Dados
DADOS = RAIZ / "dados"
BRUTOS = DADOS / "brutos"
PROCESSADOS = DADOS / "processados"
RESULTADOS = DADOS / "resultados"

# Garante a existência das pastas essenciais
for _p in (BRUTOS, PROCESSADOS, RESULTADOS):
    _p.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# Janelas de Coleta e Universo de Ativos
# -----------------------------------------------------------------------------
# Início em 2011-01-01 garante que a primeira janela de correlação (63 dias úteis)
# e as médias móveis de 200 dias estejam aquecidas antes do início do backtest.
INICIO_COLETA = "2011-01-01"
FIM_COLETA = "2026-08-06"  # Exclusivo no yfinance; último pregão disponível é 05/08/2026

SUFIXO_B3 = ".SA"
TICKER_IBOV = "^BVSP"

# Código da série temporal do Banco Central (SGS/BCB): Série 12 = Taxa CDI diária (% ao dia)
SGS_CDI = 12

# Tamanho do universo mensal de ações mais líquidas elegíveis
TAMANHO_UNIVERSO = 80

# Janela móvel para apuração da liquidez (mediana do volume financeiro diário em 63 pregões)
JANELA_LIQUIDEZ = 63

# Cobertura mínima de presença de preços na janela para habilitação do ativo
COBERTURA_MINIMA = 0.90

# Filtro de histórico mínimo para inclusão de novos tickers
MIN_OBS_TICKER = 120

# -----------------------------------------------------------------------------
# Parâmetros de Construção da MST e Seleção Topológica (Camada 1)
# -----------------------------------------------------------------------------
JANELA_CORRELACAO = 63       # Dias úteis (~3 meses) para cálculo da correlação com shrinkage Ledoit-Wolf
TOP_N = 10                   # Quantidade padrão de ações selecionadas na periferia (MVP)

# -----------------------------------------------------------------------------
# Parâmetros Operacionais, Custos e Gestão Prudencial de Risco (Camadas 2 e 3)
# -----------------------------------------------------------------------------
# Custo transacional estimado por perna: 5 bps (0.05%) = 10 bps por turnover completo
CUSTO_POR_OPERACAO = 0.0005

# CAP de Concentração Máxima por Ativo (Regra de Prudência e Alinhamento à CVM Resolução 175):
# Limita a alocação máxima em qualquer ativo individual a 10% do patrimônio líquido do fundo.
# Quando menos de 10 ações são aprovadas pelos filtros, o capital não alocado
# permanece automaticamente investido na segurança da taxa livre de risco (CDI).
CAP_POR_ATIVO = 0.10  # 10% por ação (ex: 2 ações aprovadas = 20% ações, 80% CDI)
