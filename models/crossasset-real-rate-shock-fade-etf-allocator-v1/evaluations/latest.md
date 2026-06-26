# AR-109 Evaluation Summary

Suggested decision: **rejected**.

## Protocol

- Data: qfa/Alpaca real daily OHLCV via `AlpacaGateway`; no CSV and no `--data-csv`.
- Safety: no qfa daemon, no orders, no raw daily bars/SQLite/helper scripts retained.
- Universe fixed before performance review: `TLT, IEF, SHY, TIP, GLD, UUP, LQD, HYG, SPY, XLU`.
- Windows: primary plus 12 deterministic random/stress windows; primary cost gate 10 bps one-way turnover with 5/20 bps sensitivity.

## Key metrics

- Primary 10 bps Sharpe: `-0.825573`; annualized return `-0.017391`; max drawdown `-0.097563`; annualized turnover `18.440124`.
- Random/stress 10 bps Sharpe median/p25/worst: `-0.4513` / `-1.235847` / `-2.130862`.
- Positive random/stress window rate: `0.2`; worst 10 bps drawdown: `-0.070078`.
- Max available orthogonality/proxy absolute correlation: `0.431511`.

## Ablations (primary 10 bps Sharpe)

- no_GLD: `-0.927112` (return `-0.025187`, max DD `-0.130998`)
- no_TIP: `-0.905104` (return `-0.025274`, max DD `-0.134544`)
- no_UUP: `-1.044634` (return `-0.030229`, max DD `-0.158186`)
- no_stabilization: `-0.494914` (return `-0.013613`, max DD `-0.087379`)
- duration_neutral: `-1.391709` (return `-0.020981`, max DD `-0.113598`)
- equity_beta_neutral: `-0.840513` (return `-0.016557`, max DD `-0.093401`)
- shock_only_no_fade: `-1.153035` (return `-0.012363`, max DD `-0.0716`)

## Interpretation

Decision rationale: median random/stress Sharpe <= 0 after 10 bps; p25 random/stress Sharpe < 0 after 10 bps.

The result is a price-derived proxy test only; it should not be interpreted as direct evidence about real-rate futures, breakevens, or macro positioning.

Artifacts: `evaluations/latest.json`, this summary, and immutable run `ar109_qfa_alpaca_real_20260626T191525Z.json`.
