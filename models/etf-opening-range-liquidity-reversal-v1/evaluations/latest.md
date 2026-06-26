# AR-085 evaluation latest

- Model: `etf-opening-range-liquidity-reversal-v1`
- Created UTC: 2026-06-26T15:12:12Z
- Status: `completed_bounded_real_intraday`
- Decision: **reject**
- Reason: Bounded Alpaca/qfa 1Min evaluation did not produce sufficient robust positive activation; rejected rather than promoting.
- Data: Alpaca/qfa real 1Min OHLCV via AlpacaGateway; no CSV; no --data-csv; no daemon; no orders; secrets not printed.
- CSV/`--data-csv`: not used. Daemon/orders: not used. Secrets: not printed or stored.
- Immutable run JSON: `/Users/moonk/quant-for-agent/models/etf-opening-range-liquidity-reversal-v1/evaluations/runs/ar085_qfa_alpaca_real_20260626T151212Z.json`

## Metrics

```json
{
  "median_sharpe_10bps": -0.04427722,
  "p25_sharpe_10bps": -0.41766358,
  "unavailable_if_no_events": false
}
```

## Window summary

```json
{
  "attempted": true,
  "count": 3,
  "median_sharpe_10bps": -0.04427722,
  "p25_sharpe_10bps": -0.41766358,
  "positive_window_rate_10bps": 0.33333333,
  "total_active_events": 51
}
```
