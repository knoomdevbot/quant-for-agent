# AR-115 evaluation latest

- Run: `ar115_qfa_alpaca_real_20260626T2257Z`
- Data: qfa/Alpaca real daily OHLCV; no CSV, no data-csv argument, no daemon, no orders.
- Selected trade ETFs: XLK, XLY, XLC, XLF, XLV, XLE, XLP, XLI, XLU, XLRE, XLB
- Primary 10 bps Sharpe: **-1.2639**; annualized return -0.103821; max drawdown -0.49993; mean turnover 0.366369; activation days 331.
- Random windows (30 x ~1y): median Sharpe **-1.4435**, p25 **-2.0952**, worst **-2.523**, positive-window rate **0.0667**.
- Cost sensitivity Sharpe: 5 bps -0.7187; 10 bps -1.2639; 20 bps -2.3094.
- Ablations: sector ETF-only -0.9808; no-calendar -1.2604; no-abnormal-volume -1.7221; no-close-location -1.2038; no-SPY-residual -1.3159; continuation-only -1.2639; reversal-only -0.9427; generic momentum -1.1607; generic reversal -0.8083.
- Orthogonality max abs proxy correlation: 0.2494.
- Suggested decision: **rejected**.

Warnings: Primary 10 bps Sharpe is not positive.; Random-window p25 Sharpe is below -0.10 gate.; Positive-window rate is below 55% gate.; Primary does not beat sector ETF-only baseline Sharpe.; 20 bps cost sensitivity Sharpe is not positive.
