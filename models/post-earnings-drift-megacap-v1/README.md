# post-earnings-drift-megacap-v1

AR-024 evaluates a divergent event-driven post-earnings information-diffusion hypothesis on Alpaca/qfa real market data only.

## Mechanism

qfa/Alpaca in this repository exposes OHLCV market bars but not a dependable earnings-calendar feed. This model does **not** fabricate earnings dates. Instead it uses a documented post-earnings-like event proxy:

- abnormal close-to-close information shock,
- abnormal volume,
- abnormal intraday range,
- close near the high for positive events or near the low for negative events,
- signal begins only after the event bar and decays over 8 trading days.

The trigger intentionally excludes overnight gap as a requirement and is therefore not an overnight-gap reversal refinement/direct inversion of AR-007.

## Evaluation

Durable evaluation artifacts are in `evaluations/latest.json`, `evaluations/latest.md`, and `evaluations/runs/`.

Constraints followed: Alpaca real market data via qfa, no `--data-csv`, no daemon, no trades. qfa metrics are pre-cost because the qfa CLI has no transaction cost/slippage option; costs/slippage handling is documented in the evaluation.
