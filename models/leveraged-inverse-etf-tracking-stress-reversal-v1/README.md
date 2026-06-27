# AR-124: leveraged/inverse ETF tracking-stress reversal

Research-only qfa alpha model for issue AR-124. Leveraged and inverse ETFs are used only as signal inputs; non-zero target weights are emitted only for unlevered underlying ETFs.

## Hypothesis

Close-to-close residuals of leveraged/inverse ETF returns versus stated multiples of underlying ETF returns may proxy short-lived product tracking/rebalance stress. Daily OHLCV cannot observe NAV premium/discount, creations/redemptions, borrow, flow, or actual hedge trades, so this is explicitly a tracking-stress proxy rather than a direct mechanism measurement.

## Predeclared universe protocol

Candidate pool: broad index, sector/industry, real-estate, retail/homebuilder, and Treasury underlyings with related leveraged/inverse products:

- SPY with SH/SDS/SSO/UPRO/SPXU
- QQQ with PSQ/QID/QLD/TQQQ/SQQQ
- IWM with TWM/UWM/TNA/TZA
- XLE with ERX/ERY; XLF with FAS/FAZ; XLK with TECL/TECS
- SMH with SOXL/SOXS; XBI with LABU/LABD; IYR with URE/SRS
- XRT with RETL; XHB with NAIL
- TLT with TBT/UBT/TMF/TMV

Filters used before performance review: real Alpaca daily coverage, at least 750 overlapping close-to-close returns, 63-day median underlying dollar volume >= $10M, and signal ETF dollar volume >= $1M.

## Model

For each selected mapping, compute daily residual `r_signal_etf - stated_multiple * r_underlying`, z-score over 60 sessions, sign by bull/bear orientation, average within an underlying family, scale by same-day range/volume stress, and trade the predeclared reversal sleeve in the unlevered underlying on D+1. Signal ETFs are always flat.

## Evaluation result

Decision: **rejected**.

Primary 10 bps one-way reversal sleeve metrics:

- Median random-window Sharpe: -2.4435
- p25 random-window Sharpe: -3.1917
- Positive-window rate: 2.5%
- Full-sample Sharpe: -2.0025
- Max drawdown: -97.98%
- Average daily turnover: 1.1241
- Activation: 59.85%

The continuation diagnostic was also negative, and multiple mandatory ablations beat the primary despite generally poor absolute performance. 20 bps costs further degraded results. Orthogonality was marked unavailable/deferred and was not used to rescue the failed result.

## Artifacts

- `model.py` qfa `generate_signals(context)` contract implementation
- `config.yaml` model and safety parameters
- `metadata.yaml` compact metadata
- `evaluations/latest.json` compact machine-readable evaluation
- `evaluations/latest.md` human-readable summary
- `evaluations/runs/ar124_qfa_alpaca_real_20260627T122001Z.json` immutable run copy
