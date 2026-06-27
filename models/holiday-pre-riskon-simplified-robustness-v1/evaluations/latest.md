# AR-129 Evaluation: holiday-pre-riskon-simplified-robustness-v1

Data: Alpaca real daily OHLCV via configured paper-data access (redacted), IEX feed requested. No CSV, no --data-csv, no daemon, no orders.

Bug fix: event construction now requires the true pre-holiday trading session to be present and 1-3 calendar days before a full-day NYSE holiday. The stale 2026-06-26 duplicate future-holiday events were removed.

Universe fixed before performance review: SPY, QQQ, IWM, MDY, EFA, EEM, HYG, LQD, VCIT from candidates SPY, IVV, VOO, QQQ, IWM, MDY, DIA, VTI, EFA, IEFA, EEM, VEA, HYG, JNK, LQD, VCIT, VCSH, AGG using broad risk-on exposure, common IEX daily coverage from 2020-07-27, and liquidity/availability filters.

Primary net 10 bps one-way (20 bps round-trip) metrics: n=58, median=-0.0569%, p25=-0.3176%, worst=-1.2518%, hit_rate=43.1%, event_sharpe=-0.87, max_dd=-4.93%.

Robustness: ex-calendar-overlap median=0.0422%, p25=-0.0728%; placebo median-rank=0.901; positive-year-rate=28.6%; positive-family-rate=50.0%; max relevant corr=0.068.

Decision: **rejected**. Acceptance gates: `{"ex_overlap_median_gt_0": true, "ex_overlap_p25_near_zero_or_better": true, "hit_rate_ge_55": false, "max_relevant_corr": 0.0684019493707905, "max_relevant_corr_le_060": true, "median_gt_0": false, "no_single_year_family_dependence": false, "placebo_rank_ge_085": true, "suggested_decision": "rejected"}`

Warnings: Uses current ETF symbols; survivorship/availability bias possible.; NYSE holiday/early-close calendar generated from public rules plus 2018 national mourning closure; not an exchange API calendar.; Daily-bar close-to-close implementation cannot verify intraday early-close execution quality.
