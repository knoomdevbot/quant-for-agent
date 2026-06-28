# AR-134 latest evaluation

**Status:** blocked/rejected  
**Suggested decision:** rejected

SEC Form 4 PIT event table construction timed out / was not completed in the bounded recovery run. Because the timestamp-safe event source was unavailable, no selected universe, qfa/Alpaca market-data evaluation, random-window test, placebo test, cost sensitivity, or orthogonality analysis could be completed.

## Guardrails

- `no_csv_used`: true
- `no_data_csv_argument_used`: true
- `no_daemon`: true
- `no_orders`: true
- `raw_daily_paths_retained`: false

## Feasibility note

A small public SEC `company_tickers.json` reachability probe succeeded, but this is not sufficient for Form 4 event construction or performance evaluation. No raw filings or bars were retained.

## Metrics

All performance metrics are null/unavailable. No Sharpe is fabricated.
