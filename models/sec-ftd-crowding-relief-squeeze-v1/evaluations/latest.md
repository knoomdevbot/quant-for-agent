# AR-138 SEC FTD crowding relief/squeeze allocator

Decision: **rejected**.

Data/provenance: SEC official FTD archives and configured paper-data Alpaca real daily OHLCV; no CSV, no --data-csv, no qfa daemon, no orders. Credentials were transient and not persisted.

Universe: 97 selected symbols from 178 liquid Alpaca-covered clean SEC symbols. Filters: clean common/ETF-like 1-5 letter symbols, price >= $5, median dollar volume >= $5M, real daily bar coverage; excludes obvious OTC/preferred/warrant/unit suffixes by symbol ambiguity filter. Limitations: SEC symbol field used instead of PIT CUSIP map; active Alpaca coverage survivorship; publication date approximated as settlement+20 calendar days then next trading day.

Events: 508 selected events from 108060 feature-complete FTD records; rule q97_ftd_vol_ratio_and_ret10_le_-5pct value 2.822; 10d long-only equal-weight hold, 10 bps one-way cost.

Metrics: primary Sharpe 0.509, annual return 125.561%, vol 684.071%, max drawdown -47.599%, mean turnover 0.2075. Random 2y windows: median Sharpe -0.016, p25 -0.856, worst -1.247, positive-window 46.0%.

Controls: shifted +60d Sharpe 0.509; FTD-only 0.771; pre-return-only sample 0.676; random matched non-event -0.458. Leave-year Sharpe: {'2019': 0.0, '2020': -0.47030544744679165, '2021': 0.5516535840075503, '2022': -1.185570567496748, '2023': -1.265247524977247, '2024': 1.0802440263682045, '2025': 1.2021903304284356}.

Acceptance: fail_reject. Child ideas warranted: no; rejected fast-falsification artifact.
