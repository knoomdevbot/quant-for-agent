# AR-019 Evaluation: adaptive pair residual cointegration filters

Status: **rejected** (research reference only; do not promote).

## Data and execution

- Data source: Alpaca real market data via qfa/AlpacaGateway only.
- CSV: no CSV and no `--data-csv` used.
- Trading safety: no daemon and no trades placed.
- Universe: AAPL, MSFT, NVDA, AMZN, META, GOOGL.
- Primary qfa window: 2024-01-01 to 2025-12-31, 1Day bars.
- Temporary DB: `/var/folders/_5/pc0mst9956sdt25yf5hxh4vr0000gn/T/ar019-qfa-XXXXXX.sqlite3.MReGvgoxcP`; retained: false.

## Primary qfa metrics (pre-cost)

- Sharpe: -0.26783072
- Total return: -0.04554243
- Annualized return: -0.02321869
- Annualized volatility: 0.07674504
- Max drawdown: -0.12406996
- Win rate: 0.174
- Periods: 500

## Six random-window qfa checks

- Median Sharpe: -0.03281383
- Mean Sharpe: 0.0311809
- Median total return: -0.00219042
- Median max drawdown: -0.0520986

Window details:
- random1: 2021-03-01 to 2022-03-01; Sharpe 0.21936391; return 0.01068311; max DD -0.05514561; win rate 0.11507937; periods 252
- random2: 2021-11-15 to 2022-11-15; Sharpe -0.98200321; return -0.19587701; max DD -0.22464363; win rate 0.14342629; periods 251
- random3: 2022-07-01 to 2023-07-01; Sharpe 1.86695856; return 0.13758953; max DD -0.04046068; win rate 0.148; periods 250
- random4: 2023-02-01 to 2024-02-01; Sharpe 0.0137858; return -0.00045638; max DD -0.0490516; win rate 0.124; periods 250
- random5: 2024-06-01 to 2025-06-01; Sharpe -0.85160622; return -0.05212694; max DD -0.08193028; win rate 0.10483871; periods 248
- random6: 2025-01-15 to 2025-12-31; Sharpe -0.07941347; return -0.00392446; max DD -0.03256973; win rate 0.04583333; periods 240

## Costs, slippage, and orthogonality

- qfa costs applied: false. qfa currently has no native commission/slippage parameter; a 5 bps one-way traded-notional assumption is documented and would further reduce the already negative result.
- Orthogonality: {'status': 'computed_parent_watchlist_only', 'benchmark': 'AR-005 pairs-residual-megacap-tech-5d-v1', 'overlap_periods': 499, 'daily_return_correlation': 0.36679045}

## Decision

Reject. Primary Sharpe is negative and six-window median Sharpe is non-positive before costs. Per bad-result policy, no refinement/direct inversion/extension of this failed hypothesis is proposed. At most one divergent child idea is recorded in `latest.json`.
