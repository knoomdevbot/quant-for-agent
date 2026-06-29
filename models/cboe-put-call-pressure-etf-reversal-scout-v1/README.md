# CBOE put/call pressure ETF reversal scout (AR-148)

Decision: **rejected**.

## What was tested

- Reconstructed CBOE daily options market-statistics pages with `dt=YYYY-MM-DD` from 2019-10-07 through the qfa/Alpaca overlap ending 2026-06-26.
- Parsed aggregate put/call ratios for total, index, ETP, equity, VIX, and SPX+SPXW categories plus category volume/open-interest pressure.
- Evaluated conservative T+1 primary lag and T+2 diagnostics against real Alpaca daily ETF bars for SPY, QQQ, IWM, DIA, XLK, XLF, XLE, XLU, TLT, IEF, and SHY.
- Costs: 10 bps one-way primary; 5/20 bps sensitivity.

## Result

The source gate passed: 1,689 Alpaca trading dates matched 1,689 CBOE parsed dates with no missing required ratio fields.  Performance gates failed after costs.  The best T+1 scout variant used a 126-day z-score lookback and 95% extreme threshold, but produced negative primary and random-window results.

Key metrics are in `evaluations/latest.json`; no raw CBOE daily pages, raw Alpaca bars, equity curves, weights, SQLite databases, caches, or bytecode are retained.

## Runtime behavior

Because the alpha was rejected, `model.py` exposes `generate_signals(context)` as a neutral-weight implementation for the selected ETF universe rather than scraping CBOE at runtime.
