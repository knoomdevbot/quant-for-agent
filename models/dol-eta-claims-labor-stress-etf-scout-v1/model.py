"""DOL/ETA claims labor-stress ETF scout wrapper.

AR-151 completed only a bounded source-vintage feasibility gate.  No
performance-qualified allocator is enabled yet, so this wrapper intentionally
emits no exposure until a separate real-data evaluation promotes a non-zero
policy.
"""

MODEL_NAME = "dol-eta-claims-labor-stress-etf-scout-v1"
SOURCE_GATE_STATUS = "passed_feasibility_not_evaluated"
DEFAULT_UNIVERSE = (
    "SPY", "QQQ", "IWM", "XLK", "XLF", "XLU", "XLP",
    "TLT", "IEF", "SHY", "HYG", "LQD", "GLD",
)


def generate_signals(context):
    """Return zero ETF weights for the unevaluated source-gate scout.

    The source gate found plausible timestamp-safe official DOL/ETA release
    archives, but no claims parser or no-CSV ETF performance evaluation was run
    in this bounded recovery pass.  Returning explicit zero weights prevents
    accidental trading or backtest use as a live alpha.
    """
    return {symbol: 0.0 for symbol in DEFAULT_UNIVERSE}
