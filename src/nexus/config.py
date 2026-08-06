"""Configuração central do projeto Nexus."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

DADOS = RAIZ / "dados"
BRUTOS = DADOS / "brutos"
PROCESSADOS = DADOS / "processados"

for _p in (BRUTOS, PROCESSADOS):
    _p.mkdir(parents=True, exist_ok=True)

# Janela de coleta. Começa em 2011 para dar folga: a primeira janela de
# correlação (63 dias úteis) é consumida antes do backtest começar.
INICIO_COLETA = "2011-01-01"
FIM_COLETA = "2026-08-06"  # exclusivo no yfinance; último pregão disponível é 05/08

SUFIXO_B3 = ".SA"
TICKER_IBOV = "^BVSP"

# Série 12 do SGS/BCB = taxa CDI diária (% ao dia).
SGS_CDI = 12

# Universo operacional: nº de ações mais líquidas elegíveis a cada rebalanceamento.
TAMANHO_UNIVERSO = 80

# Liquidez medida pela mediana do volume financeiro diário nesta janela trailing.
JANELA_LIQUIDEZ = 63

# Cobertura mínima de preços dentro da janela para a ação ser elegível.
COBERTURA_MINIMA = 0.90

# Descarta tickers com histórico curto demais para qualquer uso.
MIN_OBS_TICKER = 120
