# AR-068 latest evaluation

- Model: `residual-close-location-reversal-opportunity-balanced-v1`
- Data: Alpaca real market data via qfa; no CSV / no `--data-csv`
- qfa run IDs: smoke `1`, primary `2`, replay `3`
- Safety flags: raw_daily_paths_retained=false, no_daemon=true, no_orders=true

## Metrics (5 bps turnover haircut)

| metric | value |
|---|---:|
| primary Sharpe | -1.6332 |
| median_sharpe | -0.9621 |
| p25_sharpe | -1.8732 |
| worst_period_sharpe | -3.2054 |
| annualized_return | -0.1790 |
| annualized_volatility | 0.1166 |
| max_drawdown | -0.3813 |
| avg_daily_turnover | 0.5695 |
| annualized_turnover | 143.5250 |
| opportunity_days | 436 |
| positive_window_rate | 0.00 |

## Orthogonality

```json
{
  "AR-028_closing_volume_reversal_megacap_v1": {
    "correlation": 0.17429319,
    "overlap_days": 500,
    "status": "available"
  },
  "AR-045_closing_volume_reversal_costaware_megacap_v1": {
    "correlation": 0.04334972,
    "overlap_days": 500,
    "status": "available"
  },
  "AR-056_closing_volume_reversal_orthogonalized_megacap_v1": {
    "correlation": 0.04092534,
    "overlap_days": 500,
    "status": "available"
  },
  "SPY_market_proxy": {
    "correlation": 0.13720393,
    "overlap_days": 500,
    "status": "available"
  },
  "equal_weight_universe": {
    "correlation": 0.13879032,
    "overlap_days": 500,
    "status": "available"
  }
}
```

## Decision

**rejected** — Rejected by falsifier: median/primary cost-adjusted Sharpe <= 0.

Warnings: external costs only; adjusted-price controls unavailable in qfa AlpacaGateway; no raw daily paths retained.
