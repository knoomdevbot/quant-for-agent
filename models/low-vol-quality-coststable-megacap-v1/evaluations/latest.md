# AR-029 evaluation — low-vol-quality-coststable-megacap-v1

- Created UTC: 2026-06-26T08:23:19Z
- Data source: Alpaca real market data via qfa AlpacaGateway; no CSV; `--data-csv` not used.
- Primary qfa command: `set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a; export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"; export ALPACA_PAPER=true; /Users/moonk/quant-for-agent/.venv/bin/qfa backtest run /Users/moonk/quant-for-agent/models/low-vol-quality-coststable-megacap-v1/model.py --symbols AAPL,MSFT,NVDA,AMZN,META,GOOGL,TSLA,JNJ,PG,KO,PEP,WMT --start 2021-01-04 --end 2025-12-15 --timeframe 1Day --initial-cash 100000 --db <temporary-sqlite-db>`
- DB: temporary SQLite (`db_artifact_retained=false`); no daemon and no trades.
- Symbols: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, JNJ, PG, KO, PEP, WMT
- Primary period: 2021-01-04 to 2025-12-15, 1Day bars

## Primary metrics

- qfa/pre-cost Sharpe: 0.16835842
- qfa/pre-cost total return: 0.06914755
- qfa/pre-cost max drawdown: -0.31564793
- qfa/pre-cost win rate: 0.39291465
- qfa/pre-cost periods: 1242
- 5 bps cost-adjusted Sharpe: 0.1175992
- 5 bps cost-adjusted total return: 0.03150276
- Mean daily one-way turnover: 0.05768768
- Estimated annual cost drag at 5 bps: 0.00726865

## Random-window validation

- Windows: 10 random 252-trading-day windows, seed 29029
- Median random 5 bps cost-adjusted Sharpe: -0.79262501
- Positive random 5 bps cost-adjusted Sharpe fraction: 0.4
- Worst random 5 bps cost-adjusted Sharpe: -1.90029373
- Worst random 5 bps cost-adjusted max drawdown: -0.2398958

## Parameter stability

Tiny pre-specified neighbor check only; no broad grid search.

- Cost-adjusted Sharpe median across variants: 0.12880907
- Cost-adjusted Sharpe min/max across variants: 0.05516897 / 0.33707991

## Orthogonality

- Status: computed
- Computed correlations: 3

## Decision

- Suggested decision: **rejected**
- Rationale: Rejected: median random-window Sharpe after 5 bps turnover cost is <= 0 or lower-tail instability fails AR-029 falsifier.

## Durable artifacts

- `models/low-vol-quality-coststable-megacap-v1/model.py`
- `models/low-vol-quality-coststable-megacap-v1/config.yaml`
- `models/low-vol-quality-coststable-megacap-v1/metadata.yaml`
- `models/low-vol-quality-coststable-megacap-v1/README.md`
- `models/low-vol-quality-coststable-megacap-v1/evaluations/latest.json`
- `models/low-vol-quality-coststable-megacap-v1/evaluations/latest.md`
- `/Users/moonk/quant-for-agent/models/low-vol-quality-coststable-megacap-v1/evaluations/runs/ar029_qfa_alpaca_real_20260626T082319Z.json`
