# AR-144 latest evaluation — exchange-netflow pressure scout

- **Completed at:** 2026-06-29T16:18:24Z
- **Decision:** hold — external timestamp-safe provider access/qfa ingestion unavailable.
- **Model:** `crypto-btc-eth-exchange-netflow-pressure-scout-v1`
- **Asset bucket:** crypto
- **Crypto label:** true
- **Performance evaluation:** not run.

## Finding

The BTC/ETH exchange-netflow pressure hypothesis remains plausible, but it cannot be evaluated honestly in current qfa without a timestamp-safe on-chain exchange-flow provider path. Performance based on OHLCV proxies, CSV fixtures, or latest-revised provider data would violate the issue contract.

## Source feasibility gate

- **Coin Metrics community API:** public catalog exposes `FlowInExNtv`, `FlowOutExNtv`, `FlowInExUSD`, `FlowOutExUSD`, `SplyExNtv`, and `SplyExUSD` with daily BTC/ETH coverage, and sample no-credential calls returned values. However, returned samples included status/status-time fields in 2026 for 2024 observations, so latest returned values are not safe for historical performance without as-of snapshots or revision history.
- **Glassnode:** checked metric catalog / exchange-flow metric paths returned HTTP 401 without credentials.
- **CryptoQuant:** docs reachable, but checked exchange-flow endpoint returned HTTP 401 without credentials.
- **Nansen:** docs reachable; no credential-free historical BTC/ETH exchange-netflow endpoint was confirmed.

## Hold fields

- **hold_reason:** external_timestamp_safe_provider_access_unavailable
- **blocked_component:** point_in_time_exchange_flow_provider_or_qfa_ingestion
- **external_issue_url_or_id:** provider_access_required_coin_metrics_or_glassnode_or_cryptoquant_or_nansen
- **last_checked_at:** 2026-06-29T16:18:24Z
- **next_check_at:** 2026-07-29T16:18:43Z
- **unblock_condition:** licensed or credential-free provider/API with BTC/ETH exchange inflow/outflow/netflow/balance, as-of timestamps or revision history, publication-lag and label-revision policy, and qfa ingestion support.

## Fee assumptions documented

- `maker_bps: 2.0`
- `taker_bps: 5.0`
- `fill_mix: {maker: 0.5, taker: 0.5}`
- Funding not evaluated; include funding only if a later perp implementation is used.

## Constraints observed

No CSV fixtures, no user-facing data CSV argument, no qfa daemon, no orders, no raw arrays/bars/provider dumps committed, and no children spawned.
