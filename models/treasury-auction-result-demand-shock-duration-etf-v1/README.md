# Treasury auction-result demand shock duration ETF scout (AR-148)

Official Treasury FiscalData nominal note/bond auction results were joined to real qfa/Alpaca daily ETF bars. The implementation uses trailing same security type/term z-scores for award yield/high yield, bid-to-cover, and bidder takedown mix. It does **not** claim a true when-issued tail.

Entry is conservative: first signal at the close of the next regular Alpaca session after `auction_date`, held for five decision sessions.

Decision: **rejected**.

Primary 10 bps Sharpe: -0.74600738; total return: -0.29075908; max drawdown: -0.34537805; activation: 0.40505549.
Random windows: median Sharpe -1.11826361, p25 -1.63386596, worst -1.936016, positive-window rate 0.0.

Selected universe: SHY, IEI, IEF, TLT, GOVT, EDV, ZROZ, TIP, SCHP, LQD, HYG, MBB, AGG, BND, XLF, KRE, XLU, XLRE, SPY, QQQ.

Warnings: No timestamp-safe when-issued source used; high-yield/award-rate surprise is trailing same-type/term auction history z-score only, not true WI tail.; Conservative next-regular-session close entry used because FiscalData rows do not document machine-readable result-publication timestamps in this evaluation.; FOMC/CPI/payroll diagnostic uses coarse calendar-rule exclusion only; no official macro calendar retained.
