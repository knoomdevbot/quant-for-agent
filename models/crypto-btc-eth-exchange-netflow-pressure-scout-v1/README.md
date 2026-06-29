# crypto-btc-eth-exchange-netflow-pressure-scout-v1

AR-144 feasibility scout for timestamp-safe BTC/ETH exchange-netflow pressure.

## Decision
- Status: hold
- Reason: provider access/coverage and timestamp-safety could not be confirmed, and current qfa has no native on-chain exchange-netflow evaluator with crypto spot/perp cost/funding support.
- Last checked: 2026-06-29T15:24:02Z
- Next check: 2026-07-13T15:24:02Z

## Data gate
Use real on-chain provider data only: Glassnode, CryptoQuant, Coin Metrics, Nansen, or equivalent licensed provider. No OHLCV flow proxy, fabricated netflow, CSV fixture, qfa daemon, or orders were used.

Lightweight checks found:
- Glassnode: API returned 401 without credentials.
- CryptoQuant: API returned 401 without bearer token.
- Coin Metrics: community catalog reachable, but requested exchange-flow metrics returned 403 without credentials.
- Nansen: API key required.
- Repository: crypto OHLCV plumbing exists, but no native on-chain exchange netflow connector/evaluator or label-revision/availability-lag handling was found.

## Fee assumptions documented for future tests
- Spot: maker_bps 10.0, taker_bps 20.0, fill mix 50%/50%.
- Perps if used later: maker_bps 2.0, taker_bps 5.0, fill mix 50%/50%, funding included at exchange funding timestamps.

## Required unblock
Provide PIT/timestamp-safe BTC and ETH exchange inflow/outflow/netflow metrics with publication lag and exchange-label revision policy, plus qfa evaluator support for crypto spot/perp maker/taker fees and perp funding if perps are used.

## Safety flags
- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false
