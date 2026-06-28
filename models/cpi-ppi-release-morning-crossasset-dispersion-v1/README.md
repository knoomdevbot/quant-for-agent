# AR-131 CPI/PPI release-morning cross-asset reaction dispersion

Predeclared primary: **fade** large cross-asset opening-gap dispersion on CPI/PPI release dates. At release-day close the signal uses only release-day open versus prior close and prior gap history; release-day close/high/low/volume are not signal inputs.

## Selected universe
TIP, SCHP, TLT, IEF, SHY, UUP, GLD, DBC, USO, XLE, XLRE, SPY, QQQ. All candidate ETFs passed Alpaca coverage/liquidity filters; no substitutes were needed.

## Latest real-data evaluation
- Data: qfa/Alpaca real daily OHLCV, 2018-01-01 to 2026-06-18; no CSV/`--data-csv`, no daemon, no orders.
- Primary 10 bps one-way: Sharpe -0.00406, ann return -0.000384, ann vol 0.024017, max DD -0.044644, activated events 81.
- Random/event windows: median Sharpe -0.019324, p25 -0.697588, worst -1.523809, positive-window rate 0.454545.
- Decision suggestion: **rejected**.

See `evaluations/latest.json` and immutable run `ar131_qfa_alpaca_real_20260628T004057Z.json` for ablations, orthogonality proxies, and limitations.
