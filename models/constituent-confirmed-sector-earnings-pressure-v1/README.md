# AR-115 — Constituent-confirmed sector ETF post-earnings pressure allocator

Research-only qfa alpha model.  The allocator trades liquid SPDR sector ETFs only when a fixed, ex-ante mega-cap constituent map confirms sector pressure during coarse quarterly reporting-season windows.

## Model summary

- Data: qfa/Alpaca real daily OHLCV supplied through `AlpacaGateway`; no CSV input.
- Trading universe: XLK, XLY, XLC, XLF, XLV, XLE, XLP, XLI, XLU, XLRE, XLB.
- Signal inputs: fixed sector-mapped large constituents plus SPY benchmark.
- Signal gates: Jan/Apr/Jul/Oct reporting windows, constituent residual-return breadth, abnormal-volume breadth, close-location breadth, and ETF residual pressure agreement.
- Portfolio: up to four sector ETFs, gross exposure capped at 1.0, no leverage.  No order placement is performed by the model.

## Limitations

The repository data interface has daily OHLCV but no actual earnings calendar or fundamentals, so reporting periods are coarse calendar proxies. Constituent membership is fixed for ex-ante research convenience and ignores historical index membership changes. Evaluation artifacts retain compact summary metrics only, not raw bars or equity curves.
