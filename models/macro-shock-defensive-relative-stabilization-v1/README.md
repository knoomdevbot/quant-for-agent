# macro-shock-defensive-relative-stabilization-v1

AR-122 tested an OHLCV-only event study: after broad equity/credit/vol macro-shock days, allocate for five sessions to defensive/recovery ETFs that have stabilized relative to cyclicals.

## Universe fixation

Broad ex-ante pool:
- Sectors: XLK, XLY, XLP, XLV, XLU, XLF, XLI, XLE, XLB, XLRE, XLC
- Broad/style: SPY, QQQ, IWM, DIA, USMV, SPLV, QUAL, MTUM
- Credit/duration: HYG, LQD, SHY, IEF, TLT, TIP
- Hedges/commodities: GLD, DBC

Before reviewing performance, the selected universe was fixed by real daily OHLCV coverage and recent liquidity (>=1200 IEX daily observations and recent median dollar volume > $2mm): SPY, QQQ, IWM, DIA, USMV, SPLV, QUAL, MTUM, XLK, XLY, XLP, XLV, XLU, XLF, XLI, XLE, XLB, XLRE, XLC, HYG, LQD, SHY, IEF, TLT, TIP, GLD. DBC failed the liquidity filter.

## Rule

- Shock gate: SPY bottom-tail daily return, 3-day SPY drawdown, HYG weakness with equity weakness, or realized-vol jump with negative 5-day SPY.
- Stabilization: 3-day defensive-vs-cyclical relative return positive, defensive/cyclical absolute-return compression below 1.20, and HYG-LQD confirmation not deeply negative.
- Allocation: next-session event sleeve holds top 3 recovery/defensive ETFs for 5 sessions with 5% SHY fallback.

## Evaluation summary

Real-data evaluation used Alpaca daily OHLCV with IEX feed requested, 2018-01-01 to 2026-06-26. No CSV, no `--data-csv`, no daemon, and no orders.

Primary 10 bps result: Sharpe -0.595, annualized return -3.20%, annualized vol 5.38%, max drawdown -20.59%, daily turnover 0.0679, activation 16.88%.

Random 126-trading-day windows: median Sharpe -0.683, p25 -1.591, worst -3.296, positive-window rate 18.0%.

Event windows: 51 active events across 33 independent shock clusters; hit rate 39.2%; mean event return -0.227%; median event return -0.472%.

Baselines/ablations included shock-only/no stabilization, continuous defensive carry, ETF TSMOM, and pullback proxy. Defensive carry was positive while this event rule was negative; proxy correlations were below 0.60 but performance failed decisively.

## Decision

**Rejected.** The rule failed the acceptance threshold at 10 bps and under 5/20 bps sensitivities, with negative median and p25 random-window Sharpe and low event hit rate. It should not be promoted without a materially different hypothesis.

See `evaluations/latest.json` and `evaluations/latest.md` for compact metrics and limitations.
