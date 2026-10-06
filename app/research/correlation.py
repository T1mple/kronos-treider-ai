from math import sqrt

def returns(closes):
    return [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes)) if closes[i - 1] > 0]

def correlation(a, b):
    n = min(len(a), len(b))
    a, b = returns(list(a)[-n:]), returns(list(b)[-n:])
    n = min(len(a), len(b))
    if n < 2:
        return 0.0
    a, b = a[-n:], b[-n:]
    ma, mb = sum(a) / n, sum(b) / n
    da, db = [x - ma for x in a], [x - mb for x in b]
    den = sqrt(sum(x * x for x in da) * sum(x * x for x in db))
    if den > 1e-12:
        return sum(x * y for x, y in zip(da, db)) / den
    if max(abs(x) for x in da) <= 1e-12 and max(abs(x) for x in db) <= 1e-12:
        if abs(ma) <= 1e-12 or abs(mb) <= 1e-12:
            return 0.0
        return 1.0 if ma * mb > 0 else -1.0
    return 0.0

def strategy_correlation(results):
    """Pearson matrix from strategy equity curves."""
    names = list(results)
    return {
        a: {b: (1.0 if a == b else correlation(results[a].equity_curve, results[b].equity_curve))
            for b in names}
        for a in names
    }

def diversification_penalty(strategy, selected, matrix):
    if not selected:
        return 0.0
    return sum(abs(float(matrix.get(strategy, {}).get(other, 0.0))) for other in selected) / len(selected)

def concentration(exposures):
    total = sum(max(0.0, float(x)) for x in exposures.values())
    if total <= 0:
        return 0.0
    return sum((float(x) / total) ** 2 for x in exposures.values())
