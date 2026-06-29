"""AR-144 hold stub: BTC/ETH exchange-netflow pressure scout.

The alpha hypothesis requires timestamp-safe exchange inflow/outflow/netflow
metrics from an on-chain provider. No provider credentials/API client or qfa
on-chain data adapter were available in this checkout, so this model is a safe
placeholder that emits no positions until the data gate is satisfied.
"""

from __future__ import annotations

from typing import Any

MODEL_NAME = "crypto-btc-eth-exchange-netflow-pressure-scout-v1"
ASSET_BUCKET = "crypto"
CRYPTO_LABEL = True
STATUS = "hold"


def generate_signals(context: Any) -> dict[str, float]:
    """Return no target weights while timestamp-safe netflow data is unavailable.

    Required unblock condition: a real on-chain provider feed (Glassnode,
    CryptoQuant, Coin Metrics, Nansen, or equivalent) must provide BTC/ETH
    exchange inflow/outflow/netflow with documented publication lag/revision
    policy and reproducible API access. Price-only/OHLCV proxies are not used.
    """

    _ = context
    return {}
