# AR-093: Crypto stress-to-quality flight defensive ETF allocator

## Summary

This model tests whether strictly lagged BTC/ETH stress events can improve a long-only defensive ETF allocator. The stress signal is derived from real Coinbase Exchange public daily candles for BTC-USD and ETH-USD, retained only as compact event intervals in `model.py`. ETF market prices were pulled from Alpaca real daily OHLCV via qfa/AlpacaGateway; no CSV market data or `--data-csv` was used.

## Timestamp discipline

For ETF signal date D, crypto features use only completed UTC daily crypto data through D-1. The qfa backtester then applies the generated ETF weights to the next daily ETF return. This is intentionally conservative and avoids same-day crypto lookahead.

## Selected universe

Selected liquid/mature ETF set: SPY, QQQ, IWM, TLT, IEF, SHY, GLD, HYG, LQD, XLU, XLP, XLV, USMV, QUAL.

The broader candidate pool considered included broad equity, high-beta/crypto-linked equities, duration/cash-like ETFs, gold/commodities, credit, defensive sectors, low-vol/quality, and crypto-linked names.

## Evaluation result

Suggested decision: **rejected**.

Primary 2020-01-02 to 2025-12-31 cost-adjusted results at 10 bps one-way turnover cost:

- Sharpe: 0.5098
- Annualized return: 4.1690%
- Annualized volatility: 8.7664%
- Max drawdown: -22.7825%
- Annualized one-way turnover: 11.2777x

Random/stress windows at 10 bps:

- Median Sharpe: 0.3315
- p25 Sharpe: -0.3154
- Worst Sharpe: -1.1821
- Positive-window rate: 58.33%

Rejected due to materially negative p25 Sharpe and failed available orthogonality check (max available absolute correlation 0.6135 vs AR-015 retained curve).

## Artifacts

- `model.py` exposes `generate_signals(context)`.
- `config.yaml` documents universe, data, parameters, and compliance flags.
- `metadata.yaml` records decision/provenance.
- `evaluations/latest.json` and `evaluations/latest.md` contain compact evaluation results.
- Immutable run: `evaluations/runs/ar093_qfa_alpaca_coinbase_crypto_20260626T155658Z.json`.

No raw equity curves, daily returns, model weights, raw external crypto arrays, SQLite DBs, caches, bytecode, daemon activity, orders, or secrets are retained.
