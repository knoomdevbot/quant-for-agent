# AR-014 evaluation: mega-cap post-earnings drift proxy

Created: 2026-06-26T07:25:11Z

## Verdict

Suggested decision: **rejected**. Rejected for robustness despite positive random median Sharpe: main run lost 74.31% with -92.82% max drawdown and one random window lost 91.19% with -92.71% drawdown.

## qfa / data

- qfa Alpaca real market data only; `--data-csv` not used.
- No daemon run; no orders/trades placed.
- Temporary DB used: `/tmp/qfa-ar014-research-98284.sqlite3`; removed after JSON extraction.
- Universe: `AAPL,MSFT,NVDA,AMZN,META,GOOGL,TSLA`; timeframe: 1Day.

## Main metrics (2022-01-03 to 2025-12-15)

- Sharpe: 0.10436232
- Total return: -0.74309599
- Annualized return: -0.29244556
- Annualized volatility: 0.54699733
- Max drawdown: -0.92820358
- Win rate: 0.47676768
- Periods: 990

## Random-period protocol

- Windows: 6
- Median Sharpe: 0.83975742
- p25 Sharpe: 0.23852784
- Worst Sharpe: -1.00292976
- Positive-window rate: 0.83333333 (5/6)
- Worst max drawdown: -0.9271268
- Median total return: 0.15665476

## Turnover estimate

- Mean daily one-way turnover: 0.08099117
- Median daily one-way turnover: 0.00620529
- Max daily one-way turnover: 1.0
- Exposure-day rate: 0.88787879

## Orthogonality

[
  {
    "path": "/Users/moonk/quant-for-agent/models/crosssec-momentum-liquid-megacap-daily-v1/evaluations/latest.json",
    "model_name": "crosssec-momentum-liquid-megacap-daily-v1",
    "overlap_periods": 489,
    "correlation": 0.46785201
  }
]

## Warnings

- Price/volume proxy only; no point-in-time earnings calendar in this qfa/Alpaca path.
- Metrics are pre-cost because current qfa has no cost/slippage argument.
