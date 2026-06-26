# AR-091 Evaluation — Polymarket Macro Probability Shock ETF Allocator

**Status:** blocked / reject for this pass
**Created:** 2026-06-26T15:53:21Z

## Summary
The alpha was not promoted to qfa performance testing because the required external prediction-market signal could not be established with reproducible point-in-time market discovery/history discipline. I did not fabricate proxies.

## External data check
Public Polymarket endpoints were probed without secrets:

- `https://gamma-api.polymarket.com/markets?limit=3&active=true&closed=false`
- `https://clob.polymarket.com/markets?next_cursor=`
- `https://clob.polymarket.com/prices-history?market=<token_id>&interval=1w&fidelity=1440`

Requests without browser user-agent returned HTTP 403; with browser user-agent, current snapshots and token-level history were reachable. However, a defensible historical macro market-universe archive was not available/committed. Selecting macro markets after the fact and replaying their token histories would create ex-post selection/lookahead risk.

## Universe
Candidate and selected research pool before performance evaluation:

SPY, QQQ, IWM, TLT, IEF, SHY, GLD, HYG, LQD, XLE, XLU, XLV, XLF, KRE, ITA, XLI, XLP, XLY, FXI, EEM, USO, UUP.

## QFA / Alpaca
No qfa backtest was run because a fallback-only SHY model would not evaluate the prediction-market shock hypothesis.

Safety flags: `no_csv_used=true`, `no_data_csv_argument_used=true`, `no_daemon=true`, `no_orders=true`, `raw_daily_paths_retained=false`.

## Metrics
Unavailable due to external-data block:

- Median random-window Sharpe: unavailable / null
- p25 Sharpe: unavailable / null
- Worst-period Sharpe: unavailable / null
- Annualized return: unavailable / null
- Annualized volatility: unavailable / null
- Max drawdown: unavailable / null
- Turnover: unavailable / null

## Orthogonality
Not evaluated quantitatively because there is no valid return stream. Conceptually, the driver differs from price-only ETF momentum/reversal/carry alphas, but redundancy cannot be measured.

## Decision
**Reject/block AR-091** until an auditable Polymarket archive exists that records, as of each timestamp, market IDs, token IDs, liquidity/volume filters, event taxonomy membership, and probability observations.

## Divergent child
Treasury-options-implied event-risk ETF allocator: use a different data input and return driver (broker/exchange/official option-implied rates/volatility around macro events), not prediction-market probabilities.
