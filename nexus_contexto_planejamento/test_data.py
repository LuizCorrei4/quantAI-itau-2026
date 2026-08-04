import yfinance as yf

tickers = ["SOUZ3.SA", "VVAR3.SA", "BTOW3.SA", "BRML3.SA", "LCAM3.SA", "HGTX3.SA", "PCAR4.SA", "KROT3.SA", "NATU3.SA", "LAME4.SA", "PETR4.SA"]
for t in tickers:
    data = yf.download(t, start="2012-01-01", end="2020-01-01", progress=False)
    print(f"{t}: {len(data)} rows")

