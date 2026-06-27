# etf-distribution-exdate-reversal-allocator-v1

AR-120 tested whether timestamp-safe ETF cash-distribution/ex-dividend events create short-horizon drift or reversal effects in income, bond, REIT, and defensive ETFs.

## Recommendation

**Blocked / rejected for now.** Do not add to the alpha watchlist until a corporate-action source with announcement/as-of/knowledge timestamps is available.

## Result

Real Alpaca daily bars and Alpaca cash-dividend corporate-action records were reachable for the broad candidate pool. The corporate-action records exposed ex-date, payable date, record date, process date, and cash rate, but did not expose a timestamp proving when the event was known historically. Because AR-120 explicitly disallows non timestamp-safe event use and forbids OHLCV-inferred ex-dates, no performance backtest was run.

The model implementation is intentionally inert and returns zero weights/cash.

## Data and safety

- Real market data only.
- No CSV and no `--data-csv`.
- No qfa daemon.
- No orders/trades.
- No raw bars, raw event files, DBs, caches, or helper scripts retained.
- Credentials were sourced only from configured local Alpaca paper-data access and are not stored in artifacts.

See `evaluations/latest.json` and `evaluations/latest.md` for compact, verifiable coverage details.
