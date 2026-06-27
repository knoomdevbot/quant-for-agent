# AR-018 Evaluation: overnight-gap-reversal-event-megacap-v1

- Created at: `2026-06-26T07:38:09Z`
- Data: Alpaca real daily OHLCV via qfa/AlpacaGateway only; no CSV and no `--data-csv`.
- Symbols: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA
- Primary window: 2024-01-01 to 2025-12-31
- qfa DB used: `/tmp/qfa_ar018_20260626T003612_295.sqlite3` (not retained)
- qfa run id: `1`
- Decision: **rejected**

## Primary qfa proxy metrics, pre-cost

```json
{
  "annualized_return": -0.11359256,
  "annualized_volatility": 0.24613203,
  "final_equity": 78722.3405,
  "initial_cash": 100000.0,
  "max_drawdown": -0.32068938,
  "periods": 500,
  "sharpe": -0.36424762,
  "total_return": -0.2127766,
  "win_rate": 0.166
}
```

## Intended open-to-close harness, 5 bps cost-adjusted

```json
{
  "annualized_return": 0.27020264,
  "annualized_volatility": 0.22963229,
  "final_equity": 160882.7345,
  "initial_cash": 100000.0,
  "max_drawdown": -0.17053299,
  "periods": 501,
  "sharpe": 1.15561986,
  "total_return": 0.60882734,
  "win_rate": 0.20558882
}
```

## Random-window result

- Completed windows: 30
- Median cost-adjusted Sharpe: `-0.50714055`
- Positive cost-adjusted Sharpe fraction: `0.36666667`
- Median cost-adjusted return: `-0.15349145`
- Median cost-adjusted max drawdown: `-0.20683642`

## Notes

Rejected: primary qfa proxy Sharpe is negative and intended open-to-close random-window median cost-adjusted Sharpe is non-positive after 5 bps one-way turnover cost.

qfa cannot exactly enter at the same-day open and exit at the same-day close using daily bars. The durable qfa model is therefore a lagged proxy, and the evaluation includes a direct Alpaca OHLC open-to-close harness for the intended mechanism. qfa costs are not applied because the current qfa CLI has no cost/slippage parameter; the direct harness applies 5 bps one-way turnover cost.
