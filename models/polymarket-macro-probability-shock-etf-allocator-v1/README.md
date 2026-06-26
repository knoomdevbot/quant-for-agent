# AR-091 — Polymarket Macro Probability Shock ETF Allocator

Status: **blocked / rejected for this research pass**.

## Hypothesis
Large moves in liquid prediction-market probabilities for macro/political outcomes may identify event-risk repricing that spills into equity, duration, gold, credit, and sector ETFs.

## What was tested
I investigated whether a reproducible point-in-time Polymarket signal could be built without fabricated proxies or retained raw external data. Public read-only endpoints were reachable with a normal browser user-agent:

- `gamma-api.polymarket.com/markets` for current market metadata and token IDs.
- `clob.polymarket.com/markets` for CLOB market snapshots.
- `clob.polymarket.com/prices-history` for token-level probability history.

A broad ETF candidate pool was specified before performance evaluation: SPY, QQQ, IWM, TLT, IEF, SHY, GLD, HYG, LQD, XLE, XLU, XLV, XLF, KRE, ITA, XLI, XLP, XLY, FXI, EEM, USO, UUP.

## Blocking issue
The issue requires reproducible external prediction-market data with timestamp discipline. The public endpoints provided current snapshots and token history, but this pass did not establish a defensible point-in-time macro market discovery and selection archive. Selecting current/known macro markets and then replaying their histories would introduce ex-post market-selection/lookahead risk. Because the hard rule forbids fabricated proxies, no prediction-market substitute was used.

## QFA / Alpaca evaluation
No qfa backtest was run. Running a fallback-only SHY model would exercise Alpaca plumbing but would not evaluate the prediction-market shock hypothesis. No `--data-csv` argument was used, no daemon was run, and no orders were placed.

## Decision
Blocked/rejected pending a separate, auditable Polymarket market-universe archive that records market IDs, token IDs, liquidity/volume snapshots, and probability observations as they became available.

## Divergent child idea
If continuing from this rejection, use a different driver and data family: **Treasury-options-implied event risk allocator** using reproducible exchange/official or broker-sourced option-implied rates/volatility around macro announcements, rather than prediction-market probabilities.
