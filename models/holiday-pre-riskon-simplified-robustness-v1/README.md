# holiday-pre-riskon-simplified-robustness-v1

AR-129 refinement of AR-127. The tradable hypothesis is deliberately narrow: long a fixed broad risk-on ETF basket on the last tradable NYSE session before predeclared full-day holidays, cash otherwise. The failed AR-127 post-holiday leg is excluded.

## Fixed universe and filters

Candidate pool: SPY, IVV, VOO, QQQ, IWM, MDY, DIA, VTI, EFA, IEFA, EEM, VEA, HYG, JNK, LQD, VCIT, VCSH, AGG.

Selected universe before performance review: SPY, QQQ, IWM, MDY, EFA, EEM, HYG, LQD, VCIT.

Filters: broad risk-on equity/credit exposure, Alpaca availability, common IEX daily coverage from 2020-07-27 after recent SIP-data 403, and median dollar-volume proxy above $1M. Limitations: current-symbol ETF set, shortened IEX history, survivorship/availability bias, and daily bars cannot prove intraday early-close execution quality.

## Evaluation summary

Real Alpaca daily OHLCV was used through configured paper-data credentials with values redacted. No CSV, no `--data-csv`, no qfa daemon, and no orders. Primary event return is close-to-close basket return ending on the holiday-eve trading session, net of 10 bps one-way entry and 10 bps one-way exit.

Latest result: **rejected**. Net 10 bps median event return was negative and hit rate was below threshold; placebo rank was weak. See `evaluations/latest.json` and `evaluations/latest.md` for metrics and robustness gates.
