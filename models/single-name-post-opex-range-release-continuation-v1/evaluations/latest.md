# AR-126 evaluation latest

Decision: **rejected**. Primary after-cost median random-window Sharpe is not positive enough and hard placebo/reversal ablations are not convincingly beaten.

Primary 5 bps after-cost Sharpe: -0.3944; annualized return: -0.0054; max drawdown: -0.0484; event count: 11; hit rate: 0.2727272727272727.

Random-window median Sharpe: -0.5647458779459439; p25: -0.573173166973487; worst: -1.3488638781175275; positive window rate: 0.13333333333333333.

Hard ablations (Sharpe): matched non-OPEX 0.07551891601564127, shifted 0.19844423409364756, generic range -0.03458348235050343, raw no residual 0.1385092510537922, reversed 0.2682935382230642.

Data/provenance: Alpaca real daily OHLCV via qfa gateway; no CSV, no --data-csv, no daemon, no orders; raw daily paths retained: false.
