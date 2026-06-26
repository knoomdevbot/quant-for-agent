# credit-equity-stress-dispersion-reversion-v1

Research artifacts for **AR-044: Divergent from AR-025 — cross-asset credit/equity stress dispersion mean reversion**.

## Hypothesis

After large short-horizon dispersion between equity beta ETFs (`SPY`, `QQQ`, `IWM`) and credit/defensive proxies (`HYG`, `LQD`, `TLT`, `GLD`, `XLU`), liquid ETFs may mean-revert as stress premia normalize. This is intended to be a convergence/reversion mechanism, not AR-025's trend-following risk-on/risk-off switch.

## Implementation

`model.py` exposes qfa-compatible `generate_signals(context)` and uses only daily OHLCV already present in `context.prices`:

- 7-day equity-minus-credit/defensive return dispersion;
- short rolling z-score trigger;
- 1-2 day stabilization confirmation on the underperforming side;
- SPY realized-volatility ceiling;
- inverse-volatility-scaled market-neutral-ish long/short ETF basket, normalized by qfa.

The model is research-only and never places orders.

## Evaluation summary

Decision: **rejected**.

Primary qfa/Alpaca backtest, 2024-01-01 to 2025-12-31:

- qfa/pre-cost Sharpe: `-0.5202`; total return: `-5.4847%`; max drawdown: `-8.2675%`.
- External 5 bps one-way turnover-haircut Sharpe: `-0.9027`; total return: `-9.1492%`; max drawdown: `-10.3980%`.
- 10 random 252-trading-day windows: median cost-adjusted Sharpe `-1.0048`; positive Sharpe fraction `0.4000`.

The falsifier is triggered by non-positive random-period median Sharpe after the 5 bps turnover haircut and weak primary-period performance.

## Data and artifact discipline

- Data source: Alpaca real daily market data through qfa CLI and `AlpacaGateway`.
- No CSV files used; no `--data-csv` used.
- qfa ran with a temporary SQLite DB only; the DB was removed and `db_artifact_retained=false`.
- No qfa daemon and no trades.

## Files

- `model.py` — qfa model implementation.
- `config.yaml` — research/evaluation configuration.
- `metadata.yaml` — issue metadata and constraints.
- `evaluations/latest.json` — latest machine-readable evaluation.
- `evaluations/latest.md` — latest human-readable evaluation.
- `evaluations/runs/ar044_qfa_alpaca_real_20260626T095813Z.json` — immutable run artifact.
