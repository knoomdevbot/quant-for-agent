# AR-145 — CBOE volatility term-structure stress/normalization ETF allocator

Status: **rejected**.

## Real-data result

Public CBOE daily histories for VIX, VIX3M, VIX9D, and VVIX were fetched transiently and transformed into compact one-session-lagged features. No raw CBOE files were retained.

The end-to-end qfa performance evaluation was run on real ETF daily bars from the configured provider for SPY, QQQ, IWM, HYG, LQD, TLT, IEF, GLD, and SHY. The 10 bps primary result was weak: Sharpe 0.011, annualized return -0.33%, annualized volatility 9.30%, max drawdown -27.80%, and annual turnover 48.96. Random-window validation produced median Sharpe 0.214, p25 Sharpe -0.165, worst Sharpe -2.162, and 64.6% positive windows. The signal failed controls versus simple VIX level, term-slope-only, shifted external features, and ETF TSMOM, so it was rejected and no children were spawned.

## Timestamp discipline

The intended evaluator must join CBOE observations only after at least one full completed trading-session lag. The model wrapper expects pre-lagged features supplied in `context.metadata["cboe_vol_features"]`; it does not download, embed, or read raw CBOE histories.

## Evaluation constraints

- No `--data-csv` and no CSV-backed ETF prices.
- No qfa daemon and no orders.
- Fixed universe: SPY, QQQ, IWM, HYG, LQD, TLT, IEF, GLD, SHY.
- One-session-lagged public CBOE VIX, VIX3M, VIX9D, VVIX features.
- Primary 10 bps one-way turnover cost with 5/20 bps sensitivity.
- Controls versus simple VIX level, term-slope-only, no-VVIX, ETF TSMOM/reversal, shifted labels, and prior defensive/carry/stress families.

No children were spawned from this rejected decision.
