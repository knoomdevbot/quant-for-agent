# AR-011 Evaluation — meanrev-zscore-liquid-etf-regime-cost-v1

## Suggested decision

**REJECTED** — Median random-window Sharpe after 5 bps one-way turnover cost is <= 0, failing AR-011 falsifier.

## Data and commands

- Data source: Alpaca real daily market data via qfa CLI and qfa `AlpacaGateway`; no CSV and no `--data-csv`.
- Symbols: SPY, QQQ, IWM, TLT, GLD, SLV, XLF, XLK, XLE, XLV.
- Primary window: 2024-01-01 to 2025-12-31; random protocol uses 30 sampled 252-trading-day windows from 2019-01-01 to 2025-12-31.
- qfa DB used during run: `/var/folders/_5/pc0mst9956sdt25yf5hxh4vr0000gn/T/qfa_ar011_XXXXXX.sqlite.8jvzquJMOF`; DB artifact retained: `false`.
- qfa primary run id: `1`.
- Immutable run JSON: `/Users/moonk/quant-for-agent/models/meanrev-zscore-liquid-etf-regime-cost-v1/evaluations/runs/qfa_real_alpaca_ar011_20260626T064008Z.json`.

## Primary metrics

- qfa/pre-cost total return: `0.0191`.
- qfa/pre-cost annualized return: `0.0096`.
- qfa/pre-cost Sharpe: `0.1718`.
- qfa/pre-cost max drawdown: `-0.1149`.
- qfa/pre-cost win rate: `0.1040`.
- qfa/pre-cost periods: `500`.
- Cost-adjusted Sharpe, 5 bps one-way: `-0.3660`.
- Cost-adjusted annualized return: `-0.0277`.
- Cost-adjusted max drawdown: `-0.1432`.
- Cost-adjusted win rate: `0.0940`.
- Average daily one-way turnover proxy: `0.298235`.

## Random-window results

- Median random-window pre-cost Sharpe: `0.3786`.
- Median random-window cost-adjusted Sharpe: `-0.0434`.
- Median random-window cost-adjusted annualized return: `-0.0046`.
- Median random-window cost-adjusted max drawdown: `-0.0678`.
- Median random-window cost-adjusted win rate: `0.0578`.

## Orthogonality

Unavailable: no canonical accepted-alpha return stream or orthogonality harness exists in this repository for AR-011 comparison.

## Child ideas

- Refinement: **AR-011-R1 — Long-only oversold ETF rebound with adaptive volatility cutoff.** Remove short legs and allow cash during high-volatility regimes to reduce trend-fighting losses.
- Divergent: **AR-011-D1 — Cross-sectional ETF dispersion convergence after macro shock days.** Trade residual ETF dispersion convergence after large SPY/TLT/GLD disagreement days.

## Warnings

- qfa CLI metrics are pre-cost; this evaluation applies a separate 5 bps one-way turnover haircut.
- Daily close-to-close proxy excludes bid/ask spread dynamics, market impact, borrow/short availability, ETF liquidity microstructure, and intraday fill timing.

- **Bad-result policy:** rejected result; no refinement/extension child should be created because bad hypotheses are pruned rather than extended.
