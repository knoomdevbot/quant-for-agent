# xsec-etf-defensive-rotation-orthogonal-v1 (AR-051)

Research-only qfa alpha refining AR-039. `model.py` exposes `generate_signals(context)` and consumes only qfa-provided OHLCV bars.

## Idea

The parent AR-039 monthly ETF defensive rotation reduced turnover but remained economically close to existing TSMOM/carry-defensive watchlist alphas. This child keeps the monthly cross-sectional ETF rotation but subtracts an explicit trailing correlation penalty from candidate ETF scores. The penalty uses same-panel ETF return proxies for:

- TSMOM-like trend exposure: `SPY, QQQ, TLT, GLD`
- Carry/defensive exposure: `IEF, TLT, GLD, XLP, XLU, SHY`

## Universe

`SPY, QQQ, IWM, XLV, XLY, XLE, XLU, XLP, TLT, IEF, GLD, SHY`

## Signal

1. Use prior month-end data to keep weights constant within each calendar month.
2. Compute blended 63/126-day momentum divided by 63-day realized volatility.
3. Penalize each ETF by `corr_penalty * max(abs(corr_to_tsmom_proxy), abs(corr_to_carry_defensive_proxy))` over 63 days.
4. Select risk-on ETFs only if penalized risk-on median beats defensive median and SPY momentum is positive; otherwise select defensive ETFs.
5. Hold top 2 ETFs, inverse-vol scaled, gross-normalized to 1.0 and capped at 50% per ETF.

## Evaluation

Evaluation artifacts in `evaluations/` use Alpaca real market data through qfa. No `--data-csv`, daemon, or orders were used. qfa does not natively model costs, so evaluations replayed target weights and applied external one-way turnover haircuts at 10 bps (primary) and 20 bps (stress).
