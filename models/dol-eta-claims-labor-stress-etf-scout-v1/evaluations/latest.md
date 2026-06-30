# AR-151 — DOL/ETA unemployment-claims labor-stress ETF scout

Decision: **rejected / source-gated**.

## Bounded source checks

- `https://oui.doleta.gov/unemploy/claims.asp` returned HTTP 200 quickly and exposed the current DOL/ETA weekly claims page.
- `https://oui.doleta.gov/unemploy/claims_arch.asp` returned HTTP 200 quickly and pointed to the current DOL weekly claims release and ETA newsroom release archive.
- `https://www.dol.gov/ui/data.pdf` returned HTTP 403 to the bounded programmatic request.
- Short-timeout requests to ALFRED/FRED CSV graph endpoints for `ICSA` timed out during this recovery window.

## Source gate result

The gate failed.  The scout did not prove a compact official DOL/ETA or ALFRED/FRED path that maps each historical weekly initial/continuing claims observation to the public release date and point-in-time vintage/revision state.  Current DOL/ETA pages and revised FRED-style histories are not enough for timestamp-safe release accelerations.

Because the issue falsifier says to stop when source/vintage safety cannot be proven, no ETF performance, random-window, cost, or orthogonality backtest was run or accepted.  Metrics are intentionally null.

## Production behavior

`model.py` returns flat weights for `SPY`, `QQQ`, `IWM`, `XLK`, `XLF`, `XLU`, `XLP`, `TLT`, `IEF`, `SHY`, `HYG`, `LQD`, and `GLD`.

No CSV-backed market data, daemon, or order path was used. No raw bars/equity/weights/DB/cache/bytecode/helper scripts were retained.

## Next step

Do not spawn direct refinement children from this rejected result.  Revisit only if an official DOL/ETA release archive or ALFRED/FRED vintage method is proven with bounded, point-in-time retrieval and documented revision handling.
