# AR-084: Mega-cap post-earnings volume-vacuum reversal allocator

Research model: `megacap-earnings-volume-vacuum-reversal-v1`.

## Hypothesis

Mega-cap earnings-like event moves accompanied by abnormal volume should mean-revert when the subsequent several sessions show a volume drought and failed follow-through. The model goes long failed negative overreactions and short failed positive overreactions, with dollar/beta neutralization, inverse-volatility scaling, per-name caps, and a high-market-volatility brake.

## Data limitation

A point-in-time public earnings-date calendar was not safely available through qfa/Alpaca daily OHLCV. The implementation therefore uses an OHLCV proxy for earnings-like events: abnormal event volume plus large residual return. This avoids future leakage in the qfa signal path, but it may include non-earnings news, index-flow, or macro event days.

## Evaluation

- Data: Alpaca real daily market data through qfa/AlpacaGateway only.
- CSV: none; no `--data-csv`.
- Trading: no daemon and no orders.
- Storage: temporary SQLite DBs only; deleted after qfa runs; no raw daily data paths retained.
- Costs: qfa has no native cost flag, so a 5 bps one-way target-turnover haircut was applied in an external replay of the same Alpaca bars/model weights.

## Latest result

Suggested decision: **rejected**.

Primary 2024-01-01 to 2025-12-31 after 5 bps costs:

- Sharpe: `0.63444419`
- Annualized return: `0.01587829`
- Annualized volatility: `0.02533439`
- Max drawdown: `-0.01965929`
- Mean daily one-way turnover proxy: `0.01383202`

Random windows (8 annual windows, 2018-2025) after 5 bps costs:

- Median Sharpe: `0.07856542`
- p25 Sharpe: `-0.77604925`
- Worst Sharpe: `-1.41967623`
- Positive-window rate: `0.5`

The issue falsifier is triggered by materially negative p25/worst random-window Sharpe and low positive-window rate despite a positive primary period.

## Orthogonality

Available peer artifacts for liquidity reversal/watchlist streams lacked retained daily return series, so direct peer correlations could not be computed. Same-universe equal-weight daily return correlation over the primary period was `-0.09265053`; available max absolute correlation was below 0.60.

## Artifacts

- `model.py`
- `config.yaml`
- `metadata.yaml`
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/ar084_qfa_alpaca_real_20260626T143425Z.json`
