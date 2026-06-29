# AR-147 — FRED weekly financial-conditions shock ETF allocator

Decision: **rejected**.

Primary signal was predeclared as Chicago Fed NFCI from FRED. Direction was fixed before evaluation: positive 4-week NFCI shock = tighter financial conditions/risk-off sleeve; negative shock = easing/relief sleeve. A conservative availability lag of observation date + 7 calendar days was used; daily positions were entered only at/after the qfa trading close and earned the next daily return.

## Universe
Fixed economic/liquidity coverage universe selected before performance: SPY, QQQ, IWM, DIA, sector ETFs, duration/TIPS/credit, SHY cash-like sleeve, GLD/DBC, USD/FX proxies, VNQ, USMV/QUAL/MTUM. All 27 requested symbols had 2,127 Alpaca/qfa daily bars over 2018-01-02 to 2026-06-18.

## Primary metrics, 10 bps one-way turnover cost
- Sharpe: 0.72927206
- Total return: 0.62387446
- Annualized return: 0.05914958
- Annualized volatility: 0.08360936
- Max drawdown: -0.19600201
- Mean daily turnover: 0.04515522; annualized turnover: 11.37911571
- Activation frequency: 0.5098777
- Sleeve day share: cash 0.490122; relief 0.265287; stress 0.244591
- Top symbol by absolute weight: SHY, share 0.55126999

## Cost sensitivity
- 5 bps Sharpe: 0.79834372; total return: 0.70383091; max DD: -0.18972452
- 20 bps Sharpe: 0.59039067; total return: 0.47484801; max DD: -0.20842781

## Random windows
12 deterministic 1-year windows: median Sharpe 0.68214063; p25 0.02402053; worst -2.18022236; positive rate 0.75. Robustness fails because the worst window is deeply negative and performance is uneven.

## Controls and redundancy
- ETF TSMOM: Sharpe 0.24051167; correlation 0.44868989
- Price-only stress: Sharpe -0.0601405; correlation 0.55882736
- Shifted release labels: Sharpe 0.0110116; correlation 0.52605909
- Same-weekday placebo: Sharpe 0.17436637; correlation 0.27279414
- Inverted direction: Sharpe -0.01937873; correlation 0.24664604

Hostile priors from AR-008/037/043/051/063/080/088/105/135/136 remain relevant: the result is economically close to risk-off/defensive/cash-like ETF allocation, and official weekly labels/vintages are fragile.

## Why rejected
Despite positive primary and median random-window metrics, acceptance is barred by (1) latest FRED vintage rather than point-in-time ALFRED vintage, so revision leakage risk remains; (2) worst random-window Sharpe -2.18; (3) SHY cash-like sleeve dominates; and (4) redundancy with price-only/risk-off controls is high enough to be hostile.

## Provenance
qfa/Alpaca real daily bars only; no CSV and no `--data-csv`; no daemon; no orders; no raw daily returns/equity/weights arrays retained. Compact derived weekly shock records only are embedded in `model.py`.
