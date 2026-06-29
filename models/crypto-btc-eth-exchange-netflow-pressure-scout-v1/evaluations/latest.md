# AR-144 evaluation latest

- Decision: hold
- Status: hold
- Asset bucket: crypto
- Crypto label: true
- Performance evaluation run: false
- Hold reason: timestamp-safe provider access/coverage for BTC/ETH exchange netflow and qfa on-chain flow evaluator support are missing.
- Blocked component: external_onchain_exchange_netflow_provider_and_crypto_flow_evaluator
- External issue URL or ID: none
- Last checked at: 2026-06-29T15:24:02Z
- Next check at: 2026-07-13T15:24:02Z
- Unblock condition: provide Glassnode/CryptoQuant/Coin Metrics/Nansen/equivalent PIT exchange-flow access with publication-lag and label-revision policy, and add evaluator support for spot/perp maker/taker fees plus funding if perps are used.

## Source gates
- Repository: no native on-chain exchange netflow ingestion, publication-lag tracking, exchange-label revision tracking, or spot/perp flow evaluator found.
- Glassnode: HTTP 401 without credentials.
- CryptoQuant: HTTP 401 without bearer token.
- Coin Metrics: catalog reachable, exchange-flow metrics forbidden without credentials.
- Nansen: API key required.

## Fee model documented, not applied
- Spot: maker 10.0 bps, taker 20.0 bps, 50/50 fill mix.
- Perps optional later: maker 2.0 bps, taker 5.0 bps, 50/50 fill mix, funding included.

## Required booleans
- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false

Children spawned: none.
