# AR-065 — ETF realized-volatility term-state breadth allocator

Durable qfa alpha artifact for issue AR-065. This is a divergent volatility-breadth regime allocator from rejected AR-052 and intentionally avoids the VIXY/TLT stress-carry sleeve.

## Model

`model.py` exposes qfa-compatible:

```python
generate_signals(context) -> dict[str, float]
```

The model uses completed daily OHLCV bars supplied in `context.prices` and allocates long-only across:

`SPY, QQQ, IWM, TLT, GLD, XLU, XLE, SHY`

Core features:
- 10/20 and 20/60 realized-volatility term ratios.
- Cross-ETF volatility compression/expansion breadth.
- SPY downside-volatility surprise.
- SPY 126-day drawdown state.
- Defensive momentum confirmation across TLT/GLD/XLU/SHY versus equity proxies.

## Evaluation

Latest evaluation artifacts:
- JSON: `evaluations/latest.json`
- Markdown: `evaluations/latest.md`
- Immutable run: `evaluations/runs/ar065_qfa_alpaca_real_20260626T121125Z.json`

Safety/provenance:
- Data source was Alpaca/qfa real market data through qfa AlpacaGateway.
- No CSV was used; `--data-csv` was not used.
- No qfa daemon was run.
- No orders or live trading were placed.
- Temporary SQLite DBs were used for qfa run IDs and deleted after capture.

Primary range: 2020-01-02 to 2025-12-15, 1Day bars.

Primary qfa pre-cost metrics:
- Sharpe: 0.54771488
- Annualized return: 0.05587574
- Annualized volatility: 0.11046067
- Max drawdown: -0.19442805
- Total return: 0.38065111

Estimated after 5 bps one-way turnover cost:
- Sharpe: 0.40444051
- Annualized return: 0.0393107
- Mean daily one-way turnover: 0.12580745

Random windows:
- Count: 8
- Median after-cost estimated Sharpe: 0.91479255
- P25 after-cost estimated Sharpe: 0.58732363
- Positive after-cost Sharpe rate: 0.875

Orthogonality:
- Computed against retained watchlist/library curves where available.
- Max absolute correlation: 0.63897729
- Failed the issue threshold of max correlation <= 0.60.

## Suggested decision

**Rejected.** Performance was not the blocker in this run, but max retained-model correlation exceeded the AR-065 falsifier threshold. Under the bad-result policy for rejected parent AR-052/rejected result, no refinement, direct inversion, extension, or child is suggested.
