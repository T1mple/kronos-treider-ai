from dataclasses import dataclass
from math import log
from statistics import mean, pstdev


@dataclass(frozen=True)
class StrategySignal:
    strategy: str
    symbol: str
    action: str
    score: float
    expected_return: float
    reason: str


def _closes(candles):
    return [float(c.close if hasattr(c, "close") else c["close"]) for c in candles]


def _returns(closes):
    return [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes)) if closes[i - 1] > 0]


def _clip(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, float(x)))


def _zscore(values):
    if len(values) < 2:
        return 0.0
    sd = pstdev(values)
    return 0.0 if sd <= 1e-12 else (values[-1] - mean(values)) / sd


def _ema(values, period):
    if len(values) < period:
        return None
    value = mean(values[:period])
    alpha = 2.0 / (period + 1.0)
    for current in values[period:]:
        value = alpha * current + (1.0 - alpha) * value
    return value


def directional_suite(candles, symbol):
    closes = _closes(candles)
    if len(closes) < 60:
        return []
    rets = _returns(closes)
    vol = max(pstdev(rets[-20:]), 1e-9)
    momentum = _clip((closes[-1] / closes[-6] - 1.0) / (2.0 * vol))
    fast = _ema(closes, 12)
    slow = _ema(closes, 30)
    trend = _clip(((fast / slow) - 1.0) / (2.0 * vol)) if fast and slow else 0.0
    z = _zscore(closes[-20:])
    mean_rev = _clip(-z / 2.0)

    return [
        StrategySignal("momentum", symbol, "LONG" if momentum > .25 else "SHORT" if momentum < -.25 else "FLAT",
                       momentum, abs(momentum) * vol, "20-period volatility-normalized momentum"),
        StrategySignal("trend", symbol, "LONG" if trend > .25 else "SHORT" if trend < -.25 else "FLAT",
                       trend, abs(trend) * vol, "EMA12/EMA30 spread normalized by volatility"),
        StrategySignal("mean_reversion", symbol, "LONG" if mean_rev > .25 else "SHORT" if mean_rev < -.25 else "FLAT",
                       mean_rev, abs(mean_rev) * vol, "20-period price z-score reversion"),
    ]


def market_making(candles, symbol):
    closes = _closes(candles)
    if len(closes) < 30:
        return None
    rets = _returns(closes)
    vol = pstdev(rets[-20:])
    # This is a quote-readiness score only. It never submits an order.
    score = _clip((0.003 - vol) / 0.003)
    action = "QUOTE" if score > 0.0 else "OFF"
    return StrategySignal("market_making", symbol, action, score, 0.0,
                          "quote readiness from realized volatility; order-book data required for execution")


def grid(candles, symbol):
    closes = _closes(candles)
    if len(closes) < 30:
        return None
    z = _zscore(closes[-20:])
    width = max(pstdev(closes[-20:]) / max(closes[-1], 1e-9), 1e-6)
    score = _clip(0.5 - abs(z) / 4.0)
    action = "GRID_READY" if score > 0.1 and width < 0.025 else "OFF"
    return StrategySignal("grid", symbol, action, score, width, "range-regime readiness; grid spacing is volatility-adjusted")


def statistical_pair(candles_a, candles_b, symbol_a, symbol_b):
    a, b = _closes(candles_a), _closes(candles_b)
    n = min(len(a), len(b), 60)
    if n < 30:
        return None
    spread = [log(max(a[i], 1e-12)) - log(max(b[i], 1e-12)) for i in range(-n, 0)]
    z = _zscore(spread)
    score = _clip(-z / 2.0)
    action = "LONG_SPREAD" if score > .5 else "SHORT_SPREAD" if score < -.5 else "FLAT"
    return StrategySignal("stat_arb", f"{symbol_a}/{symbol_b}", action, score, abs(score) * 0.001,
                          "log-price spread z-score; pair is a research candidate, not an execution signal")


def aggregate(signals):
    usable = [s for s in signals if s and s.action not in {"OFF", "FLAT"}]
    if not usable:
        return {"active": 0, "best": None, "strategies": signals}
    best = max(usable, key=lambda s: abs(s.score))
    return {"active": len(usable), "best": best, "strategies": signals}


__all__ = [
    "StrategySignal",
    "directional_suite",
    "market_making",
    "grid",
    "statistical_pair",
    "aggregate",
]
