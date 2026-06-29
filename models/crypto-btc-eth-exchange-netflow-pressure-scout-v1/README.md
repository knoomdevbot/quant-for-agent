# AR-144 — BTC/ETH exchange-netflow pressure scout

- **Model name:** `crypto-btc-eth-exchange-netflow-pressure-scout-v1`
- **Asset bucket:** crypto
- **Crypto label:** true
- **Decision/status:** hold

## Hypothesis
Large exchange inflows may forecast sell pressure, while large outflows may indicate reduced liquid float/accumulation. The idea remains economically valid only if exchange labels, provider publication time, and revisions are timestamp-safe.

## Feasibility result
The scout did **not** run a performance backtest. This checkout has qfa support for crypto OHLCV via Alpaca, but no native on-chain exchange-flow adapter was found, and this environment exposed no Glassnode/CryptoQuant/Coin Metrics/Nansen credentials or installed provider SDKs. AR-144 forbids OHLCV flow proxies and CSV fixtures, so performance is intentionally unavailable.

## Data-source/provenance checks
- Searched qfa source for on-chain/exchange-flow provider support: none found beyond Alpaca crypto bars.
- Checked environment variable names for Glassnode, CryptoQuant, Coin Metrics, Nansen and equivalents: none found.
- Checked installed provider SDK availability: `glassnode`, `coinmetrics`, and `nansen` not installed.
- No raw market bars, daily arrays, CSVs, SQLite caches, or provider payloads retained.

## Candidate pool and universe
- Candidate pool: BTC and ETH spot/perpetuals first.
- Selected universe for future feasible test: BTC/USD and ETH/USD equivalents only until coverage/liquidity gates pass.
- Expansion to other majors is blocked until BTC/ETH provider coverage and timestamp discipline pass.

## Costs/slippage assumptions
- Spot: 10 bps maker, 20 bps taker; stress at 1x/2x/3x fees/slippage.
- Perpetuals: 2 bps maker, 5 bps taker; funding must be included once perps are evaluated.

## Planned evaluation if unblocked
- Features: exchange inflow, outflow, netflow, balance change; z-scores over 7/14/30/60-day lookbacks.
- Timestamp discipline: conservative 1/2/3-day publication lags; flat when metrics are missing or late.
- Random/regime protocol: daily/weekly random windows across bull, bear, chop, high-vol and low-vol regimes.
- Metrics: Sharpe, annualized return/vol, max drawdown, hit rate, turnover, positive-window rate, BTC/ETH leg diagnostics.
- Controls/ablations: BTC/ETH 1/7/30-day momentum, reversal, realized volatility, drawdown, stablecoin liquidity, macro/risk beta, shifted labels, inverted flow direction.

## Hold/unblock condition
Unblock only when reproducible real-provider API access is available with documented publication lag/revision policy for BTC/ETH exchange inflow/outflow/netflow and a non-CSV ingestion path suitable for qfa research.
