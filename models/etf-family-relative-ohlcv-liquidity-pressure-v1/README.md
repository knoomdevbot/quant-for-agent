# AR-121 — ETF family-relative OHLCV liquidity-pressure proxy allocator

Decision: **rejected** after real qfa/Alpaca daily OHLCV testing.

## What was tested

A broad ETF pool spanning broad-index, sector, industry, duration, credit, commodity, international, factor/style, and real-asset ETFs was filtered before performance review by Alpaca daily-bar coverage, median dollar volume, and family diversity. The final 36-symbol universe was:

`SPY QQQ IWM IVV XLF XLE XLV XLK SMH GDX XBI KRE TLT IEF BIL SHY HYG LQD AGG JNK GLD SLV USO UNG EEM EFA FXI EWZ IWF IJR IWD VTV IYR VNQ XME URA`

The signal is a long-only cash-fallback allocator buying ETFs with negative family-relative OHLCV pressure: short-term return z-score, signed abnormal dollar volume, close-location, gap/intraday residual, and realized range. It cannot observe ETF flows, NAV, premium/discount, or creations/redemptions.

## Real-data result

- Data: qfa/Alpaca real daily OHLCV, configured paper-data access with credential values redacted.
- No CSV and no `--data-csv`; no daemon; no orders/trades.
- Evaluation: 24 random 504-trading-day windows, fixed universe, primary 10 bps one-way turnover cost plus 5/20 bps stress.

Primary 10 bps random-window summary:

| metric | median | mean | p25 | worst |
|---|---:|---:|---:|---:|
| Sharpe | -1.680 | -1.689 | -1.869 | -2.191 |
| Annual return | -31.36% | -33.89% | -45.78% | -52.85% |
| Annual vol | 20.35% | 23.04% | 17.06% | 14.53% |
| Max drawdown | -54.99% | -59.21% | -72.60% | -79.99% |
| Daily turnover | 1.676 | 1.679 | 1.663 | 1.644 |
| Annual turnover | 422.3 | 423.1 | 419.2 | 414.2 |
| Activation rate | 90.97% | 91.03% | 90.23% | 89.68% |
| Positive day rate | 37.20% | 36.52% | 34.28% | 32.34% |

Positive-window rate: **0.0%**.
Stress Sharpe medians: **-0.718 at 5 bps**, **-3.716 at 20 bps**.
Full-period 10 bps Sharpe: **-1.704**, annual return **-33.59%**, max drawdown **-96.21%**.

Ablations/baselines at 10 bps were also negative: ETF mean-reversion median Sharpe -2.952, TSMOM/defensive median Sharpe -0.220, no-volume median Sharpe -2.748, raw-not-family median Sharpe -1.237. The proposed full model did not beat the simple defensive/TSMOM baseline and was extremely cost/turnover fragile.

## Orthogonality

No compact prior-alpha daily return series were available in durable artifacts for a numeric correlation matrix. Conceptually, this idea overlaps heavily with AR-028/045/056 close-location/liquidity reversal and moderately with AR-015 ETF TSMOM and AR-037/049/051 carry/defensive allocators. The available baselines directly test those main explanations.

## Durable artifacts

- `model.py` — timestamp-safe implementation of the rejected signal.
- `config.yaml` — universe and parameters.
- `metadata.yaml` — compact provenance and key metrics.
- `evaluations/latest.json` and `evaluations/runs/ar121_qfa_alpaca_real_20260627T075912Z.json` — compact evaluation payload; no raw bars/equity curves/daily returns.
- `evaluations/latest.md` — this summary.
