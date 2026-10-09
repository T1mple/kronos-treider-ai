"""External research-inspired strategy candidates for offline evaluation only.

Research leads reviewed:
- https://github.com/PeterLP123/systematic-crypto-research
  Reports a volatility-normalized multi-asset trend-following candidate with a
  frozen post-selection evaluation; its results are research evidence, not a
  guarantee and are not copied as an exact reproduction.
- https://github.com/cbenitezpy/chocotrader-research
  Reports that simple retail-accessible spot strategies failed its pre-registered
  out-of-sample gate after realistic costs. This is a useful negative control.

This module implements a small, independently written trend-following candidate
inspired by the first project's research direction. It does not place orders.
"""
from math import sqrt
from statistics import mean, pstdev
from typing import Sequence


def _close(candle) -> float:
    return float(candle.close if hasattr(candle, "close") else candle["close"])


def _ema(values: Sequence[float], period: int) -> float | None:
    if period < 2 or len(values) < period:
        return None
    value = mean(values[:period])
    alpha = 2.0 / (period + 1.0)
    for current in values[period:]:
        value = alpha * current + (1.0 - alpha) * value
    return value


def external_trend_score(
    candles: Sequence,
    *,
    fast_period: int = 20,
    slow_period: int = 60,
    volatility_window: int = 20,
) -> float:
    """Return a volatility-normalized EMA trend score in [-1, 1].

    Uses only the candles supplied by the caller. In the backtester, the caller
    supplies candles through the current decision bar and fills at the next open.
    A score near zero means no clear trend; positive scores indicate an uptrend.
    """
    if fast_period < 2 or slow_period <= fast_period or volatility_window < 2:
        raise ValueError("require 2 <= fast_period < slow_period and volatility_window >= 2")
    closes = [_close(c) for c in candles]
    if len(closes) < max(slow_period, volatility_window + 1):
        return 0.0
    if any(price <= 0 for price in closes[-max(slow_period, volatility_window + 1):]):
        return 0.0

    fast = _ema(closes, fast_period)
    slow = _ema(closes, slow_period)
    if fast is None or slow is None or slow <= 0:
        return 0.0

    returns = [
        closes[i] / closes[i - 1] - 1.0
        for i in range(len(closes) - volatility_window, len(closes))
        if closes[i - 1] > 0
    ]
    volatility = pstdev(returns) if len(returns) > 1 else 0.0
    # Floor volatility to avoid unstable scores in nearly flat data.
    scale = max(volatility * sqrt(slow_period), 0.001)
    normalized_spread = (fast / slow - 1.0) / scale
    return max(-1.0, min(1.0, normalized_spread))


def external_trend_signal(candles: Sequence) -> str:
    """Long/flat wrapper compatible with Kronos' OHLC backtester."""
    return "LONG" if external_trend_score(candles) >= 0.25 else "FLAT"
