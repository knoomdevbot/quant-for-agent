# AR-024 evaluation: post-earnings-drift-megacap-v1

- Data: Alpaca real market data through qfa; no CSV/`--data-csv`; no daemon; no trades.
- Primary: 2022-01-03 to 2025-12-15, symbols AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA.
- qfa run ids: {'primary': 1, 'random1_20231206_20240829': 2, 'random2_20220502_20230120': 3, 'random3_20230217_20240328': 4, 'random4_20220211_20230330': 5, 'random5_20231115_20241028': 6, 'random6_20240919_20250710': 7, 'random7_20211116_20220721': 8, 'random8_20221230_20231206': 9}
- Primary qfa pre-cost Sharpe: -0.28729; return: -0.89345743; max drawdown: -0.94521027; win rate: 0.26060606; periods: 990.
- Random windows: 8; median Sharpe: 0.04901952; positive Sharpe windows: 4/8; worst drawdown: -0.92547727.
- Costs/slippage: qfa has no cost parameter, so reported qfa metrics are pre-cost. Mean one-way turnover estimate: 0.10481861 at 5.0 bps assumption.
- Orthogonality: computed.
- Earnings-date limitation: no real earnings-calendar feed was available through qfa/Alpaca; no dates fabricated; documented OHLCV proxy used.
- Suggested decision: **rejected** — Rejected: primary Sharpe is non-positive or random-window median Sharpe/drawdown failed the AR-024 falsifier after considering cost sensitivity.

Artifacts:

- latest JSON: `/Users/moonk/quant-for-agent/models/post-earnings-drift-megacap-v1/evaluations/latest.json`
- immutable run JSON: `/Users/moonk/quant-for-agent/models/post-earnings-drift-megacap-v1/evaluations/runs/ar024_qfa_alpaca_real_20260626T075845Z.json`
