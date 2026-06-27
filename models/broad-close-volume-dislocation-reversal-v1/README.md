# broad-close-volume-dislocation-reversal-v1

AR-103 research model: a broad ex-ante liquid large-cap/ETF close-volume dislocation reversal test.

## Design

- Universe: liquid sector/broad ETFs plus highly liquid large-cap equities selected ex ante by liquidity and recognizability, not by returns.
- Signal: abnormal daily volume and dollar-volume, extreme close location in the daily range, contrarian next-session positioning, inverse-volatility normalization.
- Throttles: event-only activation, weak sign-flip dampening, persistence blend, symbol cap, ETF sleeve cap, high market-volatility kill switch.
- Intended use: research/backtest only.

## Real-data controls

- no_csv_used: true
- no_data_csv_argument_used: true
- no_daemon: true
- no_orders: true
- raw_daily_paths_retained: false

## Limitation

Daily bars are only a proxy for closing-auction pressure; they do not expose auction-only imbalance or closing auction volume.
