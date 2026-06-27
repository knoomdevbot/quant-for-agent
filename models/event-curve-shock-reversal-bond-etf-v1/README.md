# AR-070: event-curve-shock-reversal-bond-etf-v1

Research alpha for scheduled FOMC/CPI/NFP bond ETF curve-shock reversal/continuation behavior. The model is explicitly event-gated and is flat outside a short post-event window, so it is not a continuous AR-061 duration/carry allocator.

- Universe: SHY, IEF, TLT, TIP, LQD, HYG, GLD, SPY.
- Data: Alpaca real daily OHLCV through qfa; no CSV and no `--data-csv`.
- Event calendar: hardcoded public FOMC/CPI/NFP release/statement dates in `model.py`.
- Trading side effects: none; no daemon, no orders.
- Cost proxy: 5 and 10 bps one-way on daily target-weight turnover.

Evaluation artifacts are in `evaluations/latest.json`, `evaluations/latest.md`, and `evaluations/runs/`.
