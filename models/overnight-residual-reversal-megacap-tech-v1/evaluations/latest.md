# AR-020 evaluation — overnight residual reversal mega-cap tech v1

Status: **rejected**

## Data and execution

- Data source: Alpaca real market data only via qfa/AlpacaGateway; no CSV.
- Symbols: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA.
- Direct harness date range: 2021-01-01 to 2026-06-24; qfa proxy range: 2024-01-01 to 2025-12-31.
- Temporary qfa DB: `/var/folders/_5/pc0mst9956sdt25yf5hxh4vr0000gn/T/ar020-qfa-3i_ba05y.sqlite3`; retained: false.
- qfa run id: `1`.
- No daemon, no live trading, no orders.

## qfa limitation

qfa daily bars cannot exactly enter at same-day open and exit at same-day close after observing the open. The qfa model is a lagged close-to-close proxy. The primary decision uses a direct Alpaca OHLC open-to-close harness.

## Primary metrics

- Open-to-close 5 bps Sharpe: `-0.9402`
- Open-to-close 5 bps total return: `-43.75%`
- Open-to-close 5 bps max drawdown: `-44.33%`
- Open-to-close 5 bps win rate: `18.65%`
- Periods: `1373`
- Event days: `548`

## Random-window robustness

- Windows: `30` of `126` trading days, seed `20020`.
- Median Sharpe: `-0.8319`
- Mean Sharpe: `-0.7229`
- Median annualized return: `-7.88%`
- Median max drawdown: `-7.69%`

## qfa proxy smoke metrics

- Sharpe: `-0.7562`
- Total return: `-17.34%`
- Max drawdown: `-19.20%`
- Win rate: `14.80%`
- Periods: `500`

## Decision

Primary 5 bps open-to-close Sharpe -0.940, total return -43.75%, max drawdown -44.33%, random-window median Sharpe -0.832.

Suggested decision: **Do not promote; research reference only.**

## Child policy

rejected result: no refinement, direct inversion, or extension of the failed overnight residual open-to-close reversal hypothesis; at most one divergent child with a different mechanism is recorded
