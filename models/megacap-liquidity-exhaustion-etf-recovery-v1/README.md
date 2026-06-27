# megacap-liquidity-exhaustion-etf-recovery-v1

## Hypothesis

Broad capitulation across liquid US mega-cap equities can identify forced-selling liquidity exhaustion before ETF allocation normalizes. The model uses constituent OHLCV breadth for the signal, but trades only diversified ETFs or cash-like exposure.

## Signal Definition

- Fixed ex-ante signal universe: 60 liquid mega-cap US equities selected for Alpaca daily coverage, dollar-volume, sector diversity, and broad market relevance before performance review.
- Fixed tradable universe: 20 liquid ETFs spanning broad equity, sectors, duration/cash, gold, low-volatility, and quality.
- Daily features: abnormal dollar-volume z-score, high-low range expansion, downside-return breadth, close-location/recovery breadth, 63-day ETF trend, and realized-volatility penalty.
- Output: long-only ETF weights; single names are never traded by this model.

## Parameters

See `config.yaml`. Primary cost threshold is 10 bps one-way turnover cost with 5/10/20 bps sensitivity.

## Evaluation Summary

Latest real-data evaluation is in `evaluations/latest.json` and `evaluations/latest.md`.

## Orthogonality / Redundancy

The evaluation compares compact model return streams to available retained library summaries/proxies where raw streams are unavailable, with special attention to AR-043/AR-046 liquidity-reversal family overlap and SPY/equal-weight ETF proxies.

## Known Risks

- Fixed current mega-cap universe creates survivorship bias.
- Signal may be a broad market rebound or AR-043/AR-046 clone rather than a distinct breadth edge.
- Daily-bar timing approximates next-close execution and cannot observe intraday liquidity restoration.
- Stress-cluster activation can make random-window metrics unstable.

## Change Log

- 2026-06-27: Initial AR-119 implementation and real-data evaluation artifacts.
