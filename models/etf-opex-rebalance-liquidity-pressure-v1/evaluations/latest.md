# AR-106 evaluation — ETF OPEX/rebalance liquidity-pressure reversal

- Data: qfa/Alpaca real daily market bars only; no CSV; no daemon; no orders.
- Universe: fixed ex ante 30 ETF pool across index, sector, style/factor, bond/credit, commodity sleeves.
- Primary: 2021-01-04 to 2026-06-25, event-gated and standard turn-of-month excluded.
- Decision: **rejected**. At 10 bps the random-window median Sharpe is not robustly positive and p25/worst windows are materially negative; ex-turn-of-month event gating is sparse and noisy.

## Primary metrics

| cost | Sharpe | Ann ret | Ann vol | Max DD | Ann turnover | Activation |
|---|---:|---:|---:|---:|---:|---:|
| 0 bps | -0.2991 | -0.0079 | 0.0253 | -0.1126 | 9.17 | 0.0364 |
| 5 bps | -0.4790 | -0.0124 | 0.0254 | -0.1257 | 9.17 | 0.0364 |
| 10 bps | -0.6567 | -0.0169 | 0.0255 | -0.1385 | 9.17 | 0.0364 |
| 20 bps | -1.0015 | -0.0259 | 0.0259 | -0.1698 | 9.17 | 0.0364 |

## Random windows at 10 bps

Median Sharpe -0.6306; p25 -1.7621; worst -2.3650; positive-window rate 36.36%; worst max DD -0.0569; median annualized turnover 7.97; median activation 0.0316.

## Ablations and orthogonality

OPEX-only ex-ToM 10 bps Sharpe -1.0451; quarterly-only ex-ToM 10 bps Sharpe 0.1736; all event windows including ToM 10 bps Sharpe -0.6567. Max absolute proxy correlation: 0.4278.

Warnings: daily OHLCV lacks direct option flow, ETF creation/redemption, and auction imbalance data; orthogonality is proxy-only; no raw bars/equity/return paths retained.
