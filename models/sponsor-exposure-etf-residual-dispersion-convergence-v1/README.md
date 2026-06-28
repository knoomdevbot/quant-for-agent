# Sponsor/exposure ETF residual-dispersion convergence v1 (AR-132)

Research-only qfa alpha model for fixed sponsor-and-exposure ETF clusters. The sponsor label is used only as an ex-ante clustering label and is not interpreted as creation/redemption, flow, or sponsor-behavior evidence.

## Signal

- Inputs: completed daily OHLCV close-derived returns from qfa/Alpaca only.
- Estimate each ETF sleeve's residual return versus a broad exposure proxy using trailing data.
- Require broad/exposure stress or elevated trailing exposure volatility, then require an unusually high within-cluster residual-dispersion z-score.
- Fade lagged residual outliers within cluster with caps; target horizon is the next 3-5 daily bars through repeated daily re-evaluation.
- Excluded by design: abnormal volume, close-location, range, gap/close residuals, and liquidity-pressure composites.

## Universe

Started from a broad candidate pool of liquid US-listed SPDR, iShares, and Vanguard broad/style/sector/factor ETFs. The selected universe is restricted to symbols with qfa/Alpaca daily coverage, sufficient liquidity, and fixed sponsor/exposure cluster mapping with at least two comparable products. Sector/factor sleeves were mostly excluded from the final traded set because the strict same-sponsor exposure-matched cluster requirement produced too few duplicates.

## Evaluation result

Real-data qfa/Alpaca daily evaluation was decisively negative after transaction-cost haircuts.

- Decision: rejected
- Primary 10 bps full-period Sharpe: -0.97685593
- Random-window median/p25/worst Sharpe: -1.0045856 / -1.60790097 / -2.94216707
- Random-window positive rate: 0.20
- 20 bps sensitivity Sharpe: -2.67529997
- Orthogonality: deferred due to decisive rejection.

See `evaluations/latest.json`, `evaluations/latest.md`, and immutable run JSON under `evaluations/runs/`.

No CSV, no `--data-csv`, no daemon, no orders, no raw bars retained.
