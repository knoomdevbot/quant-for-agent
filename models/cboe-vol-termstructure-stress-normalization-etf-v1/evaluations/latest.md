# AR-145 latest evaluation

Decision: **hold**

CBOE public daily-history endpoints for VIX, VIX3M, VIX9D, and VVIX returned HTTP 200 CSV samples, and no raw CBOE files were retained. Timestamp-safe use remains conditional on applying at least one completed trading-session lag before scoring ETF returns.

The qfa/Alpaca market-data gate failed in this environment: `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` were not configured, and `AlpacaGateway().get_bars(...)` raised the expected missing-credentials error. Because CSV-backed ETF market-price backtests are forbidden, no performance run was attempted.

Required unblock condition: configure approved Alpaca/qfa real ETF daily bar access and rerun with no `--data-csv`, no daemon, no orders, 10 bps primary turnover cost, 5/20 bps sensitivity, required controls, and compact artifacts only.

Required booleans:

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false
