# AR-030 evaluation — earnings-quality-drift-megacap-v1

## Result
- Suggested decision: **reject**
- Rationale: Rejected: primary Sharpe is negative, full-period return/drawdown are poor, and random-window median Sharpe is not positive after considering cost sensitivity.

## Data / execution
- Data source: Alpaca real market data via qfa AlpacaGateway; no CSV and no `--data-csv`.
- qfa primary run id: 1
- Temporary DB: `/tmp/ar030_qfa_*.sqlite3`; retained: false.
- Command: `set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a; export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"; export ALPACA_PAPER=true; /Users/moonk/quant-for-agent/.venv/bin/qfa backtest run /Users/moonk/quant-for-agent/models/earnings-quality-drift-megacap-v1/model.py --symbols AAPL,MSFT,NVDA,AMZN,META,GOOGL,TSLA,JNJ,PG,KO,PEP,WMT --start 2022-01-03 --end 2025-12-15 --timeframe 1Day --initial-cash 100000 --db <temporary-sqlite-db>`
- No daemon, no live trading, no trades placed.

## Primary metrics (qfa, pre-cost)
- Sharpe: -0.35078842
- Total return: -0.47158558
- Annualized return: -0.14987173
- Annualized volatility: 0.31041827
- Max drawdown: -0.52572723
- Win rate: 0.4030303
- Periods: 990
- Final equity: 52841.4417

## Random windows (8 qfa/Alpaca windows)
- Median Sharpe: -0.00430704
- Min/Max Sharpe: -1.3926271 / 0.93276157
- Positive Sharpe fraction: 0.5
- Median return: -0.02599695
- Median max drawdown: -0.18019164

## Costs / slippage
- qfa applied costs: false (current qfa CLI has no cost/slippage flag).
- Assumption documented: 5 bps one-way.
- Mean daily one-way turnover estimate: 0.17866266
- Estimated daily cost drag at 5 bps: 8.93313e-05

## Earnings-date limitation
qfa/Alpaca market-data access here does not provide a reliable earnings calendar. No dates were fabricated; the model uses only a documented OHLCV event proxy.

## Orthogonality
- Status: computed
- Correlations: [
  {
    "model_name": "low-vol-quality-proxy-megacap-v1",
    "path": "/Users/moonk/quant-for-agent/models/low-vol-quality-proxy-megacap-v1/evaluations/runs/qfa_real_alpaca_20260626T063544Z.json",
    "overlap_periods": 488,
    "correlation": 0.05626082
  },
  {
    "model_name": "post-earnings-drift-megacap-v1",
    "path": "/Users/moonk/quant-for-agent/models/post-earnings-drift-megacap-v1/evaluations/runs/ar024_qfa_alpaca_real_20260626T075845Z.json",
    "overlap_periods": 989,
    "correlation": 0.50424157
  },
  {
    "model_name": "closing-volume-reversal-megacap-v1",
    "path": "/Users/moonk/quant-for-agent/models/closing-volume-reversal-megacap-v1/evaluations/runs/qfa_realdata_20240101_20251231_primary.json",
    "overlap_periods": 488,
    "correlation": -0.1890852
  }
]

## Bad-result policy
Rejected result; no refinement, direct inversion, or extension of this failed hypothesis is proposed. At most one genuinely divergent child idea is recorded in `latest.json`.
