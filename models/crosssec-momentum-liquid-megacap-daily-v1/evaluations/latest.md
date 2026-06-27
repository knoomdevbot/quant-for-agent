# AR-001 real-data evaluation: crosssec-momentum-liquid-megacap-daily-v1

- Status: completed real-data qfa backtest
- Created: 2026-06-26T05:45:54Z
- Data source: Alpaca market data via qfa backtest; `--data-csv` was not used
- Run JSON: `evaluations/runs/qfa_realdata_20240101_20251231_run1.json`
- QFA DB: `evaluations/qfa_realdata.sqlite`

## Command

```bash
set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a; export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"; export ALPACA_PAPER=true; qfa backtest run /Users/moonk/quant-for-agent/models/crosssec-momentum-liquid-megacap-daily-v1/model.py --symbols AAPL,MSFT,NVDA,AMZN,META,GOOGL,TSLA --start 2024-01-01 --end 2025-12-31 --timeframe 1Day --initial-cash 100000 --db /Users/moonk/quant-for-agent/models/crosssec-momentum-liquid-megacap-daily-v1/evaluations/qfa_realdata.sqlite
```

## Setup / model review

`model.py` was reviewed against AR-001 and already implements the requested cross-sectional intermediate momentum seed: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA; 63-trading-day return; 5-day skip; 20-day volatility normalization; demeaned long/short weights; gross exposure 1.0; single-name cap 0.25. No model code change was required.

## Metrics, pre-cost

- Period: 2024-01-01 to 2025-12-31
- Symbols: AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA
- QFA run id: 1
- Equity points / periods: 500 / 500
- Initial cash: 100000.00
- Final equity: 69287.4594
- Total return: -0.30712541
- Annualized return: -0.16882985
- Annualized volatility: 0.17069684
- Sharpe: -0.99519064
- Max drawdown: -0.36715277
- Win rate: 0.41000000

## Costs / caveats

- Intended cost assumption from AR-001: 5 bps.
- Current qfa backtest CLI has no transaction-cost/slippage parameter, so costs were **not applied**.
- Metrics are therefore pre-cost and likely optimistic versus executable performance.
- No trades were placed and the daemon was not run.
- Previous fixture/CSV smoke results are stale and overwritten by this real-data evaluation.

## Suggested decision

Reject for alpha-library acceptance or trading. The real-data backtest is materially negative before costs: Sharpe -0.9952, total return -30.71%, max drawdown -36.72%.

## Child ideas

- Refinement child: AR-001-R1 invert/test anti-momentum variant or add regime/cost/turnover filters and parameter stability sweep over lookback_days=[63,126], skip_days=[5,10], volatility_normalize=[true,false] on Alpaca data.
- Divergent child: AR-001-D1 mega-cap post-earnings announcement drift / analyst-revision event signal over 1-20 day horizon, independent of pure price momentum.
