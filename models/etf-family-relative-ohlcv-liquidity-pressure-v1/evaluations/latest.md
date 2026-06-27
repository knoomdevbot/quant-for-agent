# AR-121 latest evaluation — ETF family-relative OHLCV liquidity-pressure proxy allocator

**Decision:** rejected.

**Protocol:** qfa/Alpaca real daily OHLCV only; no CSV, no `--data-csv`, no daemon, no orders. Candidate pool covered broad-index, sector, industry, duration, credit, commodity, international, factor/style, and real-asset ETFs. Final 36-symbol universe was selected before performance review by coverage, liquidity, and family diversity.

**Selected symbols:** SPY, QQQ, IWM, IVV, XLF, XLE, XLV, XLK, SMH, GDX, XBI, KRE, TLT, IEF, BIL, SHY, HYG, LQD, AGG, JNK, GLD, SLV, USO, UNG, EEM, EFA, FXI, EWZ, IWF, IJR, IWD, VTV, IYR, VNQ, XME, URA.

## Primary 10 bps random windows

| Metric | Median | Mean | P25 | Worst |
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

## Cost stress and baselines

- Stress Sharpe median: 5 bps **-0.718**, 20 bps **-3.716**.
- Full-period 10 bps: Sharpe **-1.704**, annual return **-33.59%**, max drawdown **-96.21%**, annual turnover **425.9**.
- 10 bps baseline/ablation median Sharpe: ETF mean-reversion **-2.952**, TSMOM/defensive **-0.220**, no-volume **-2.748**, raw-not-family **-1.237**.

## Interpretation

Reject. The OHLCV liquidity-pressure proxy is not merely weak; it is negative in every random window and highly turnover/cost fragile. It fails the median Sharpe, p25 Sharpe, positive-window-rate, 20 bps stress, and baseline-superiority gates. Daily OHLCV cannot observe true ETF flows/NAV/premium-discount, and compact prior return series were unavailable for numeric orthogonality, so orthogonality is reported as conceptual/proxy-limited.
