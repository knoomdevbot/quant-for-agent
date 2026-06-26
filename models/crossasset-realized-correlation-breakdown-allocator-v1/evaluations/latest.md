# AR-080 Evaluation Latest

Decision: **REJECT**

- Primary qfa run id: `1`
- Data: Alpaca real daily OHLCV via qfa/AlpacaGateway only; no CSV, no daemon, no orders.
- Temporary SQLite DB retained: false

## Metrics

- median_sharpe: 0.0
- p25_sharpe: -0.8103479
- worst_period_sharpe: -1.19800957
- annualized_return: -0.00252675
- annualized_volatility: 0.07110019
- max_drawdown: -0.2199614
- turnover/proxy: 64.78318122
- positive_window_rate: 0.44444444
- max_abs_orthogonality_correlation: 0.76185761

## Warnings

- qfa native backtest metrics are pre-cost; reported decision metrics apply an external 5 bps one-way turnover-cost proxy.
- Orthogonality is computed only where retained latest.json equity curves are available; missing curves are explicitly marked in JSON.

## Suggested decision

reject: Rejected: random-window p25 Sharpe was negative and/or max available retained-curve correlation breached 0.60.
