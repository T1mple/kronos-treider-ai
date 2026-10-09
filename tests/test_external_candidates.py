from datetime import datetime, timedelta, timezone

import pytest

from app.research.external_candidates import external_trend_score, external_trend_signal


def _candles(prices):
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return [
        {
            "timestamp": start + timedelta(hours=i),
            "open": price,
            "high": price * 1.01,
            "low": price * 0.99,
            "close": price,
            "volume": 1.0,
        }
        for i, price in enumerate(prices)
    ]


def test_external_trend_candidate_is_neutral_without_warmup():
    assert external_trend_score(_candles([100 + i for i in range(20)])) == 0.0
    assert external_trend_signal(_candles([100 + i for i in range(20)])) == "FLAT"


def test_external_trend_candidate_detects_sustained_uptrend():
    prices = [100.0 * (1.004 ** i) for i in range(100)]
    score = external_trend_score(_candles(prices))
    assert 0.25 <= score <= 1.0
    assert external_trend_signal(_candles(prices)) == "LONG"


def test_external_trend_candidate_rejects_invalid_parameters():
    with pytest.raises(ValueError):
        external_trend_score(_candles([100 + i for i in range(100)]), fast_period=60, slow_period=20)


def test_external_trend_candidate_score_is_bounded():
    prices = [100.0 * (1.003 ** i) for i in range(100)]
    assert -1.0 <= external_trend_score(_candles(prices)) <= 1.0
