from dataclasses import dataclass
from math import sqrt
from statistics import mean, pstdev


@dataclass(frozen=True)
class QuantSnapshot:
    alpha: float
    expected_return: float
    win_probability: float
    avg_win: float
    avg_loss: float
    volatility: float
    atr: float
    stop_distance: float
    position_usd: float
    action: str
    reason: str
    edge_samples: int
    direction_threshold: float


def _closes(candles):
    return [float(c.close if hasattr(c, "close") else c["close"]) for c in candles]


def _highs(candles):
    return [float(c.high if hasattr(c, "high") else c["high"]) for c in candles]


def _lows(candles):
    return [float(c.low if hasattr(c, "low") else c["low"]) for c in candles]


def _returns(closes):
    return [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes)) if closes[i - 1] > 0]


def _ema(values, period):
    if len(values) < period:
        return None
    value = mean(values[:period])
    alpha = 2.0 / (period + 1.0)
    for value_now in values[period:]:
        value = alpha * value_now + (1.0 - alpha) * value
    return value


def _clip(value, low=-1.0, high=1.0):
    return max(low, min(high, float(value)))


def _atr(candles, period=14):
    closes = _closes(candles)
    highs = _highs(candles)
    lows = _lows(candles)
    if len(closes) < period + 1:
        return None
    trs = []
    for i in range(1, len(closes)):
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
    return mean(trs[-period:])


def alpha_at(candles):
    closes = _closes(candles)
    if len(closes) < 40:
        return None
    rets = _returns(closes)
    vol = pstdev(rets[-20:]) if len(rets) >= 20 else 0.0
    vol = max(vol, 1e-9)

    momentum = _clip((closes[-1] / closes[-6] - 1.0) / (2.0 * vol))
    ema_fast = _ema(closes, 12)
    ema_slow = _ema(closes, 30)
    trend = _clip(((ema_fast / ema_slow) - 1.0) / (2.0 * vol)) if ema_fast and ema_slow else 0.0

    window = closes[-20:]
    z = (window[-1] - mean(window)) / max(pstdev(window), 1e-9)
    mean_reversion = _clip(-z / 2.0)

    # Volatility is a risk modifier, not a directional vote.
    volatility_score = _clip((vol - 0.005) / 0.01)

    # Kronos is deliberately injected separately by the caller.
    alpha = 0.40 * momentum + 0.35 * trend + 0.20 * mean_reversion - 0.05 * volatility_score
    return {
        "alpha": _clip(alpha),
        "momentum": momentum,
        "trend": trend,
        "mean_reversion": mean_reversion,
        "volatility": vol,
    }


def historical_edge(candles, min_samples=12):
    closes = _closes(candles)
    if len(closes) < 70:
        return {"samples": 0, "win_probability": 0.5, "avg_win": 0.0, "avg_loss": 0.0}

    outcomes = []
    # Strictly causal samples: alpha uses data through t, outcome is t+1.
    for end in range(40, len(closes) - 1):
        snap = alpha_at(candles[:end + 1])
        if not snap or abs(snap["alpha"]) < 0.15:
            continue
        future = closes[end + 1] / closes[end] - 1.0
        signed = future if snap["alpha"] > 0 else -future
        outcomes.append(signed)

    if len(outcomes) < min_samples:
        return {"samples": len(outcomes), "win_probability": 0.5, "avg_win": 0.0, "avg_loss": 0.0}

    wins = [x for x in outcomes if x > 0]
    losses = [-x for x in outcomes if x <= 0]
    return {
        "samples": len(outcomes),
        "win_probability": len(wins) / len(outcomes),
        "avg_win": mean(wins) if wins else 0.0,
        "avg_loss": mean(losses) if losses else 0.0,
    }


def evaluate_quant(candles, equity, max_position_usd=50.0, risk_fraction=0.005,
                   fee_rate=0.001, slippage_rate=0.0005, kronos_direction=0.0,
                   kronos_confidence=0.0):
    closes = _closes(candles)
    if len(closes) < 70:
        return None

    base = alpha_at(candles)
    edge = historical_edge(candles)
    atr = _atr(candles)
    price = closes[-1]
    if not base or not atr or atr <= 0:
        return None

    kronos_vote = _clip(kronos_direction) * _clip(kronos_confidence)
    alpha = _clip(0.85 * base["alpha"] + 0.15 * kronos_vote)

    # Expected value is net of one round-trip cost estimate.
    cost = 2.0 * (fee_rate + slippage_rate)
    expected_return = edge["win_probability"] * edge["avg_win"] - (1.0 - edge["win_probability"]) * edge["avg_loss"] - cost
    direction_threshold = 0.20
    direction_ok = abs(alpha) >= direction_threshold
    edge_ok = expected_return > 0.0
    action = "LONG" if alpha >= direction_threshold and edge_ok else "FLAT"
    if alpha <= -direction_threshold and edge_ok:
        action = "SHORT"

    stop_distance = max(2.0 * atr, price * 0.01)
    risk_budget = max(0.0, equity * risk_fraction)
    position_usd = min(max_position_usd, risk_budget * price / stop_distance) if stop_distance else 0.0
    if not direction_ok:
        reason = f"alpha_below_threshold:{alpha:+.3f}<{direction_threshold:.3f}"
    elif not edge_ok:
        reason = f"negative_expected_value:{expected_return:+.5f}"
    elif edge["samples"] < 12:
        reason = f"insufficient_edge_samples:{edge["samples"]}<12"
    else:
        reason = f"positive_expected_value:{expected_return:+.5f}:samples={edge["samples"]}"

    return QuantSnapshot(
        alpha=alpha,
        expected_return=expected_return,
        win_probability=edge["win_probability"],
        avg_win=edge["avg_win"],
        avg_loss=edge["avg_loss"],
        volatility=base["volatility"],
        atr=atr,
        stop_distance=stop_distance,
        position_usd=position_usd,
        action=action if edge["samples"] >= 12 else "FLAT",
        reason=reason,
        edge_samples=edge["samples"],
        direction_threshold=direction_threshold,
    )
