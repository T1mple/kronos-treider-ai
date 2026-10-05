import pytest

from app.research.quant_engine import alpha_at, evaluate_quant, historical_edge


def _candles(prices):
    return [
        {"open": p, "high": p * 1.002, "low": p * 0.998, "close": p, "volume": 1.0}
        for p in prices
    ]


def test_alpha_is_directional_for_trend():
    prices = [100 + i * 0.5 for i in range(90)]
    snap = alpha_at(_candles(prices))
    assert snap is not None
    assert snap["alpha"] > 0


def test_historical_edge_is_causal():
    prices = [100 + i * 0.2 for i in range(90)]
    edge = historical_edge(_candles(prices))
    assert edge["samples"] > 0
    assert edge["win_probability"] == 1.0


def test_quant_engine_returns_risk_bounded_position():
    prices = [100 + i * 0.2 for i in range(90)]
    result = evaluate_quant(_candles(prices), equity=300.0, max_position_usd=50.0)
    assert result is not None
    assert 0.0 <= result.position_usd <= 50.0
    assert result.stop_distance > 0
