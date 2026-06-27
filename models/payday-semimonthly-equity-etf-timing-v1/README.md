# Payday semi-monthly equity ETF timing v1 (AR-110)

Rule-based research model for the fixed payday/semi-monthly contribution-flow hypothesis: hold **SPY** for the first tradable session on or after the 16th calendar day of each month. Broad ETF panel results are diagnostic only and were not used for selection.

## Guardrails
- qfa/Alpaca real daily market data only; no CSV and no `--data-csv`.
- No daemon, no orders, no retained raw bars/equity curves/weights tails/SQLite/caches/helper evaluator scripts.
- SPY is the only selected trading universe; broad ETFs are diagnostics only.

## Latest decision
**REJECTED** — 10 bps median/p25 random-window Sharpe and required calendar ablations fail acceptance gates.

Key 10 bps SPY metrics: Sharpe 0.057949, annualized return 0.001679, max drawdown -0.157784, activation 0.048452, annualized turnover 24.419919.

Random/stress 10 bps: median Sharpe -0.754028, p25 -1.019815, worst -1.229227, positive-window rate 0.0.

See `evaluations/latest.json` and `evaluations/latest.md`.
