# AR-128 Sector ETF shock lead-lag catch-up

Research-only qfa alpha for testing whether same-day residual shocks in liquid sector ETFs lead delayed next-session catch-up in mapped liquid large-cap constituents.

## Mechanism

- Compute each sector ETF's one-day residual return versus SPY.
- Gate on unusually large absolute sector residual shock.
- For mapped common-stock constituents, compare the stock's same-day market residual to the mapped sector shock.
- Rank underreaction/catch-up score, with a small recent-return control to reduce pure 1-day reversal/momentum leakage.
- Hold a gross-normalized long/short basket for the next daily bar with sector gross caps.

## Data and universe policy

Evaluation used qfa/Alpaca real daily OHLCV only, requested directly from Alpaca in memory. No CSV input, local data-file argument, daemon, orders, raw-bar files, SQLite databases, or helper scripts are retained.

The candidate pool was fixed ex ante from liquid U.S. large-cap common stocks across sectors, with SPY/QQQ/IWM controls and sector ETF signal proxies XLK/XLY/XLC/XLF/XLV/XLE/XLP/XLI/XLU/XLB/XLRE. Final selection was made before performance review by Alpaca coverage, price, dollar-volume, and static sector mapping filters. The static current-large-cap mapping is survivorship-biased and suitable only for fast falsification.

## Decision

Rejected after costed random-window real-data replay. The primary 10 bps one-way cost run did not satisfy required robustness gates and did not beat all required baselines.

See `evaluations/latest.json`, `evaluations/latest.md`, and immutable run JSON under `evaluations/runs/` for compact metrics and diagnostics.
