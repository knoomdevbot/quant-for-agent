# crypto-btc-eth-exchange-netflow-pressure-scout-v1

AR-144 feasibility scout for timestamp-safe BTC/ETH exchange-netflow pressure.

## Decision

**Hold.** The mechanism is not rejected, but immediate performance evaluation is blocked by external provider/qfa-ingestion requirements. Real on-chain exchange inflow/outflow/netflow/balance data is required. OHLCV proxies, CSV fixtures, and latest-revised-only provider series are not acceptable.

## Provider gate summary

Coin Metrics community endpoints expose relevant daily BTC/ETH exchange flow/supply metrics and returned sample values without credentials, but the checked values included provider status-time fields far after the observation dates. Without as-of snapshots or revision history, a historical backtest would be revision/availability unsafe. Glassnode and CryptoQuant checked paths required credentials. Nansen documentation was reachable, but no credential-free historical BTC/ETH exchange-flow endpoint was confirmed.

## Required before performance

1. Provider/API access for BTC/ETH exchange inflow, outflow, netflow, and exchange balance.
2. Point-in-time availability or revision-history support plus documented publication lag and exchange-label revision policy.
3. qfa ingestion/evaluator support for crypto assets, missing/late metrics, maker/taker fees, and relevant BTC/ETH momentum/reversal/stablecoin controls.
4. No CSV fixtures, no daemon, no orders, and no raw provider data committed.

## Artifacts

- `model.py` exposes `generate_signals(context)` and returns no tradable signals while on hold.
- `config.yaml` records required data gates and fee assumptions.
- `evaluations/latest.json` and `evaluations/latest.md` record the source-gate result.
