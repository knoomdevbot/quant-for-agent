# earnings-quality-drift-megacap-v1

AR-030 research-only qfa alpha model.

This model tests whether mega-cap equities with a large OHLCV information-shock proxy, same-direction post-event drift, and stable realized volatility produce an earnings-quality/post-event drift return stream distinct from pure low-volatility ranking.

Important limitation: qfa/Alpaca in this repository provides real OHLCV bars but not a reliable earnings calendar. No earnings dates are fabricated. The event trigger is a documented price/volume proxy.

Run with Alpaca real market data only; do not use `--data-csv`:

```bash
set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a
export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"
export ALPACA_PAPER=true
/Users/moonk/quant-for-agent/.venv/bin/qfa backtest run /Users/moonk/quant-for-agent/models/earnings-quality-drift-megacap-v1/model.py   --symbols AAPL,MSFT,NVDA,AMZN,META,GOOGL,TSLA,JNJ,PG,KO,PEP,WMT   --start 2022-01-03 --end 2025-12-15 --timeframe 1Day --initial-cash 100000   --db <temporary-sqlite-db>
```

Evaluation artifacts are in `evaluations/latest.json`, `evaluations/latest.md`, and `evaluations/runs/`.
