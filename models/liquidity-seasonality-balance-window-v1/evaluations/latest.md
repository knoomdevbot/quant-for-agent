# AR-038 evaluation: liquidity-seasonality-balance-window-v1

## Result
- Suggested decision: **rejected**
- Rationale: Rejected by falsifier: median random-period costed Sharpe -0.36843186 and worst random drawdown -0.19281088.
- Data: Alpaca real daily OHLCV via qfa `AlpacaGateway`; `no_csv_used=true`; no daemon; no trades.
- Temporary qfa DB: `/tmp/qfa_ar038_20260626T091232Z.sqlite3` deleted after extracting run ids; `db_artifact_retained=false`.

## Universe and window
- Symbols: AAPL, MSFT, NVDA, AMZN, META, GOOGL, AVGO, JPM, LLY, XOM, UNH, COST
- Fetch range: 2019-01-01 to 2025-12-31; primary evaluation: 2024-01-01 to 2025-12-31; timeframe: 1Day
- Cost/slippage: 5 bps one-way turnover haircut applied ex-post as `sum(abs(w_t-w_(t-1)))*0.0005`.

## Key cost-adjusted metrics
| Window | Sharpe | Ann. return | Ann. vol | Max DD | Win rate | Active days | Avg turnover |
|---|---:|---:|---:|---:|---:|---:|---:|
| main 2024-01-01..2025-12-31 | 0.0873 | 0.0035 | 0.1112 | -0.1563 | 0.1080 | 96 | 0.1275 |
| win1 2020-06-01..2021-05-28 | -0.1553 | -0.0509 | 0.1997 | -0.1928 | 0.1200 | 52 | 0.1253 |
| win2 2021-03-01..2022-02-25 | -0.5816 | -0.0541 | 0.0889 | -0.1164 | 0.0960 | 52 | 0.1173 |
| win3 2021-11-01..2022-10-31 | -1.4164 | -0.1144 | 0.0833 | -0.1378 | 0.0760 | 42 | 0.1302 |
| win4 2022-06-01..2023-05-31 | 0.9031 | 0.1122 | 0.1264 | -0.0565 | 0.0843 | 42 | 0.1277 |
| win5 2023-01-03..2023-12-29 | 1.3342 | 0.1743 | 0.1263 | -0.0532 | 0.1008 | 48 | 0.1440 |
| win6 2024-06-03..2025-05-30 | -0.9827 | -0.1070 | 0.1090 | -0.1517 | 0.0931 | 43 | 0.1217 |


Random-window median Sharpe: **-0.3684**; worst random Sharpe: **-1.4164**; worst random drawdown: **-0.1928**.

## QFA run ids
The qfa backtester was run against the same Alpaca bars and saved into a temporary SQLite DB only:

```json
[
  {
    "label": "main",
    "run_id": 1,
    "start": "2024-01-01",
    "end": "2025-12-31",
    "uncosted_metrics": {
      "initial_cash": 100000.0,
      "final_equity": 97618.0454,
      "total_return": -0.02381955,
      "annualized_return": -0.01207682,
      "annualized_volatility": 0.09382975,
      "sharpe": -0.08219064,
      "max_drawdown": -0.14552013,
      "win_rate": 0.094,
      "periods": 500
    }
  },
  {
    "label": "win1",
    "run_id": 2,
    "start": "2020-06-01",
    "end": "2021-05-28",
    "uncosted_metrics": {
      "initial_cash": 100000.0,
      "final_equity": 87378.1235,
      "total_return": -0.12621877,
      "annualized_return": -0.12716142,
      "annualized_volatility": 0.18534754,
      "sharpe": -0.63416354,
      "max_drawdown": -0.1831835,
      "win_rate": 0.088,
      "periods": 250
    }
  },
  {
    "label": "win2",
    "run_id": 3,
    "start": "2021-03-01",
    "end": "2022-02-25",
    "uncosted_metrics": {
      "initial_cash": 100000.0,
      "final_equity": 97570.7086,
      "total_return": -0.02429291,
      "annualized_return": -0.02448486,
      "annualized_volatility": 0.08013593,
      "sharpe": -0.26922304,
      "max_drawdown": -0.10924951,
      "win_rate": 0.08,
      "periods": 250
    }
  },
  {
    "label": "win3",
    "run_id": 4,
    "start": "2021-11-01",
    "end": "2022-10-31",
    "uncosted_metrics": {
      "initial_cash": 100000.0,
      "final_equity": 95011.4696,
      "total_return": -0.0498853,
      "annualized_return": -0.05027418,
      "annualized_volatility": 0.06172671,
      "sharpe": -0.80466095,
      "max_drawdown": -0.09354084,
      "win_rate": 0.056,
      "periods": 250
    }
  },
  {
    "label": "win4",
    "run_id": 5,
    "start": "2022-06-01",
    "end": "2023-05-31",
    "uncosted_metrics": {
      "initial_cash": 100000.0,
      "final_equity": 113459.0442,
      "total_return": 0.13459044,
      "annualized_return": 0.13631786,
      "annualized_volatility": 0.12455844,
      "sharpe": 1.08649862,
      "max_drawdown": -0.04071693,
      "win_rate": 0.07228916,
      "periods": 249
    }
  },
  {
    "label": "win5",
    "run_id": 6,
    "start": "2023-01-03",
    "end": "2023-12-29",
    "uncosted_metrics": {
      "initial_cash": 100000.0,
      "final_equity": 98405.946,
      "total_return": -0.01594054,
      "annualized_return": -0.01619555,
      "annualized_volatility": 0.06442489,
      "sharpe": -0.22130565,
      "max_drawdown": -0.05049403,
      "win_rate": 0.06451613,
      "periods": 248
    }
  },
  {
    "label": "win6",
    "run_id": 7,
    "start": "2024-06-03",
    "end": "2025-05-30",
    "uncosted_metrics": {
      "initial_cash": 100000.0,
      "final_equity": 90071.8753,
      "total_return": -0.09928125,
      "annualized_return": -0.10118573,
      "annualized_volatility": 0.09631814,
      "sharpe": -1.05855312,
      "max_drawdown": -0.11540865,
      "win_rate": 0.05668016,
      "periods": 247
    }
  }
]
```

## Orthogonality/redundancy
not_high_by_design; quantitative library return correlation unavailable in retained artifacts. Parent AR-014 artifact status: rejected. AR-038 uses calendar liquidity/balance-sheet windows rather than event/earnings drift. Quantitative return-correlation checks against a retained alpha library were unavailable from durable artifacts.

## Artifacts
- `model.py`
- `config.yaml`
- `metadata.yaml`
- `README.md`
- `evaluations/latest.json`
- `evaluations/latest.md`
- `evaluations/runs/ar038_qfa_alpaca_real_20260626T091232Z.json`
