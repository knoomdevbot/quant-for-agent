# AR-142 latest evaluation — crypto perp funding/OI deceleration scout

## Decision
Blocked for immediate timestamp-safe real-data performance evaluation.

## Rationale
Current qfa can evaluate price-only OHLCV strategies, but it does not model crypto perpetual funding cashflows, open-interest features, mark/index/last price alignment, venue contract metadata, or maker/taker fill costs. A backtest now would be misleading because the alpha hypothesis depends directly on funding payment timing and OI deceleration.

## Data/API feasibility findings
- OKX public API was reachable from this host in lightweight checks for funding history, OI-related data, and historical price candles.
- Binance USD-M public derivative endpoints returned HTTP 451 restricted-location responses from this host.
- Bybit public derivative endpoints returned HTTP 403 CloudFront country-block responses from this host.
- Kraken Futures public instruments/tickers were reachable, but historical funding/OI suitability was not established.
- Vendor options such as CoinGlass, Kaiko, Amberdata, and Coin Metrics remain plausible but require credentials/licensing and cannot be assumed.

## Gate results
- Data coverage gate: not passed.
- Timestamp discipline gate: not passed without new ingestion/evaluator infrastructure.
- Costed performance gate: not run.
- Suggested direct children: none.

## Constraints observed
- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false

See `latest.json` and `runs/20260629T015402Z.json` for the machine-readable result.
