# closing-volume-reversal-orthogonalized-megacap-v1 (AR-056)

Refinement of AR-045 that tests whether abnormal close-location / abnormal-volume reversal survives explicit orthogonality constraints.

## Hypothesis

AR-045 may partly monetize broad market mean reversion. This model only trades stronger close-location events when the stock also has a same-direction idiosyncratic residual versus the equal-weight mega-cap basket, then beta/dollar-neutralizes the raw signal vector.

## Universe

AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, TSLA, JPM, LLY.

## Signal summary

- daily close-location value from Alpaca/qfa OHLCV;
- share-volume and dollar-volume z-score gates;
- range expansion gate;
- rolling beta residual z-score confirmation versus equal-weight basket;
- market-volatility and absolute basket-move gates;
- inverse-volatility sizing, beta neutralization, cross-sectional demeaning, per-name cap, and turnover dampening.

## Evaluation protocol

Use qfa with Alpaca real daily market data only. Do not use `--data-csv`, daemon mode, or order placement. qfa has no native transaction-cost flag, so evaluation applies an external 5 bps one-way turnover haircut to replayed target weights.

Artifacts are in `evaluations/latest.json`, `evaluations/latest.md`, and immutable `evaluations/runs/*.json`.
