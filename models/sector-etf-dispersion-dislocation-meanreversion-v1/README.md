# sector-etf-dispersion-dislocation-meanreversion-v1

AR-075 research alpha for AOI AlphaEvolve qfa.

## Hypothesis

Short-horizon sector ETF dispersion dislocations can mean-revert after broad market-adjusted sector moves. The model fades relative sector residual outliers rather than allocating to defensive carry or simple single-ETF mean reversion.

## Model

`model.py` exposes qfa-compatible `generate_signals(context) -> dict[symbol, weight]`.

Universe: `SPY, QQQ, IWM, XLF, XLK, XLE, XLU, XLV, XLI, XLP`.

Signal steps:

1. Build daily close matrix from qfa/Alpaca context bars.
2. Estimate sector beta to SPY over 60 sessions.
3. Compute 5-day sector residual returns versus SPY.
4. Trigger only when cross-sectional sector residual dispersion is elevated versus a 63-session history.
5. Fade sector residual outliers, volatility-normalize, cap sector weights, and add an SPY hedge to reduce broad beta.
6. Return zero weights outside dislocation regimes.

## Evaluation

Evaluation used Alpaca real daily OHLCV through qfa repository components only. No CSV, no `--data-csv`, no qfa daemon, and no orders. Temporary SQLite DB was under `/tmp` and removed.

Costs/slippage were applied externally as a target-weight turnover haircut because qfa native transaction-cost flags are unavailable:

`adjusted_return = gross_return - one_way_turnover * bps / 10000`

Primary period: 2024-01-01 to 2025-12-31. Random protocol: 10 deterministic pseudo-random/stress windows across 2019-2025, with 5 bps and 10 bps one-way turnover proxies.

## Results

Suggested decision: **rejected**.

- Primary 5 bps Sharpe: `0.43709188`
- Primary 5 bps annualized return: `0.01924321`
- Primary 5 bps max drawdown: `-0.02449612`
- Random-window median 5 bps Sharpe: `-0.414531`
- Random-window p25 5 bps Sharpe: `-0.76493942`
- Random-window worst 5 bps Sharpe: `-0.94985866`
- Positive random-window rate: `0.2`
- Worst max drawdown including primary: `-0.09659022`
- Orthogonality: `limited_no_retained_curves`; prior compact artifacts did not retain enough daily/equity curves for most requested comparisons.

The falsifier was met because median random-window Sharpe after the 5 bps turnover haircut was below zero and p25 was materially negative.

## Artifacts

- `model.py`
- `config.yaml`
- `metadata.yaml`
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/ar075_qfa_alpaca_real_20260626T132259Z.json`
