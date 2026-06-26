# AR-112 — International country ETF RS + currency-stress rotation

Status: **rejected**.

## Result
The selected universe passed the history screen (19 country/region ETFs), but the alpha was rejected. At 10 bps one-way cost the main model had full-sample Sharpe 0.41443477, annualized return 0.04783625, max drawdown -0.22410403, and random/stress-window median Sharpe 0.4353281 with p25 -0.02841595 and worst -1.40977027.

## Why rejected
- Robustness is weak: p25/worst random-window Sharpe are negative.
- Anti-clone check is marginal: max absolute observed correlation is 0.59232144, which passes the 0.60 hard gate but fails the preferred 0.50 gate versus same-data TSMOM/defensive proxies.
- Diagnostics did not show enough incremental value from USD/commodity/drawdown context beyond generic ETF momentum/risk-on beta; broad TSMOM and defensive proxies had much higher 10 bps Sharpe.

## Universe
Selected before performance review from Alpaca daily bar availability: EFA, EEM, EWJ, EWU, EWG, EWQ, EWL, EWC, EWA, EWH, EWT, EWS, EWY, EWW, INDA, FXI, MCHI, EWZ, EZA. Context-only controls: UUP, GLD, DBC, SPY.

## Safety / data
Used qfa/Alpaca real daily bars in memory only. No CSV, no `--data-csv`, no qfa daemon, no orders. Alpaca paper-data credentials were configured with values redacted; no raw daily bars/equity curves/weights were retained.

See `evaluations/latest.json` and `models/country-etf-rs-currency-stress-rotation-v1/evaluations/runs/ar112_qfa_alpaca_real_20260626T204848Z.json` for compact metrics.
