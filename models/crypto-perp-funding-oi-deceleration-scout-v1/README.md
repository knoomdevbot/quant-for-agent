# AR-142 — Crypto perp funding/OI deceleration feasibility scout

## Decision
Blocked for immediate performance evaluation: current qfa infrastructure is not timestamp-safe for crypto perpetual funding/OI carry.

This is not an alpha rejection from performance. No costed backtest was run because doing so with the current OHLCV/Alpaca/CSV-oriented evaluator would fabricate missing funding cashflows and open-interest timing.

## What was checked
- Current repository infrastructure:
  - `src/quant_for_agent/data.py` loads OHLCV CSV fixtures only.
  - `src/quant_for_agent/backtest.py` evaluates price returns from close-to-close bars only.
  - Alpaca/qfa paths in existing artifacts are equity/ETF daily-bar oriented.
  - No native funding cashflow, OI feature, mark/index alignment, perpetual contract metadata, or maker/taker fill accounting exists.
- Public API reachability from the research host:
  - OKX public endpoints: accessible for funding history, OI/current or aggregate OI data, and historical mark/index/trade candles in lightweight shape checks.
  - Binance USD-M endpoints: blocked from this host by HTTP 451 restricted-location response.
  - Bybit public endpoints: blocked from this host by HTTP 403 CloudFront country block.
  - Kraken Futures: public instruments/tickers accessible; historical funding/OI suitability not proven in this scout.
  - CoinGlass, Kaiko, Amberdata, Coin Metrics or equivalent vendors: plausible, but not available here without credentials/licensing and a cache-retention policy.

No raw API payloads, CSV fixtures, vendor dumps, credentials, caches, SQLite DBs, or orders were created or retained.

## Feasibility conclusion
A timestamp-safe evaluator is plausible after dedicated crypto derivatives ingestion work, but it is not immediately feasible with current repo/infrastructure.

Minimum prerequisite work:
- Funding-rate history connector with exact funding timestamps and conservative availability-lag policy.
- Historical open-interest connector aligned to venue contract identifiers.
- Mark/index/last price candle ingestion on the same timestamp/contract schema.
- Contract metadata, delisting, symbol migration, settlement interval, and venue outage handling.
- Evaluator that separates mark/price PnL from funding cashflow PnL.
- Maker/taker/slippage/fill-mix model applied to turnover.
- Coverage report before any product universe is selected.

## Fee model placeholder
- maker_bps: 2.0
- taker_bps: 5.0
- fill_mix:
  - maker: 0.5
  - taker: 0.5

The fee model was documented but not applied because no performance evaluation was run.

## Required constraints
- asset_bucket: crypto
- crypto_label: true
- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false
