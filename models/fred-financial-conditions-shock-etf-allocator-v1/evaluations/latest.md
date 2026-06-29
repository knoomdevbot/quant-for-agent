# AR-147 evaluation latest

Decision: **rejected**.

Primary 10 bps: Sharpe 0.72927206; total return 0.62387446; annualized return 0.05914958; annualized vol 0.08360936; max drawdown -0.19600201; annualized turnover 11.37911571; activation 0.5098777.

Cost sensitivity: 5 bps Sharpe 0.79834372; 20 bps Sharpe 0.59039067.

Random windows: count 12; median Sharpe 0.68214063; p25 0.02402053; worst -2.18022236; positive rate 0.75.

Controls: ETF TSMOM Sharpe 0.24051167 corr 0.44868989; price-only stress Sharpe -0.0601405 corr 0.55882736; shifted release labels Sharpe 0.0110116 corr 0.52605909; same-weekday placebo Sharpe 0.17436637 corr 0.27279414; inverted direction Sharpe -0.01937873 corr 0.24664604.

Warnings: latest FRED vintage, not point-in-time ALFRED; SHY dominates absolute weight; worst random window fails. qfa/Alpaca real daily bars only; no CSV/data-csv, no daemon, no orders, no raw daily arrays retained.
