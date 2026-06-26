# AR-035 qfa/Alpaca evaluation: etf-vol-risk-rotation-v1

- Created: 2026-06-26T08:34:47Z
- Data source: Alpaca real market data via qfa; no CSV and no `--data-csv`.
- Symbols: SPY,QQQ,IWM,TLT,GLD,SLV,XLF,XLK,XLE,XLV
- Primary range: 2021-01-04 to 2025-12-15, 1Day
- Temporary DB retained: false
- Suggested decision: **rejected**

## Primary qfa metrics, pre-cost

- Sharpe: 0.30528843
- Total return: 0.19339232
- Annualized return: 0.03652363
- Annualized volatility: 0.15888426
- Max drawdown: -0.2843525
- Win rate: 0.50563607
- Periods: 1242

## 5 bps one-way cost/slippage proxy

qfa `backtest run` exposes no native cost/slippage parameter, so costs were not applied by qfa. Ex-post turnover haircut estimate:

- Mean daily one-way turnover: 0.13391228
- Estimated annual cost drag: 0.01687295
- Approx cost-haircut Sharpe: 0.12367921

## Random-window stability

- Window count: 8
- Median random-window Sharpe: -0.18289894
- Mean random-window Sharpe: -0.2394129
- Min / max random-window Sharpe: -1.01571084 / 0.53208952

- Window 1: 2023-01-30 to 2024-07-23 | Sharpe 0.21295138 | return 0.03053048 | max DD -0.13072756 | win 0.42972973 | periods 370
- Window 2: 2022-10-19 to 2024-04-11 | Sharpe -0.00692696 | return -0.01250775 | max DD -0.14767402 | win 0.41463415 | periods 369
- Window 3: 2022-11-22 to 2024-05-15 | Sharpe 0.53208952 | return 0.09407715 | max DD -0.14767402 | win 0.42276423 | periods 369
- Window 4: 2021-10-29 to 2023-04-22 | Sharpe -0.1605968 | return -0.05863879 | max DD -0.25533766 | win 0.41891892 | periods 370
- Window 5: 2021-06-08 to 2022-11-30 | Sharpe -1.01571084 | return -0.2281599 | max DD -0.28149829 | win 0.42091153 | periods 373
- Window 6: 2022-10-11 to 2024-04-03 | Sharpe -0.20520108 | return -0.04719317 | max DD -0.14767402 | win 0.40921409 | periods 369
- Window 7: 2021-01-11 to 2022-07-05 | Sharpe -0.45176263 | return -0.09177324 | max DD -0.1973699 | win 0.46361186 | periods 371
- Window 8: 2021-12-02 to 2023-05-26 | Sharpe -0.82014582 | return -0.20221342 | max DD -0.25533766 | win 0.39622642 | periods 371

## Orthogonality

- Status: computed
- Method: Pearson correlation of daily qfa equity returns from retained latest.json curves
- risk-off-crossasset-randomcost-v1: corr 0.64517382 over 1241 periods
- tsmom-voltarget-liquid-etf-randomcost-v1: corr 0.63509311 over 488 periods
- post-earnings-drift-megacap-v1: corr -0.05004648 over 989 periods
- earnings-quality-drift-megacap-v1: corr -0.04516969 over 989 periods
- meanrev-zscore-liquid-etf-1d-v1: corr 0.03145054 over 488 periods

## Command

```bash
set -a; source /Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env; set +a; export ALPACA_API_KEY="${ALPACA_API_KEY:-${ALPACA_KEY_ID:-}}"; export ALPACA_PAPER=true; /Users/moonk/quant-for-agent/.venv/bin/qfa backtest run /Users/moonk/quant-for-agent/models/etf-vol-risk-rotation-v1/model.py --symbols SPY,QQQ,IWM,TLT,GLD,SLV,XLF,XLK,XLE,XLV --start 2021-01-04 --end 2025-12-15 --timeframe 1Day --initial-cash 100000 --db <temporary-sqlite-db>
```

## Decision rationale

Rejected: median random-window Sharpe and/or approximate cost-adjusted Sharpe failed acceptance threshold.
