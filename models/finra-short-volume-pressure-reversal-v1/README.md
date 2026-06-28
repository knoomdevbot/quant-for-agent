# FINRA short-sale volume pressure reversal (AR-140)

**Decision:** rejected / blocked by universe-event gates.

This model folder records a compact evaluation attempt for a timestamp-lagged FINRA Reg SHO short-sale-volume reversal signal. FINRA public files were accessed in memory and configured Alpaca/qfa real daily OHLCV was used where market data was needed. No CSV market data, daemon, or orders were used.

## Result

The recorded filters produced no selected liquid common-stock universe and no timestamp-safe primary events:

- FINRA symbols with at least 400 file-date observations: 9,861.
- Selected liquid common stocks: 0.
- Primary event count: 0.
- Minimum universe gate passed: false.
- Minimum event gate passed: false.
- Median/p25/worst random-window Sharpe: unavailable because no active primary events survived.
- Turnover/max drawdown: unavailable.

The issue should be rejected in this form. No direct short-volume refinement child should be spawned unless the universe construction problem is solved with a materially better, timestamp-safe security master rather than a cosmetic threshold change.
