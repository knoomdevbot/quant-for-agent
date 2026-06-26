# AR-040 Evaluation — yield-credit-stress-etf-allocation-v1

- Created: 2026-06-26T09:10:43Z
- Data: Alpaca real market data through qfa AlpacaGateway; `--data-csv` not used.
- Symbols: SPY, QQQ, IWM, TLT, IEF, GLD, HYG, LQD, XLP, XLU, XLV, XLY, XLI, XLK, XLF
- Primary range: 2021-01-04 to 2025-12-15, 1Day.
- Temporary DBs: `/tmp/qfa_ar040_*.sqlite3`; deleted after capture; no DB/raw data/cache artifacts retained.
- Costs: qfa native costs unavailable; post-cost proxy subtracts 5.0 bps one-way target-weight turnover.

## Key metrics

| Metric | Pre-cost qfa | Post-cost proxy |
|---|---:|---:|
| Sharpe | 0.1416 | 0.1060 |
| Total return | 0.0489 | 0.0274 |
| Ann. return | 0.0097 | 0.0055 |
| Ann. vol | 0.1180 | 0.1180 |
| Max drawdown | -0.2337 | -0.2375 |
| Win rate | 0.4557 | 0.4549 |

Random-window median post-cost Sharpe: **0.4114**; min post-cost Sharpe: **-0.5335**; worst post-cost max drawdown: **-0.2375**.

## Random windows

| Start | End | Pre-cost Sharpe | Post-cost Sharpe | Post-cost max DD |
|---|---|---:|---:|---:|
| 2021-01-04 | 2022-12-30 | -0.5035 | -0.5335 | -0.2375 |
| 2021-07-01 | 2023-06-30 | -0.3166 | -0.3460 | -0.2025 |
| 2022-01-03 | 2023-12-29 | 0.1198 | 0.0860 | -0.1572 |
| 2022-07-01 | 2024-06-28 | 0.5922 | 0.5461 | -0.1101 |
| 2023-01-03 | 2024-12-31 | 0.8433 | 0.8019 | -0.0892 |
| 2023-07-03 | 2025-06-30 | 0.9631 | 0.9271 | -0.0838 |
| 2024-01-02 | 2025-12-15 | 0.4390 | 0.4114 | -0.1116 |

## Orthogonality

Status: **low_to_moderate_redundancy**. Max absolute retained-library daily-return correlation: 0.66860615.

## Decision

**rejected** — Rejected: despite positive median random-window post-cost Sharpe, the 2021-2022 lower-tail drawdown exceeded 20%, violating the defensive macro-stress falsifier.

## Repro command (sanitized)

```bash
credentials sourced from profile secret file (redacted); /Users/moonk/quant-for-agent/.venv/bin/qfa backtest run /Users/moonk/quant-for-agent/models/yield-credit-stress-etf-allocation-v1/model.py --symbols SPY,QQQ,IWM,TLT,IEF,GLD,HYG,LQD,XLP,XLU,XLV,XLY,XLI,XLK,XLF --start 2021-01-04 --end 2025-12-15 --timeframe 1Day --initial-cash 100000 --db <temporary-sqlite-db>
```
