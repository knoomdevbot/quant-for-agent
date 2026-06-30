# AR-151 — DOL/ETA unemployment-claims labor-stress ETF scout

Decision: **rejected / source-gated**.

This compact artifact records the bounded recovery evaluation for a weekly labor-stress ETF rotation idea based on initial/continuing unemployment-insurance claims release accelerations.

## Result

The source/vintage gate failed. Official DOL/ETA pages were reachable, but the recovery did not prove a compact machine-readable historical release/vintage path adequate to prevent revised-data lookahead. Short-timeout ALFRED/FRED checks did not return usable vintage data inside the bounded budget.

The falsifier required stopping at the source gate, so no performance or controls were run. Metrics are null in `evaluations/latest.json`.

## Safe model surface

`model.py` exposes `generate_signals(context)` and returns zero weights for the candidate ETF universe:

`SPY`, `QQQ`, `IWM`, `XLK`, `XLF`, `XLU`, `XLP`, `TLT`, `IEF`, `SHY`, `HYG`, `LQD`, `GLD`.

## Provenance

- `no_csv_used: true`
- `no_data_csv_argument_used: true`
- `no_daemon: true`
- `no_orders: true`
- `raw_daily_paths_retained: false`

No raw market data, claims data files, caches, databases, bytecode, helper scripts, equity curves, or weights were retained.
