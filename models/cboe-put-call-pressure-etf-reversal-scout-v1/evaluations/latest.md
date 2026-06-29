# AR-148 latest evaluation

- **Decision:** rejected
- **Source gate:** passed
- **Real data:** CBOE daily market-statistics pages plus Alpaca/qfa real ETF OHLCV
- **No CSV / daemon / orders:** `no_csv_used=true`, `no_data_csv_argument_used=true`, `no_daemon=true`, `no_orders=true`
- **Raw daily paths retained:** false

## Source gate

CBOE URL template: `https://www.cboe.com/markets/us/options/market-statistics/daily?mkt=all&dt=YYYY-MM-DD`.

Parsed 1,689 of 1,689 Alpaca trading dates from 2019-10-07 through 2026-06-26. Required aggregate put/call fields were 100% non-null for total, index, ETP, equity, VIX, and SPX+SPXW ratios.

## Performance summary

Primary T+1 best scout variant: 126-day lookback, 95% extreme threshold, risk-on on high aggregate put pressure and defensive bond allocation on low put pressure.

- 10 bps Sharpe: -0.3563
- 10 bps annualized return: -1.95%
- 10 bps max drawdown: -13.33%
- Random windows: median Sharpe -0.3592, p25 Sharpe -1.3801, positive-window rate 41.67%
- Cost sensitivity: 5 bps Sharpe -0.0004; 20 bps Sharpe -1.0495

Controls did not rescue the signal. Relevant price-control max absolute correlation excluding the intentionally inverted diagnostic was about 0.276, but performance gates failed decisively.

See `latest.json` and `runs/ar148_cboe_alpaca_real_20260629T212906Z.json` for compact details.
