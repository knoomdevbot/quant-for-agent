# stress-gap-reversal-etf-v1

AR-026 tested a divergent stress-day gap-reversal idea for liquid ETFs: after a broad negative overnight gap in SPY/QQQ/IWM, allocate long to risk ETFs (SPY, QQQ, IWM, XLE) using inverse trailing volatility weights.

## Data and execution

- Data source: Alpaca real market data through qfa/`AlpacaGateway`; `--data-csv` was not used.
- Symbols: SPY, QQQ, IWM, TLT, GLD, XLU, XLE.
- Range: 2021-01-01 to 2026-06-24, daily bars.
- No daemon was run and no trades were placed.
- qfa limitation: the daily qfa engine cannot enter at the just-observed open and exit later, so `model.py` is a lagged close-to-close proxy. The intended same-day open-to-close horizon was measured with a direct Alpaca OHLC research harness.

## Result

Rejected. The qfa close-to-close proxy was only slightly positive gross/pre-cost, but the intended open-to-close strategy failed after a 5 bps per-side cost haircut.

- Primary open-to-close, 5 bps per side: Sharpe -0.202; total return -8.36%; max drawdown -15.98%; win rate 6.85%; 1,373 periods; 189 event days.
- qfa close-to-close gross proxy: Sharpe 0.062; total return 0.98%; max drawdown -21.80%; 1,372 periods.
- Random windows: 10 windows x 126 trading days; median Sharpe -0.575; median total return -1.73%; median max drawdown -2.98%.

The result fails the AR-026 falsifier (non-positive random-period median Sharpe after costs). Per bad-result policy, no refinement, direct inversion, or extension of this failed stress-gap reversal hypothesis is proposed.

## Artifacts

- `model.py`
- `config.yaml`
- `metadata.yaml`
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/ar026_alpaca_qfa_stress_gap_reversal_20260626T080919Z.json`
