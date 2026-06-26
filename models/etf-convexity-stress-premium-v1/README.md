# etf-convexity-stress-premium-v1 (AR-050)

Divergent child of AR-037. This model tests whether an ETF allocator driven by realized-volatility/convexity stress proxies can earn defensive convexity premia without relying on the parent's carry allocation logic.

## Signal design

- Universe: `SPY, QQQ, IWM, TLT, IEF, SHY, GLD, XLU, VIXY`.
- Stress proxy: combines short/slow realized-volatility acceleration, fast/mid volatility convexity, downside-variance share, recent drawdown, high-low range z-score, and short-horizon loss across broad equity ETFs.
- Allocation:
  - calm regimes: diversified long-only risk and ballast exposure;
  - rising stress: rotates budget from risk ETFs toward `TLT/IEF/SHY/GLD/XLU` and permits a small capped `VIXY` convexity sleeve;
  - gross exposure may fall below 1.0, leaving implicit cash.
- Hard caps: max single ETF 34%, max VIXY 9%.

## Research constraints

- QFA-compatible `generate_signals(context)` only.
- Alpaca real daily OHLCV through qfa/AlpacaGateway only; no CSV data.
- No daemon, no live trading, no order placement.
- Native qfa backtest has no transaction cost field; evaluations apply a post-run 5 bps one-way turnover cost proxy.

## Evaluation status

See:

- `evaluations/latest.json`
- `evaluations/latest.md`
- immutable run bundle under `evaluations/runs/`
