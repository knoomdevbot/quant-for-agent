"""AR-144 exchange-netflow pressure scout placeholder.

This model intentionally emits no tradable signals until timestamp-safe,
point-in-time BTC/ETH exchange-flow data is available through qfa ingestion.
"""

MODEL_NAME = "crypto-btc-eth-exchange-netflow-pressure-scout-v1"
ASSET_BUCKET = "crypto"
CRYPTO_LABEL = True
DECISION = "hold"
HOLD_REASON = "No credential-free provider path was confirmed for point-in-time/revision-safe historical BTC/ETH exchange netflow evaluation."


def generate_signals(context):
    """Return no signals while the scout is on external-data hold.

    Parameters
    ----------
    context : object
        qfa evaluation context. It is not inspected because using OHLCV,
        fixture CSVs, or latest-revised on-chain data would violate AR-144.

    Returns
    -------
    dict
        Empty signal payload plus explicit hold metadata.
    """
    return {
        "signals": {},
        "model_name": MODEL_NAME,
        "decision": DECISION,
        "asset_bucket": ASSET_BUCKET,
        "crypto_label": CRYPTO_LABEL,
        "hold_reason": HOLD_REASON,
    }
