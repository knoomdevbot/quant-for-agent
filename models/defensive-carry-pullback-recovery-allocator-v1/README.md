# defensive-carry-pullback-recovery-allocator-v1

## Hypothesis

A short-horizon pullback-recovery effect may exist inside defensive/carry ETFs that remain in a positive intermediate trend during benign or moderate stress. The allocator attempts to buy recovery setups in duration, credit, gold, low-volatility, utilities, staples, and healthcare while avoiding crisis regimes.

## Signal Definition

- Candidate universe: 28 liquid ETFs spanning cash/duration, TIPS, credit, gold/silver, commodities, broad/style equity, and sector sleeves.
- Eligibility: at least 90 daily bars, positive 63-day return, and positive 63-day return per realized volatility.
- Stress gate: requires SPY 20-day return between -8% and +3%, SPY realized volatility below crisis levels, and no severe HYG/LQD breakdown.
- Score: risk-adjusted trend, 5-day pullback z-score, 2-day rebound/stabilization, defensive/carry bias, and low-volatility bonus.
- Portfolio: long-only top 3 ETFs by score, score weighted, with SHY fallback when the gate or candidates are inactive.

## Parameters

See `config.yaml`. Primary decision threshold uses 10 bps one-way turnover cost with 0/5/10/20 bps sensitivity.

## Evaluation Summary

Real-data evaluation artifacts are in:

- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/ar118_qfa_alpaca_real_20260627T043642Z.json`

Status suggestion: **rejected**. The full model failed primary and random-window 10 bps robustness thresholds.

Key 10 bps metrics:

- Full-period Sharpe: `-1.241678`
- Annualized return: `-0.175841`
- Max drawdown: `-0.674394`
- Random-window median Sharpe: `-1.7066`
- Random-window positive rate: `0.0`
- Max abs correlation to retained ETF/proxy benchmarks: `0.4464`

## Data / Safety Contract

Evaluation used qfa/Alpaca real daily OHLCV via configured paper-data access. No CSV, no `--data-csv`, no daemon, and no orders/trades were used. Compact artifacts retain no raw bars, daily return paths, equity curves, or weight tails.

## Known Risks and Limitations

- Alpaca/IEX paper-data access returned truncated history before 2020 for most ETFs, so the requested 2018-present protocol is only partially covered by returned real bars.
- Orthogonality could not fully compare against AR-015/037/049/051/060/061/067/071/105 raw streams because compact prior artifacts generally do not retain daily return paths.
- Daily close-to-next-close replay approximates execution and does not model intraday fill quality or live rebalance constraints.
