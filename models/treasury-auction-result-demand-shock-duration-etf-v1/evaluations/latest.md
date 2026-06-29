# AR-148 evaluation latest

- Decision: **rejected**
- Source gate: 612 nominal note/bond auctions with required result fields and qfa/Alpaca bar coverage; passed=True
- Universe: SHY, IEI, IEF, TLT, GOVT, EDV, ZROZ, TIP, SCHP, LQD, HYG, MBB, AGG, BND, XLF, KRE, XLU, XLRE, SPY, QQQ
- Primary 10 bps: Sharpe -0.74600738, total return -0.29075908, max DD -0.34537805, turnover total 297.0, activation 0.40505549
- Sensitivity: 5 bps Sharpe -0.41003735; 20 bps Sharpe -1.40252951
- Random windows: median Sharpe -1.11826361; p25 -1.63386596; worst -1.936016; positive-window rate 0.0
- Controls: shifted 21d Sharpe -1.11316418; matched non-auction Sharpe -1.04058528; AR-108 calendar baseline Sharpe -0.38599012; AR-109 real-rate proxy Sharpe -0.52367035; AR-123 payment-day proxy Sharpe -2.01046305; TSMOM Sharpe -0.50764776; reversal Sharpe -0.06878502; ex coarse FOMC/CPI/payroll Sharpe -1.03658495
- Rate beta diagnostics: corr TLT -0.00371; beta TLT -0.009057
- Provenance: no CSV, no `--data-csv`, no daemon, no orders, no raw daily returns/equity/weights arrays retained.
- Warning: no timestamp-safe WI source; signal uses trailing same-type/term history z-scores, not true when-issued tail.

Run JSON: `models/treasury-auction-result-demand-shock-duration-etf-v1/evaluations/runs/ar148_qfa_alpaca_fiscaldata_real_20260629T162845Z.json`
