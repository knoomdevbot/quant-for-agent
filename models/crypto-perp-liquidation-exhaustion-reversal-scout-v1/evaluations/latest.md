# AR-143 latest evaluation — feasibility scout

- Completed at: 2026-06-29T02:01:49Z
- Decision: blocked_infra_data_depth_evaluator
- Performance evaluation run: false
- Asset bucket: crypto
- Crypto label: true

## Result
Immediate timestamp-safe performance evaluation is blocked. OKX makes the liquidation-print side plausible, but current qfa lacks the required crypto perp liquidation/depth/event-study evaluator, and historical depth/spread coverage was not proven from public checks.

## Source findings
- OKX public API: promising. Filled liquidation orders on BTC-USDT-SWAP returned timestamp, side, position side, size, and bankruptcy price fields. Historical trades, 1m candles, and current book endpoints were reachable.
- Binance: USD-M API returned HTTP 451 from this host. Binance Data Vision direct HEAD checks showed price/depth archives for BTCUSDT, but the checked liquidationSnapshot path returned 404.
- Bybit: HTTP 403 CloudFront country block from this host.
- Kraken Futures: instruments endpoint reachable; liquidation/depth history not proven.
- CoinGlass: liquidation-history endpoint requires an API key; no key used.
- Kaiko/Amberdata/Coin Metrics/equivalent vendors: plausible licensed paths only.

## Required next work
- Dedicated liquidation-print ingestion with timestamp and pagination tests.
- Same-venue trades/candles aligned to contract metadata.
- Historical depth/spread data or conservative real-data-calibrated proxy.
- Timestamp-safe event-study evaluator with maker/taker fees, slippage/depth stress, matched non-events, shifted timestamps, and simple reversal/vol-spike controls.

## Fee model documented, not applied
- maker_bps: 2.0
- taker_bps: 5.0
- fill_mix: maker 0.25 / taker 0.75

## Constraints observed
- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false
