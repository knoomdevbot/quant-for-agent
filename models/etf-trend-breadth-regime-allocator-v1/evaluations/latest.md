# AR-077 Evaluation — ETF trend-breadth regime allocator

Created: `2026-06-26T13:44:16Z`

## Suggested decision

**rejected** — Fails AR-077 falsifier on random-window after-cost Sharpe distribution or drawdown.

## Primary results

Window `2020-01-02` to `2025-12-15`; after-cost Sharpe `0.36734683`, annualized return `0.03578016`, annualized volatility `0.11326018`, max drawdown `-0.20554378`, win rate `0.48294314`.

## Random windows

Count `8`; median Sharpe `0.08900822`; p25 Sharpe `-0.45617412`; worst Sharpe `-0.93140835`; positive-window rate `0.5`; worst max drawdown `-0.1451679`.

## Orthogonality

Status `failed_max_corr_gt_0_60`; max abs corr `0.69327024`.

- `AR-037` corr `0.69327024` over `989` periods: `/Users/moonk/quant-for-agent/models/etf-carry-defensive-allocation-v1/evaluations/runs/ar037_qfa_alpaca_real_20260626T083545Z.json`
- `AR-063` corr `0.64784039` over `738` periods: `/Users/moonk/quant-for-agent/models/macro-surprise-drawdown-etf-allocator-v1/evaluations/runs/ar063_qfa_alpaca_real_20260626T115805Z.json`
- `AR-063` corr `0.64784039` over `738` periods: `/Users/moonk/quant-for-agent/models/macro-surprise-drawdown-etf-allocator-v1/evaluations/runs/ar063_qfa_alpaca_real_20260626T115707Z.json`
- `AR-051` corr `0.54670138` over `500` periods: `/Users/moonk/quant-for-agent/models/xsec-etf-defensive-rotation-orthogonal-v1/evaluations/runs/ar051_qfa_alpaca_real_20260626T102756Z.json`
- `AR-049` corr `0.41020048` over `989` periods: `/Users/moonk/quant-for-agent/models/etf-carry-defensive-orthogonal-v1/evaluations/runs/ar049_qfa_alpaca_real_20260626T102842Z.json`

## Controls

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- db_artifact_retained: false
- raw_daily_paths_retained: false

Command provenance: credentials were sourced from the configured secret profile with values redacted; qfa/Alpaca daily bars were used without CSV input, daemon, or order commands.
