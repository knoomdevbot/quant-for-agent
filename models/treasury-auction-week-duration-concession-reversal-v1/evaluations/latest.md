# AR-108 evaluation: Treasury auction-week duration concession reversal

**Decision:** rejected  
**Reason:** 10bps random-window median Sharpe <= 0; materially negative p25 Sharpe

## Primary 10 bps metrics
- Full-period Sharpe: -0.02971008
- Annualized return: -0.00073946
- Annualized volatility: 0.02488904
- Max drawdown: -0.0462691
- Activation fraction: 0.03501684
- Random-window median / p25 / worst Sharpe: -0.05507141 / -0.69603262 / -2.01593168
- Positive random-window rate: 0.5

## Data and constraints
Real Alpaca daily bars via qfa AlpacaGateway (iex); no CSV, no `--data-csv`, no daemon, no orders. Raw bars were not retained.

## Universe
Candidate and selected symbols fixed ex ante: TLT, IEF, SHY, TIP, LQD, HYG, SPY, GLD, UUP. Selection was based on data coverage and economic exposure only.

## Orthogonality
Max absolute ETF proxy correlation: 0.03002164. Watchlist return-stream correlations were unavailable in compact prior artifacts, so proxy correlations were used.

Immutable run JSON: `/Users/moonk/quant-for-agent/models/treasury-auction-week-duration-concession-reversal-v1/evaluations/runs/ar108_qfa_alpaca_real_20260626T183213Z.json`
