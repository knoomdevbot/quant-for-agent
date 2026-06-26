# AR-098 evaluation: sector-etf-earnings-season-dispersion-reversal-v1

Suggested decision: **rejected**.

## Protocol
- Data: Alpaca real daily OHLCV via qfa/AlpacaGateway, symbols `XLK, XLY, XLP, XLV, XLF, XLI, XLE, XLU, XLB, XLRE, SPY`.
- No CSV input, no `--data-csv` argument, no daemon, no orders.
- Costs: external one-way turnover haircut at 5/10/20 bps; qfa has no native cost model.
- Random/stress windows: 10 windows from 2020-2025.

## Key metrics
- Primary 2021-01-04 to 2025-12-15 pre-cost Sharpe: 0.3253.
- Primary 5 bps cost Sharpe: 0.0749; max drawdown: -0.0540.
- Random-window 5 bps median Sharpe: -0.1936; p25 Sharpe: -0.4653; positive-window rate: 30.00%.
- Worst random-window 5 bps Sharpe: -1.2116; worst max drawdown: -0.0378.
- Primary mean daily one-way turnover proxy: 0.0462; annualized turnover proxy: 11.64.

## Orthogonality
Status: `unavailable`; max absolute correlation: `None`. Most accepted/watchlist artifacts do not retain compact return streams, so correlation may be unavailable.

## Decision notes
Rejected if median/p25 random-window Sharpe after 5 bps costs fail acceptance threshold or if orthogonality exceeds cap; no refinement/direct extension should be created for rejected parent-linked result.

## Warnings
- Earnings-season is approximated from calendar months because no fundamental earnings calendar is available in qfa/Alpaca OHLCV.
- qfa normalizes nonzero weights to gross 1.0; cash scaling is represented only by returning all-zero outside event windows.
- Turnover costs are external proxy; qfa has no native cost/slippage flags.
- Parent AR-086 is rejected; this result is treated only as a divergent sector dispersion idea, not a refinement of fixed-income carry.
