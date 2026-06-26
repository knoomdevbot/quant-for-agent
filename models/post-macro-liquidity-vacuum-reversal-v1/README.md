# post-macro-liquidity-vacuum-reversal-v1 (AR-053)

Research-only qfa alpha for deterministic scheduled-macro proxy date liquidity-vacuum reversal in liquid ETFs. Uses only qfa/Alpaca daily OHLCV bars; no CSV fixtures, no daemon, and no live trading.

## Hypothesis

After large same-day range expansion around deterministic macro proxy dates, the ETF sleeves that lag/close poorly may mean-revert over the next 1-3 sessions.

## Signal

Universe: `SPY, QQQ, IWM, TLT, GLD, XLU, XLE`. Deterministic proxies include first-Friday payroll, CPI days 10-14, FOMC third-Wednesday neighborhoods in regular meeting months, and mid-quarter liquidity dates. If SPY/TLT/GLD range expansion is abnormal, the model buys up to three lagging/poor-close ETF sleeves using inverse-volatility-scaled scores and a 1/2/3-session decay.

## Evaluation

- Data: Alpaca real daily OHLCV via qfa AlpacaGateway; no CSV; no --data-csv
- Fetch range: 2019-01-01 to 2025-12-31; primary evaluation: 2021-01-04 to 2025-12-15
- Costs/slippage: qfa native costs unavailable; applied 5 bps one-way turnover haircut ex post.
- Random windows: 8 seeded real-data windows.

## Results after costs

| Metric | Value |
|---|---:|
| Primary Sharpe | 0.49240692 |
| Primary annualized return | 0.0324517 |
| Primary annualized volatility | 0.06975364 |
| Primary max drawdown | -0.13532074 |
| Primary avg daily turnover | 0.1002045 |
| Median random-window Sharpe | 0.18538839 |
| p25 random-window Sharpe | -0.5284254 |
| Worst random-window Sharpe | -1.01566838 |
| Positive random-window rate | 0.5 |

Random-window Sharpes: `-1.01566838, 0.39920934, -0.44543003, 1.06456542, -0.02843256, 1.08683613, 0.51335098, -0.77741152`.

## Orthogonality

Status: `low_to_moderate_redundancy`; max absolute computed correlation: `0.29718076`. See `evaluations/latest.json` for per-model comparisons.

## Decision

**Suggested decision: reject_or_park_do_not_refine.** Fails acceptance: primary post-cost Sharpe 0.49240692, median random Sharpe 0.18538839, p25 random Sharpe -0.52842540, orthogonality status low_to_moderate_redundancy.
