# AR-096 — mega-cap analyst-revision dispersion drift allocator

## Decision

**Suggested decision: rejected / blocked by data availability.**

The alpha hypothesis requires point-in-time analyst revision breadth and estimate-dispersion history. I found no durable, non-secret local source for those fields, and the repository qfa/Alpaca integration exposes real OHLCV bars only. An OHLCV-only proxy would not be faithful to the mechanism, so the qfa model is intentionally flat and no performance backtest was treated as evidence for the hypothesis.

## Controls

- Data source checked: Alpaca real market-data integration through qfa/AlpacaGateway.
- No CSV used; no `--data-csv` argument used.
- No daemon and no orders.
- Credentials were sourced from the configured private profile and key-id mapping was performed without printing secret values.
- No SQLite database artifact was retained.
- Raw daily paths/equity curves were not retained.

## Universe intended by issue

AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY.

## Findings

- Local repository search found no analyst revision/estimate/dispersion files or databases.
- qfa `AlpacaGateway` public methods are `get_bars`, `account_equity`, and `submit_notional_order`; the only market-data getter returns `timestamp`, `symbol`, `open`, `high`, `low`, `close`, and `volume`.
- Because PIT analyst data is unavailable, random-window Sharpe, p25 Sharpe, turnover, hit rate, and orthogonality correlations are unavailable rather than estimated from a fabricated proxy.

## Artifacts

- `model.py`: qfa-compatible flat model documenting the block.
- `config.yaml`: intended universe/parameter defaults and block rationale.
- `metadata.yaml`: compact status metadata.
- `evaluations/latest.json`, `evaluations/latest.md`, and immutable run JSON under `evaluations/runs/`.
