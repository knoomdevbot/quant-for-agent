# AR-130 — SEC 13F deadline mega-cap attention residual reversal

## Decision
**Rejected** as a production/watchlist alpha. The event-gated result is mildly positive in full sample but fails robustness and redundancy gates.

## Model
`model.py` exposes `generate_signals(context)`. It uses only completed qfa/Alpaca daily OHLCV bars and deterministic SEC Form 13F filing deadline dates: 45 calendar days after quarter-end, shifted to the next observed trading day. For three sessions after a deadline it reverses 5-day sector/SPY residual pressure in mega/large-cap names with positive abnormal dollar-volume z-score.

## Evaluation
- Data: qfa `AlpacaGateway` / Alpaca real daily OHLCV, fetched in-memory; no CSV, no `--data-csv`, no daemon, no orders.
- Period: 2019-01-01 through 2026-06-26; 25 deadline events from 2020-05-15 through 2026-05-15.
- Universe: 130 liquid mapped mega/large-cap common-stock candidates selected by pre-performance Alpaca coverage/liquidity screens; static current universe is survivorship-biased.

## Primary metrics at 10 bps one-way
- Sharpe: 0.354903
- Annualized return / volatility: 0.008472 / 0.024614
- Max drawdown: -0.050913
- Avg daily turnover: 0.024014
- Activation rate: 0.036021
- Event count / hit rate: 25 / 0.52
- Random windows: median Sharpe 0.100233, p25 -0.751899, worst -2.185575, positive-window rate 0.566667

## Falsifiers / ablations
- 5/10/20 bps Sharpe: 0.476873 / 0.354903 / 0.108692
- Matched +21 trading-day placebo Sharpe: -0.71569
- Shifted deadline +10 trading-days Sharpe: -0.44974
- Generic daily residual reversal Sharpe: -1.581976
- Generic abnormal-volume/close-location reversal Sharpe: -2.711475
- Raw pressure/no sector residual Sharpe: 0.300219; correlation to primary 0.973612

## Warnings
- Static current universe is survivorship-biased and used only for fast falsification.
- No timestamp-safe earnings calendar was available; earnings contamination was not fully removed.
- Exact existing alpha stream correlations were unavailable; generic reversal proxies were used.
- Sparse quarterly events make inference fragile.

See `evaluations/latest.json`, `evaluations/latest.md`, and immutable run JSON under `evaluations/runs/`.
