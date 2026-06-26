# closing-volume-reversal-costaware-megacap-v1

Research artifact for **AR-045**, a refinement of AR-028's abnormal close-location/volume reversal on liquid mega-cap equities.

The qfa-compatible `model.py` keeps the daily OHLCV proxy for closing-auction-like pressure but adds cost-aware filters: stricter close-location/volume gates, minimum expected edge, weak sign-flip damping, persistence blending, an equal-weight market-volatility gate, and inverse-realized-volatility cross-sectional sizing.

## Files

- `model.py` — qfa `generate_signals(context)` implementation; research-only and never places orders.
- `config.yaml` — parameters and evaluation controls.
- `metadata.yaml` — issue/model metadata.
- `evaluations/latest.json` / `latest.md` — latest evaluation artifacts after the Alpaca/qfa run.
- `evaluations/runs/` — immutable qfa and summary JSON artifacts.

## Data / safety constraints

Evaluation uses Alpaca real daily OHLCV through qfa only. CSV fixtures and `--data-csv` are not used. Alpaca credentials must be sourced externally from `/Users/moonk/.hermes/profiles/alphaaoi/secrets/alpaca.env` with `ALPACA_KEY_ID` mapped to `ALPACA_API_KEY`; secrets are not stored or printed. Runs use a temporary SQLite DB in `/tmp`, no daemon, and no trades.

## Important limitation

Alpaca/qfa daily bars do not expose closing-auction imbalance or auction-only volume. The model is a next close-to-close proxy using close location within the daily high-low range and abnormal share/dollar volume.
