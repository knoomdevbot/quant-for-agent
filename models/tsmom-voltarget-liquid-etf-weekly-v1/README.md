# tsmom-voltarget-liquid-etf-weekly-v1

Research artifact for `AR-003: Volatility-targeted time-series momentum on liquid ETFs`.

## Hypothesis

Assets with positive medium-term trend may continue trending; scaling by realized volatility should reduce concentration in volatile assets and may improve cross-regime stability.

## Model

- Universe: SPY, QQQ, IWM, TLT, GLD, SLV, USO, FXE, FXY.
- Horizon: intended weekly concept, but the current qfa backtester calls the model daily.
- Signal: trailing total return over `lookback_days=126`; long positive momentum assets only.
- Vol targeting: scale positive momentum by `target_vol / realized_vol` using `vol_window=20` daily returns.
- Warmup: `min_periods=127`, so the model waits for enough history before emitting the medium-term signal.
- Sizing: gross-normalized weights, with `max_abs_weight=0.35` pre-engine concentration cap.
- Contract: `model.py` exposes `generate_signals(context)`.

## Latest real-data evaluation

The latest evaluation uses qfa with Alpaca real market data and no CSV fixture.

```bash
set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a
export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"
export ALPACA_PAPER=true
/Users/moonk/quant-for-agent/.venv/bin/qfa backtest run \
  models/tsmom-voltarget-liquid-etf-weekly-v1/model.py \
  --symbols SPY,QQQ,IWM,TLT,GLD,SLV,USO,FXE,FXY \
  --start 2024-01-01 \
  --end 2025-12-31 \
  --db models/tsmom-voltarget-liquid-etf-weekly-v1/evaluations/qfa-real.sqlite3
```

Artifacts:

- Latest JSON: `evaluations/latest.json`
- Latest Markdown: `evaluations/latest.md`
- Run JSON: `evaluations/runs/qfa_real_alpaca_20260626T055000Z.json`
- qfa DB: `evaluations/qfa-real.sqlite3`, run id `1`

Metrics for 2024-01-01 through 2025-12-31 over 500 qfa periods:

- Total return: `33.163486%`
- Annualized return: `15.528762%`
- Annualized volatility: `12.518939%`
- Sharpe: `1.21599641`
- Max drawdown: `-9.362303%`
- Win rate: `42.6%`
- Final equity from 100k: `133163.4859`

## Limitations

- Costs/slippage were not applied because this qfa version has no transaction-cost, slippage, or turnover option in `backtest run` / `run_backtest`.
- qfa currently evaluates/rebalances daily; true weekly cadence requires backtester support or model state handling not present in the API.
- Random-period validation and orthogonality checks remain outstanding.
- Alpaca bar adjustment behavior is whatever qfa's `AlpacaGateway` defaults to; no explicit adjusted-price flag is available in this repo version.

## Stale CSV smoke artifacts

Earlier fixture-derived smoke results are stale and superseded by the real-data evaluation:

- `evaluations/runs/qfa_smoke_20260626T012301Z.json`
- prior `evaluations/latest.json` / `evaluations/latest.md` CSV fixture summaries overwritten by the latest real-data evaluation

## Decision suggestion

Watchlist / continue research. The one real-data backtest is promising pre-cost, but the alpha should not be accepted until it passes costed random-window validation and orthogonality review.

## Child ideas

- Refinement: `AR-003-R1` — implement scripted random-window validation plus 5 bps turnover-based cost haircut and compare 63/126/252 lookbacks with 20/60 vol windows.
- Divergent: `AR-003-D1` — test cross-sectional ETF relative-strength/defensive-rotation using macro/liquidity proxies instead of pure time-series momentum.
