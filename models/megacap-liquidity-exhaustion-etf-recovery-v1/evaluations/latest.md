# AR-119 evaluation: megacap-liquidity-exhaustion-etf-recovery-v1

- Run: `ar119_qfa_alpaca_real_20260627T033919Z`
- Data: qfa/Alpaca real daily OHLCV, 2018-01-01 to 2026-06-26; configured paper-data access with credential values redacted.
- Controls: no CSV, no data-csv argument, no daemon, no orders; raw daily paths not retained.
- Smoke/contract: passed `qfa backtest run` on configured real daily market data for 2025-01-02 to 2025-03-31 using a temporary DB that was deleted; flat output was expected because the short smoke window is below warmup.
- Decision: **rejected**

## 10 bps headline metrics

- Median random-window Sharpe: -0.5372
- p25 Sharpe: -1.0768
- Worst window Sharpe: -1.766
- Positive window rate: 0.3
- Full-period annualized return: -0.0273
- Full-period annualized volatility: 0.1037
- Full-period max drawdown: -0.2866
- Average turnover: 0.1987
- Activation: 0.6647

## Cost sensitivity

{
  "0": {
    "sharpe": 0.268,
    "annualized_return": 0.0226,
    "max_drawdown": -0.2004
  },
  "5": {
    "sharpe": 0.0263,
    "annualized_return": -0.0027,
    "max_drawdown": -0.2411
  },
  "10": {
    "sharpe": -0.2151,
    "annualized_return": -0.0273,
    "max_drawdown": -0.2866
  },
  "20": {
    "sharpe": -0.6965,
    "annualized_return": -0.0749,
    "max_drawdown": -0.421
  }
}

## Orthogonality

Max absolute correlation to available relevant replay/proxy benchmarks: `0.7606`.
Correlations: `{'SPY': 0.6551, 'QQQ': 0.651, 'IWM': 0.6579, 'TLT': 0.1465, 'GLD': 0.1666, 'equal_weight_megacap_proxy': 0.6512, 'AR-043_replayed_proxy': 0.7606}`.

## Rationale

- Failed robustness thresholds after costs or had insufficient positive random-window breadth.
- High correlation to a relevant benchmark/library proxy limits standalone novelty.

## Warnings

- Fixed current mega-cap signal universe has survivorship bias.
- BRK.B or other ticker coverage may be unavailable depending on Alpaca symbol support; failed symbols are summarized by count/name only.
- Daily close-to-next-close replay is an approximation, not live-executable intraday liquidity capture.
