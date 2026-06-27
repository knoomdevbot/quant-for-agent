# Stale CSV / fixture evaluation results

The following previously existing AR-002 artifacts were encountered and are stale because they used local CSV fixture data instead of real Alpaca-backed ETF market data:

- `models/meanrev-zscore-liquid-etf-1d-v1/evaluations/runs/1.json`
- `models/meanrev-zscore-liquid-etf-1d-v1/evaluations/runs/qfa_run_1.json`
- prior contents of `models/meanrev-zscore-liquid-etf-1d-v1/evaluations/latest.json`
- prior contents of `models/meanrev-zscore-liquid-etf-1d-v1/evaluations/latest.md`

Do not use these CSV/fixture smoke results for model selection. The current real-data evaluation handles are:

- `models/meanrev-zscore-liquid-etf-1d-v1/evaluations/latest.json`
- `models/meanrev-zscore-liquid-etf-1d-v1/evaluations/latest.md`
- `models/meanrev-zscore-liquid-etf-1d-v1/evaluations/runs/qfa_realdata_20260626T054638Z.json`
- `models/meanrev-zscore-liquid-etf-1d-v1/evaluations/qfa_realdata.sqlite3`
