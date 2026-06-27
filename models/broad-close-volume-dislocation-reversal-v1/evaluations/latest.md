# AR-103 evaluation: broad-close-volume-dislocation-reversal-v1

- evaluation_status: completed_compact_real_data_backtest
- suggested_decision: rejected
- decision_reason: Falsifier tripped at 10 bps: random-window median/p25 Sharpe was not robustly positive or activation/turnover did not justify broadening.
- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false

## Protocol

Real daily market bars via the project data gateway. Compact recovery run: primary 2023-01-03 to 2025-12-31, plus 7 random/stress windows. Evaluated 5/10/20 bps one-way turnover costs. No raw bars, equity curves, or weight tails retained.

## Primary 10 bps

- Sharpe: 0.14208352
- Annualized return: 0.00610005
- Annualized volatility: 0.23719399
- Max drawdown: -0.25391653
- Annualized one-way turnover: 237.03073379
- Activation fraction: 0.48666667

## Random-window 10 bps summary

- Count: 7
- Median Sharpe: -0.04077626
- P25 Sharpe: -0.59216684
- Worst Sharpe: -1.87821482
- Positive-window rate: 0.42857143
- Worst max drawdown: -0.39077726
- Median annualized one-way turnover: 226.56588319
- Median activation fraction: 0.46

## Orthogonality

- SPY proxy correlation: 0.00272722 over 750 periods
- Broad equal-weight universe correlation: 0.00403339 over 750 periods

## Conclusion

Falsifier tripped at 10 bps: random-window median/p25 Sharpe was not robustly positive or activation/turnover did not justify broadening. Because the hypothesis is rejected, no child idea is proposed; the failed broadening hypothesis is pruned.
