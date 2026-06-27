# xsec-etf-defensive-rotation-v1

AR-016 research model: a cross-sectional ETF defensive rotation alpha derived as a divergent child of AR-003.

## Hypothesis

Relative strength and defensive rotation across liquid ETFs may capture cross-asset regime allocation that is distinct from single-asset time-series momentum.

## Mechanism

The model ranks ETFs cross-sectionally using blended 63-day and 126-day returns penalized by 20-day realized volatility. It chooses the risk-on basket only when risk-on median score beats the defensive median and SPY blended momentum is positive; otherwise it rotates to defensive ETF winners. Allocation is long-only, top-3, inverse-vol scaled, and gross-normalized by qfa.

## Universe

SPY, QQQ, IWM, XLV, XLY, XLE, XLU, XLP, TLT, IEF, GLD.

## Data and execution constraints

- Evaluated with qfa AlpacaGateway real Alpaca market data only.
- `--data-csv` is not used.
- No daemon is run.
- No trades are placed.
- qfa in this repository does not provide native transaction-cost/slippage modeling, so qfa performance metrics are pre-cost; evaluation artifacts also include reconstructed target-weight turnover and a requested 5 bps cost assumption.

## Files

- `model.py`: qfa-compatible alpha.
- `config.yaml`: research/evaluation configuration.
- `metadata.yaml`: issue metadata.
- `evaluations/latest.json` and `latest.md`: latest evaluation summary.
- `evaluations/runs/*.json`: immutable evaluation record.
