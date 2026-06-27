# AR-102 credit-spread compression breadth risk allocator

Rule-based qfa alpha implementing `generate_signals(context)` for a credit-breadth regime allocator. It uses only qfa/Alpaca daily OHLCV bars and tradeable ETF spread proxies: HYG/LQD, HYG/IEF, and breadth across HYG/JNK/VCIT/LQD versus IEF.

## Selected universe

`HYG, JNK, LQD, VCIT, TIP, TLT, IEF, SHY, SPY, QQQ, IWM, XLF, XLI, XLE, XLU, XLP, XLV, GLD`.

This broad pool covers high-yield credit, investment-grade/intermediate credit, duration, inflation-linked bonds, cash-like bonds, equity beta, cyclicals, defensive sectors, and gold. Ratios are spread proxies and may confound duration shocks.

## Signal summary

- Credit compression: positive HYG/LQD and HYG/IEF ratio z-scores plus credit ETF breadth above threshold.
- Risk-on allocation: high-yield/intermediate credit plus confirmed equities/cyclicals.
- Expansion/stress allocation: duration, gold, defensive sectors, and SHY fallback.
- Neutral allocation: quality credit, IEF/SHY, GLD with small confirmed equity/defensive sleeves.

## Controls

No CSV-backed data, no `--data-csv`, no daemon, no orders, no leverage. Evaluation artifacts retain compact metrics only; raw daily data and equity curves are not retained.

## Evaluation result

Real-data qfa/Alpaca evaluation completed for AR-102. The model is **rejected**: 11 random/stress windows had weak-to-negative cost-adjusted Sharpe distribution (10 bps median Sharpe -0.3145, p25 -0.5594, worst -1.3649) and primary full-period 10 bps Sharpe -0.8613 with high turnover sensitivity. See `evaluations/latest.json`, `evaluations/latest.md`, and immutable run JSON files under `evaluations/runs/`.
