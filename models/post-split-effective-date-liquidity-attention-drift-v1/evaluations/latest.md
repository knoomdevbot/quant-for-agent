# AR-124 latest evaluation — post-split effective-date liquidity/attention drift

Decision: **rejected**

Hypothesis: Liquid U.S. equities may exhibit short-horizon drift after forward split effective/ex/process dates due to post-split attention/liquidity effects; reverse/unit splits are diagnostics only.

Falsifier: Reject if post-effective forward split returns do not clear costs, have weak hit rate/p25, are sparse/concentrated, or fail placebo/momentum/reversal/beta baselines.

Data: Alpaca corporate-action split records plus qfa/Alpaca real daily OHLCV only. No CSV, no daemon, no orders. Raw daily bars were not retained.

Primary sleeve: liquid forward splits only; entry is the first available trading close strictly after the ex/process date, so there is no announcement-time assumption and no pre-event exposure. Reverse/unit splits are diagnostics only.

Universe: 74 candidate forward-split symbols (79 forward records); selected 12 liquid symbols: AAON, AIV, AMZN, ANET, APG, APH, AVGO, BEPC, BKNG, BN, CELH, CHDN.

Primary 5d/10bps metrics: event_count=14, mean_event_return=0.011583966966923733, median_event_return=0.0029169866781636475, p25=-0.01824960737314596, hit_rate=0.5, Sharpe=0.24051245571111418, ann_return_proxy=0.025014617856995148, ann_vol_proxy=0.1040054985220427, max_drawdown=-0.18825879818752334, turnover=0.01880456682337139.

Decision rationale:
- primary p25 event return materially negative
- primary hit/positive-window rate below 55%
- event count too sparse for robust watchlist

Orthogonality: deferred_due_rejection; beta proxy corr to SPY same windows = 0.7013477491924412.

Immutable run: `/Users/moonk/quant-for-agent/models/post-split-effective-date-liquidity-attention-drift-v1/evaluations/runs/ar124_qfa_alpaca_real_20260627T200624Z.json`
