# AR-150 TIC foreign Treasury-flow pressure ETF scout evaluation

Decision: **rejected**. Source/vintage gate passed for 2021+ official dated Treasury TIC release ZIPs, but the fixed flow-pressure allocator failed acceptance controls.

Key metrics (10 bps one-way): full-sample Sharpe -0.587, annualized return -3.418%, max drawdown -12.418%. Random windows: median Sharpe -0.511, p25 -0.852, positive-window rate 25.5%. Max abs control correlation 0.989.

Provenance: official Treasury TIC dated `ticrel_YYYYMMDD.zip` archives for signal; transient real adjusted ETF daily closes from Yahoo Finance chart API for prices because configured paper brokerage data access was unavailable in this environment. No qfa `--data-csv`, no daemon, no orders, and no raw bars/ZIPs retained.

Primary rejection reasons: median_random_window_sharpe_not_positive, p25_random_window_sharpe_materially_negative, positive_window_rate_below_55pct, max_control_correlation_above_0p60, full_sample_post_cost_sharpe_not_positive.
