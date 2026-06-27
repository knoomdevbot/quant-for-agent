# AR-052 Evaluation — vixy-tlt-stress-carry-etf-v1

## Decision
**Suggested decision:** rejected

Rationale: p25 random-window post-cost Sharpe -0.8037 <= -0.25.

## Data and execution
- Source: Alpaca real OHLCV through qfa/AlpacaGateway; `--data-csv` was not used.
- Command shape: `/Users/moonk/quant-for-agent/.venv/bin/qfa backtest run /Users/moonk/quant-for-agent/models/vixy-tlt-stress-carry-etf-v1/model.py --symbols VIXY,TLT,IEF,SHY,SPY --start 2021-01-04 --end 2026-06-15 --timeframe 1Day --initial-cash 100000 --db <temporary-sqlite-db>`
- Symbols: VIXY, TLT, IEF, SHY, SPY
- Primary range: 2021-01-04 to 2026-06-15, 1Day bars.
- Temporary DB: `/tmp/qfa-AR-052-*.sqlite3`; retained: false.
- No daemon, no live trades.

## Primary metrics
| Metric | QFA pre-cost | Post-cost proxy |
|---|---:|---:|
| Total return | -0.101627 | -0.120144 |
| Ann. return | -0.019577 | -0.023336 |
| Ann. vol | 0.059926 | 0.059927 |
| Sharpe | -0.299941 | -0.364039 |
| Max drawdown | -0.222285 | -0.230299 |
| Win rate | 0.460469 | 0.459736 |

## Random-window protocol
- Random windows: 10
- Median post-cost Sharpe: 0.178870
- 25th percentile post-cost Sharpe: -0.803671
- Positive-window rate: 0.600000
- Worst post-cost Sharpe: -2.588103
- Worst max drawdown: -0.138981

## Costs / turnover
- Native qfa costs: false.
- External haircut: 5.0 bps one-way times estimated target-weight turnover.
- Mean daily one-way turnover: 0.030490
- Annualized turnover proxy: 7.683465
- Estimated annual drag: 0.003842

## Orthogonality
- Status: moderate_redundancy
- Max abs correlation: 0.65370053
- Method: Pearson daily equity-return correlation vs retained latest.json curves where available

## Suggested child ideas
- If this result is rejected, no refinement/direct inversion/extension is suggested.
- At most one divergent child: **ETF volatility-term-state breadth allocator** — use cross-ETF realized-volatility term-structure/breadth states without VIXY/TLT stress-carry sleeves.
