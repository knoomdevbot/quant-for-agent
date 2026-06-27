# low-vol-quality-coststable-megacap-v1

AR-029 cost-aware refinement of AR-010's mega-cap low-volatility quality proxy.

## Hypothesis

A low-volatility/quality proxy may be more robust if turnover and rebalance cadence are made explicit. This implementation keeps the AR-010 126-day inverse-realized-volatility rank with a positive 126-day momentum quality filter, but computes ranks on a monthly anchor to reduce daily churn.

## Data and execution constraints

- Data source: Alpaca real market data through qfa/AlpacaGateway only.
- No CSV and no `--data-csv`.
- No qfa daemon, no live trading, no orders.
- Primary qfa run used a temporary SQLite DB that was removed; `db_artifact_retained=false`.

## Model spec

- Universe: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, JNJ, PG, KO, PEP, WMT
- Signal: inverse 126-trading-day realized volatility
- Quality proxy: require positive 126-trading-day return
- Rebalance proxy: monthly anchor
- Selection: top 6 names
- Sizing: inverse-vol weighted, long-only, gross exposure <= 1.0, max single-name target 20%

## Latest evaluation

- Primary period: 2021-01-04 to 2025-12-15, 1Day bars
- qfa/pre-cost Sharpe: 0.16835842
- qfa/pre-cost total return: 0.06914755
- qfa/pre-cost max drawdown: -0.31564793
- 5 bps cost-adjusted Sharpe: 0.1175992
- 10 random 252-trading-day windows, seed 29029
- Median random 5 bps cost-adjusted Sharpe: -0.79262501
- Positive random 5 bps cost-adjusted Sharpe fraction: 0.4

## Decision

Suggested decision: **rejected**.

Reason: the primary result remained only modestly positive and the median random-window Sharpe after a 5 bps one-way turnover haircut was negative, failing the AR-029 falsifier. Per bad-result policy, no direct refinement, inversion, or extension child was created.

## Artifacts

- `model.py`
- `config.yaml`
- `metadata.yaml`
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/ar029_qfa_alpaca_real_20260626T082319Z.json`
