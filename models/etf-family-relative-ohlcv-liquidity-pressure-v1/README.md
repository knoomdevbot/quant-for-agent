# ETF family-relative OHLCV liquidity-pressure v1 (AR-121)

Rule-based qfa model implementing a fast-falsification test of whether daily ETF OHLCV dislocations proxy temporary liquidity pressure that mean-reverts over the next 1-5 trading days.

## Signal

The model uses only bars present in `context.prices`:

- abnormal dollar-volume shock,
- close-location pressure,
- gap/close residual,
- signed realized range expansion,
- return-volume dislocation,
- median-relative normalization within fixed exposure families.

It ranks family-relative pressure across a broad fixed ETF universe. Low-pressure names are held long and high-pressure names short in a market-neutral-lite portfolio, capped at 12.5% absolute symbol weight and gross exposure <= 1.

## Universe and data

The candidate pool spans broad equity, sectors, style/factor, international, rates/credit, and commodity/real-asset ETFs. The selected universe was fixed before performance review using Alpaca daily bar coverage/history and trailing dollar-volume sanity filters only.

Evaluation used qfa/Alpaca real daily OHLCV only. No CSV, no `--data-csv`, no daemon, and no orders.

## Result

Fast falsification rejects the idea. At 10 bps one-way turnover cost, random-window median Sharpe was -5.723 with 0% positive-window rate; primary all-history Sharpe was -5.115. Turnover was too high and cost fragility severe. See `evaluations/latest.json` and `evaluations/latest.md`.
