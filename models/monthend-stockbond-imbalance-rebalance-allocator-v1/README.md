# AR-125 monthend-stockbond-imbalance-rebalance-allocator-v1

Hypothesis: completed-month equity-vs-bond performance gaps induce balanced-fund/pension rebalancing pressure near month end. The primary rule trades the last-2/first-2 trading-day window in the reversal direction: after equity outperformance, long bonds/short equities; after bond outperformance, long equities/short bonds.

Falsifier: reject if 10 bps cost-adjusted random/month-subset event Sharpe is not positive with p25 near/above zero, if generic turn-of-month or simple momentum/reversal explains the returns, if placebo dates are comparable, or if correlation to retained watchlist alphas is too high.

Universe was fixed before performance review from broad liquid ETFs with Alpaca daily bars: SPY/QQQ/IWM/DIA and sectors for equity exposure; TLT/IEF/SHY/LQD/HYG/AGG/BND/TIP for duration/credit/inflation-linked bonds; GLD/UUP as controls only. Data access used configured paper Alpaca credentials with values redacted. No CSV, no `--data-csv`, no qfa daemon, and no orders.
