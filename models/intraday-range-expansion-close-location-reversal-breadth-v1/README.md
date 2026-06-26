# intraday-range-expansion-close-location-reversal-breadth-v1

AR-079 research alpha. The model is a qfa-compatible intraday ETF reversal breadth rule that uses Alpaca/qfa OHLCV bars only.

## Mechanism

For each completed 1-minute regular-session bar, the rule checks whether many ETFs simultaneously print range expansion versus their recent median minute range and close near the bar high or low. A broad downside close-location/range-expansion event is treated as forced-flow exhaustion and faded by buying risk/sector ETFs while underweighting defensive sleeves. A broad upside event is faded in reverse. Gross exposure is capped at 1.0 and single ETF weight at 0.18.

## Data and evaluation constraints

- Real Alpaca market data only through qfa/Alpaca tooling.
- No CSV fixtures and no `--data-csv`.
- No daemon and no orders.
- Costs are applied as an external one-way turnover haircut because qfa backtest has no native slippage flag.
- If qfa 1Min data is unavailable, the issue requires blocked/rejected rather than substituting the AR-071 daily skew logic.

## Files

- `model.py` exposes `generate_signals(context)`.
- `config.yaml` records parameters.
- `evaluations/latest.json` and `evaluations/latest.md` contain compact results.
- `evaluations/runs/*.json` contains immutable run snapshots.
