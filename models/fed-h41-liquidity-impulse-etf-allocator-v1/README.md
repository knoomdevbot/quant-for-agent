# fed-h41-liquidity-impulse-etf-allocator-v1

AR-147 fast-falsification/source-vintage scout for a Fed H.4.1 weekly liquidity impulse ETF allocator.

The signal uses public H.4.1-related series (`WALCL`, `WRESBAL`, `WTREGEN`, `RRPONTSYD`) with a conservative release rule: Wednesday observation values are only eligible after the scheduled Thursday 16:30 ET H.4.1 release, with ETF allocation effective the next trading session. ETF prices were Alpaca real daily bars via qfa `AlpacaGateway`; no CSV-backed market-data backtest, daemon, orders, raw cache, SQLite DB, bytecode, or helper script is retained.

## Decision

`rejected` — Rejected: failed strict fast-falsification gates: max_relevant_correlation_above_0_60

## Key metrics

- Primary 10 bps one-way Sharpe: `0.48697177`
- Random-window median / p25 Sharpe: `0.78305925` / `0.39129277`
- Positive random-window rate: `0.875`
- 20 bps cost Sharpe: `0.33790794`
- Shifted-label Sharpe: `0.24736634`; inverted-label Sharpe: `0.25367064`
- TSMOM baseline Sharpe: `0.48992916`
- Max relevant retained-model correlation: `0.62351781`

## Caveat

Release timing is timestamp-feasible, but this compact scout used current FRED mirror history rather than retaining ALFRED vintage-by-vintage values; historical revision immunity is therefore marked `pass_with_revision_caveat`.
