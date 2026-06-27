# AR-122 evaluation: macro-shock defensive relative stabilization

Decision: **reject**.

Data: Alpaca real daily OHLCV (IEX feed requested), 2018-01-01 to 2026-06-26; no CSV, no data-csv, no daemon, no orders. Selected universe fixed before performance review with coverage/liquidity filters: SPY, QQQ, IWM, DIA, USMV, SPLV, QUAL, MTUM, XLK, XLY, XLP, XLV, XLU, XLF, XLI, XLE, XLB, XLRE, XLC, HYG, LQD, SHY, IEF, TLT, TIP, GLD.

Primary 10 bps metrics: Sharpe -0.595, ann return -3.202%, ann vol 5.383%, max DD -20.595%, turnover 0.068, activation 16.880%.

Random 126d windows: count 200, median Sharpe -0.683, mean -0.762, p25 -1.591, worst -3.296, positive rate 18.000%.

Event windows: 51 active events, 33 independent shock clusters, hit rate 0.39215686274509803, mean event return -0.0022739817780815666.

Baselines / orthogonality: shock-only, defensive carry, ETF TSMOM, and pullback proxy evaluated with same 10 bps cost. Proxy correlations: {"defensive_carry": 0.32457694738442916, "pullback_proxy": 0.13183134859859258, "shock_only": 0.36308301118013225, "tsmom": 0.2800363662504289}.

Recommendation: reject. The acceptance gate required positive median/p25 random-window Sharpe, >55% positive windows, enough independent shock clusters, and proxy correlations <=0.60. See latest.json for compact full metrics and limitations.
