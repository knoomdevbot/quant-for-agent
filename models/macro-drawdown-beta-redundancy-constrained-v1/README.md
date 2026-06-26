# AR-072 — macro drawdown beta/redundancy constrained allocator

This qfa model refines AR-063 by using the same ETF drawdown/shock proxy family while adding:

- an estimated SPY beta cap (`0.30` selected; `0.50` considered),
- slow 10-day rebalance gates / threshold changes as a turnover brake,
- a redundancy penalty that avoids the common AR-037/AR-043 TLT+GLD+defensive-equity stack, and
- external one-way turnover-cost evaluation at 5 bps plus a 20 bps stress view.

The implementation is long-only, gross exposure <= 1.0 after normalization, and exposes `generate_signals(context)` for qfa.

## Data / execution controls

Evaluation used Alpaca real daily bars through qfa/AlpacaGateway only. No CSV fixtures and no `--data-csv` were used. No daemon and no trade/order commands were used. qfa SQLite DBs were temporary under `/tmp` and removed after execution.

## Artifacts

- `model.py`
- `config.yaml`
- `metadata.yaml`
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/<immutable>.json`
