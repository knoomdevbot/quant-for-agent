# AR-114 — Municipal Bond ETF Tax-Calendar Flow Reversal

Research-only qfa alpha model for a predeclared municipal ETF tax-calendar flow reversal idea.

## Hypothesis

Municipal bond ETFs may experience temporary tax-sensitive flow pressure around late-November/December tax-loss selling and April tax-payment liquidity needs, followed by reversal/reinvestment demand in January and after pressure stabilizes. The model is intentionally calendar-gated and long-only; it does not mine calendar dates from performance.

## Universe

Broad ex-ante candidate pool: MUB, TFI, SHM, HYD, ITM, SUB, PZA, VTEB, MLN, HYMB, SMB. Controls/proxies: SHY, IEF, TLT, LQD, HYG, SPY.

Selected primary municipal ETF sleeve before performance review: MUB, TFI, SHM, HYD, ITM, SUB, PZA, VTEB, subject to real-data coverage/liquidity checks in the evaluation artifact. The selection emphasizes history, daily bar availability, liquidity, and economic exposure to municipal debt rather than realized alpha.

## Signal

- Active windows: Nov 20–Dec 31, Jan 1–Jan 18, Apr 10–Apr 30.
- Within an active window, buy qualifying muni ETFs only after recent 21-trading-day pressure, acceptable volume, and latest-day stabilization.
- Penalize already-positive intermediate momentum to avoid generic trend following.
- Normalize long-only gross exposure up to 1.0 with per-ETF caps; use SHY as an inactive fallback if available.

## Evaluation

Evaluation artifacts are in `evaluations/`. They use qfa/Alpaca real daily OHLCV only; no CSV input, no `--data-csv`, no daemon, and no orders. The saved artifacts are compact and do not retain raw bars, SQLite DBs, equity curves, or weight histories.
