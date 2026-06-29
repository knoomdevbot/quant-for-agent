# AR-143 — Crypto perp liquidation-exhaustion reversal scout

## Decision
Blocked for immediate performance evaluation: a timestamp-safe liquidation-exhaustion event study is plausible with additional crypto derivatives data work, but it is not feasible in current qfa without fabricating key data and execution assumptions.

This is not a performance rejection. No costed backtest or event study was run.

## What was checked
- Current repository infrastructure:
  - `src/quant_for_agent/data.py` is CSV/OHLCV oriented.
  - `src/quant_for_agent/backtest.py` evaluates price-return bars and has no event-time liquidation/depth evaluator.
  - No native crypto perpetual liquidation, historical order-book/depth, spread, venue-contract metadata, or maker/taker fill model exists.
- Public source/API shape checks from this host:
  - OKX public API: reachable for filled liquidation orders on BTC-USDT-SWAP with timestamp/side/size fields, plus historical trades, 1m candles, and current order book.
  - Binance USD-M API: restricted by HTTP 451 from this host. Binance Data Vision direct HEAD checks showed BTCUSDT 1m kline and bookDepth daily archives exist, but the checked liquidationSnapshot path did not exist.
  - Bybit public API: blocked by HTTP 403 CloudFront country restriction.
  - Kraken Futures: instruments endpoint reachable; historical liquidation/depth suitability not proven.
  - CoinGlass: liquidation-history endpoint requires an API key; no key used.
  - Kaiko/Amberdata/Coin Metrics/equivalent: plausible licensed routes only.

No raw API payloads, CSV fixtures, vendor dumps, credentials, caches, SQLite DBs, or orders were created or retained.

## Feasibility conclusion
- Timestamped liquidation prints: plausible on OKX and likely through vendors, but cross-venue coverage needs proof.
- Tradable price history: plausible from OKX trades/candles and/or venue archives.
- Historical depth/spread: not proven from lightweight public checks; required for cost/slippage-stressed evaluation.
- Current qfa evaluator: not adequate for this event-time, microstructure, maker/taker/depth-dependent alpha.

## Minimum prerequisite work
- Build a liquidation-print connector with exchange timestamp, side, size/notional, symbol, venue, contract metadata, and pagination tests.
- Ingest same-venue trades or 1m-or-finer tradable price series with conservative availability lag.
- Ingest historical bid/ask/depth snapshots or document a conservative real-data-calibrated spread/depth proxy.
- Implement timestamp-safe event labeling using only liquidation intensity and price action available at decision time.
- Add event-study controls: matched non-events, shifted liquidation timestamps, simple reversal/vol-spike baselines, clustered-event caps, and stressed cost/slippage tests.

## Fee model placeholder
- maker_bps: 2.0
- taker_bps: 5.0
- fill_mix:
  - maker: 0.25
  - taker: 0.75

The fee model was documented but not applied because no performance evaluation was run.

## Required constraints
- asset_bucket: crypto
- crypto_label: true
- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false
