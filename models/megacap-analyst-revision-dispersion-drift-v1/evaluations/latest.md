# AR-096 Evaluation — mega-cap analyst-revision dispersion drift allocator

- Status: **blocked_required_point_in_time_analyst_revision_data_unavailable**
- Suggested decision: **rejected**
- Universe intended: AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY
- Data controls: Alpaca/qfa real market-data integration checked; no CSV; no `--data-csv`; no daemon; no orders; no retained DB; no raw daily paths.

## Result

The hypothesis could not be faithfully evaluated. It requires point-in-time analyst revision breadth and estimate-dispersion data. No durable non-secret local source for those fields was found, and qfa/AlpacaGateway in this repository exposes OHLCV bars only.

I did **not** fabricate analyst revisions and did **not** treat an OHLCV drift proxy as evidence for this analyst-revision mechanism. The qfa-compatible `model.py` therefore returns flat weights and documents the block.

## Metrics

Unavailable: no primary Sharpe, random-window Sharpe, turnover, hit rate, or orthogonality correlation was computed because the data-source falsifier triggered before evaluation.

## Costs / slippage

Planned external cost assumption was 5 bps one-way turnover, but it was not applied because no strategy returns or turnover were generated.

## Orthogonality

Not computed. There is no evaluated AR-096 return stream to compare with retained event-drift or liquidity-reversal alphas.

## Decision rationale

Reject/block under the issue falsifier: required point-in-time revision data cannot be sourced safely from durable local inputs. No refinement or direct extension is proposed.
