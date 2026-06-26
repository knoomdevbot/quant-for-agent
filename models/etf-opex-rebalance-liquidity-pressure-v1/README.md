# ETF OPEX/rebalance liquidity-pressure reversal (AR-106)

Research-only qfa alpha using Alpaca/qfa real daily OHLCV bars. The selected ETF universe was fixed ex ante from the issue candidate pool across equity index, sectors, style/factor, bonds/credit, and commodity sleeves; no return-ranked selection was used.

The model is strictly event-gated to monthly third-Friday OPEX weeks / quarterly expiry-rebalance weeks and excludes standard turn-of-month windows by default. Within event windows it looks for abnormal volume, extreme close location, short pressure return, failed follow-through, and a realized-volatility skip filter, then takes contrarian next-session ETF weights.

Evaluation artifacts are compact: summary metrics only, no raw bars, equity curves, daily return paths, caches, or retained helper scripts. No daemon or order path was used.

Decision: **rejected**. The 10 bps random-window distribution was not robustly positive and the ex-turn-of-month gated signal remained sparse/noisy.
