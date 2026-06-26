# AR-044 Evaluation — credit-equity-stress-dispersion-reversion-v1

## Suggested decision

**REJECTED** — Fails falsifier: non-positive random-period median Sharpe after 5 bps turnover haircut and/or weak primary result.

## Data and command discipline

- Data source: Alpaca real daily OHLCV through qfa CLI / `AlpacaGateway`; no CSV files and no `--data-csv`.
- Symbols: SPY, QQQ, IWM, TLT, GLD, HYG, LQD, XLU.
- Primary window: 2024-01-01 to 2025-12-31; random protocol: 10 sampled 252-trading-day windows from 2019-01-01 to 2025-12-31.
- qfa primary CLI run id: `1`; direct qfa Python engine id: `direct_python_qfa_engine_no_store`.
- Temporary DB used during run: `/tmp/ar044-qfa-XXXXXX.sqlite3`; DB artifact retained: `false`.
- Immutable run JSON: `/Users/moonk/quant-for-agent/models/credit-equity-stress-dispersion-reversion-v1/evaluations/runs/ar044_qfa_alpaca_real_20260626T095813Z.json`.

## Primary metrics

- qfa/pre-cost Sharpe: `-0.5202`; total return: `-0.0548`; max drawdown: `-0.0827`; periods: `500`.
- 5 bps one-way turnover haircut Sharpe: `-0.9027`; total return: `-0.0915`; annualized return: `-0.0472`; max drawdown: `-0.1040`.
- Average daily one-way turnover proxy: `0.158126`; active-day fraction: `0.1380`.

## Random-window results

- Median random-window cost-adjusted Sharpe: `-1.0048`.
- Positive cost-adjusted Sharpe fraction: `0.4000`.
- Median cost-adjusted annualized return: `-0.0259`.
- Median cost-adjusted max drawdown: `-0.0339`.

## Orthogonality

Status: `unavailable`; redundancy assessment: `unknown`; max absolute primary daily correlation where computed: `None`.

## Costs and caveats

qfa has no native cost/slippage parameter in this repo, so primary and random-window results apply an external 5 bps one-way daily target-weight turnover haircut. The model is a daily close-to-close proxy and does not model bid/ask, market impact, short borrow, or intraday execution.
