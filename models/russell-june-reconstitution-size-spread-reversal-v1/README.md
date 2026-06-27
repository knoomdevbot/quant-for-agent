# russell-june-reconstitution-size-spread-reversal-v1

## Hypothesis
Annual Russell index reconstitution around the late-June effective date may create temporary benchmark-flow pressure in small-cap/large-cap and size-style ETF spreads that reverses after the event.

## Signal Definition
Cash except after the public last-Friday-in-June proxy. On the next trading day, hold for five trading days. For each predeclared sleeve, measure the prior five-trading-day small-minus-large spread move and take the opposite direction: long the laggard leg and short the winner leg. Gross exposure is normalized to 1.0 across active sleeves.

## Universe
Candidate pool: IWM, IWB, VTWO, VTI, IJR, MDY, RSP, IWF, IWD, IWO, IWN, VTV, VB, VBR, VBK.
Selected before performance review using real-data coverage, recent dollar-volume proxy, and economic exposure: IJR, IWB, IWD, IWF, IWM, IWN, IWO, MDY, VBK, VBR, VTI, VTWO.
RSP, VB, and VTV were candidates/diagnostics but excluded from the primary sleeves because they did not add a cleaner predeclared paired spread than the selected set.

## Evaluation Summary
Data source was qfa/Alpaca real daily OHLCV using configured paper-data access with credential values redacted. No CSV, no data-csv argument, no daemon, and no orders.

Primary 10 bps result over 9 usable June events (2017-2025): mean event return 0.00052177, median -0.00108209, p25 -0.00218099, worst -0.00601856, positive-event rate 0.44444444, event-hold daily Sharpe 4.06271992, max drawdown during holds -0.00801675.

Decision: **rejected**. Main rationale: fewer than 12 usable annual June events; primary 10 bps median event return is not positive; positive-year rate does not clear >50% gate; does not beat ETF TSMOM-style June baseline.

## Orthogonality / Redundancy
Library correlation was deferred because the primary rule failed fast-falsification gates and compact comparable event streams were unavailable in this subtask. Baseline comparisons include no-signal, simple June size spread, pressure momentum, ETF TSMOM, non-June placebos, and quarter-end proxies.

## Known Risks
- Annual event sample is small even with ETF history.
- ETF daily OHLCV may be too coarse for Russell closing-auction flow pressure.
- Calendar overlap with month-end, quarter-end, and OPEX remains a major confound.
- Fixed bps costs do not model borrow availability or intraday execution.

## Change Log
- Initial AR-126 fast-falsification event study and model artifact.
