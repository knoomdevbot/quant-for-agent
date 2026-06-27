# turn-month-calendar-window-etf-v1

AR-021 research model: exchange-session-aware refinement of AR-006 turn-of-month ETF seasonality.

## Hypothesis
Month-end/month-start institutional flows may create predictable ETF returns, but the AR-006 calendar rule should use observed exchange sessions rather than synthetic weekdays. This model holds broad liquid ETFs during the final 1 observed market session and first 4 observed market sessions of each month.

## Model
- QFA entry point: `generate_signals(context)` in `model.py`.
- Universe: SPY, QQQ, IWM, TLT, GLD.
- Signal: long-only equal-weight basket during the exchange-session-aware turn-of-month window; flat otherwise.
- Calendar handling: valid sessions are inferred from Alpaca/qfa price timestamps already in `context.prices`, so holidays/missing non-sessions are not treated as trading days.
- Risk: model caps single-symbol pre-engine weight at 25%; qfa then normalizes gross exposure.

## Latest real-data evaluation
- Data source: Alpaca real market data via qfa AlpacaGateway only.
- `--data-csv`: not used.
- Backtest window: 2021-01-01 to 2025-12-31, timeframe 1Day.
- Primary qfa run id: 1.
- Random-window qfa run ids: 2, 3, 4, 5, 6, 7, 8, 9.
- Runtime DB: `/tmp/qfa_ar021.sqlite3`; DB artifact removed/not retained.
- Costs/slippage: qfa has no native cost/slippage flag, so `latest.json` includes an ex-post 5 bps per estimated gross-turnover event haircut.
- No trades were placed; qfa daemon was not run.

## Primary metrics
Pre-cost qfa metrics:
- Total return: 0.47031678
- Annualized return: 0.08061063
- Annualized volatility: 0.13355703
- Sharpe: 0.64718778
- Max drawdown: -0.26322576
- Win rate: 0.53232243
- Periods: 1253

Cost-haircut metrics:
- Total return: 0.3833081
- Annualized return: 0.0674345
- Annualized volatility: 0.13358099
- Sharpe: 0.55523109
- Max drawdown: -0.27131907
- Win rate: 0.528332
- Periods: 1253

## Random-window validation
8 seeded random windows over 2021-2025 were run with qfa/Alpaca real data.

Cost-haircut Sharpe summary:
- Min: -1.43748385
- Median: 0.5829092
- Mean: 0.29564799
- Max: 1.38249264

Cost-haircut total-return summary:
- Min: -0.18393039
- Median: 0.05463321
- Mean: 0.02601957
- Max: 0.17756052

## Orthogonality
Daily equity-curve return correlation versus parent `turn-month-liquid-etf-seasonality-v1` over 499 overlapping periods: 0.50325754. This is moderately correlated, so it is a refinement rather than a diversifying standalone alpha.

## Artifacts
- `model.py`
- `config.yaml`
- `metadata.yaml`
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/qfa_real_alpaca_ar021_20260626T075853Z.json`

## Suggested decision
Watchlist / continue research, non-rejected: median random-window Sharpe remains positive after the cost haircut, but negative windows and drawdown show material regime fragility. Not production-ready.

## Child ideas
- Refinement child: AR-041 volatility/regime-gated turn-of-month ETF seasonality using the same exchange-session window and explicit turnover haircut.
- Divergent child: AR-042 ETF flow pressure around scheduled macro/liquidity dates using cross-asset breadth rather than calendar month-boundaries.
