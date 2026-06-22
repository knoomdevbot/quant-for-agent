def generate_signals(context):
    prices = context.prices.pivot(index="timestamp", columns="symbol", values="close").ffill()
    if len(prices) < 2:
        return {symbol: 0.0 for symbol in context.symbols}
    momentum = prices.iloc[-1] / prices.iloc[0] - 1.0
    positives = momentum[momentum > 0]
    if positives.empty:
        return {symbol: 0.0 for symbol in context.symbols}
    total = positives.sum()
    return {symbol: float(positives.get(symbol, 0.0) / total) for symbol in context.symbols}
