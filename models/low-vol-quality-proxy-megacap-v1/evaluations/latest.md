# AR-010 evaluation: low-vol-quality-proxy-megacap-v1

## Decision
**Watchlist.** Full-period Sharpe is positive but modest; median random-window Sharpe is positive and lower-tail windows are not catastrophic. Keep on watchlist pending cost-aware and parameter-stability validation.

## Data and command
- Data source: Alpaca real market data via qfa backtest for primary run; AlpacaGateway for random-window protocol. No `--data-csv`; no CSV fixtures.
- Primary qfa run ID: `1`
- DB path used during execution: `models/low-vol-quality-proxy-megacap-v1/evaluations/qfa_realdata.sqlite3` (not retained as required artifact)
- Run JSON: `models/low-vol-quality-proxy-megacap-v1/evaluations/runs/qfa_real_alpaca_20260626T063544Z.json`

```bash
set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a; export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"; export ALPACA_PAPER=true; /Users/moonk/quant-for-agent/.venv/bin/python -m py_compile models/low-vol-quality-proxy-megacap-v1/model.py && /Users/moonk/quant-for-agent/.venv/bin/qfa backtest run models/low-vol-quality-proxy-megacap-v1/model.py --symbols AAPL,MSFT,NVDA,AMZN,META,GOOGL,TSLA,JNJ,PG,KO,PEP,WMT --start 2024-01-01 --end 2025-12-31 --timeframe 1Day --initial-cash 100000 --db models/low-vol-quality-proxy-megacap-v1/evaluations/qfa_realdata.sqlite3
```

## Full-period qfa metrics, pre-cost
- Period: 2024-01-01 to 2025-12-31, 500 daily periods
- Final equity: 106887.9073
- Total return: 0.06887907
- Annualized return: 0.03414158
- Annualized volatility: 0.11257841
- Sharpe: 0.35445852
- Max drawdown: -0.16939658
- Win rate: 0.362

## Random-window protocol
- 30 random windows, seed 10010, 252 trading-day windows, Alpaca real data from 2021-01-04 to 2025-12-30.
- Sharpe summary: median 0.08598409, p25 -0.69008777, p75 0.52516002, min -1.86587634, max 2.42535025.
- Positive-Sharpe fraction: 0.5.
- Annualized-return median: 0.00350583.
- Max-drawdown median: -0.11839984.

## Costs/slippage caveat
Costs/slippage were **not applied** by qfa because the current qfa backtest CLI exposes no cost or slippage parameter. The documented assumption is 5 bps; rough annual drag estimate from turnover proxy is 0.01577504, but this is not an applied qfa result.

## Orthogonality
unavailable_no_comparable_equity_curves. Attempted retained watchlist comparisons: AR-003, AR-005, AR-006, AR-008; no overlapping timestamped equity-curve return streams were available in retained latest artifacts.

## Child ideas
- Refinement: AR-029: Parameter-stability/cost-aware low-vol quality proxy sweep vol_window=[60,126,189], top_n=[4,6,8], momentum_filter=[true,false], with explicit turnover-cost haircut and monthly rebalance approximation.
- Divergent: AR-030: Mega-cap defensive earnings-quality drift using post-earnings gap persistence plus balance-sheet/profitability proxies rather than realized-volatility ranks.

## Warnings
- No trades placed; qfa daemon not run.
- qfa metrics are pre-cost.
