import pytest
from datetime import datetime, timezone, timedelta

from app.paper.forward_runner import ForwardPaperRunner


@pytest.mark.asyncio
async def test_forward_runner_processes_one_closed_cycle(monkeypatch, tmp_path):
    from app.paper import forward_runner as module

    class FakeCandle:
        close = 100.0
        timestamp = datetime(2026, 10, 5, 0, 0, tzinfo=timezone.utc)

    async def fake_fetch(*args, **kwargs):
        return [FakeCandle()]

    monkeypatch.setattr(module, "fetch_klines", fake_fetch)

    runner = ForwardPaperRunner(limit=1, state_path=str(tmp_path / "forward.json"))
    monkeypatch.setattr(
        runner.system,
        "evaluate",
        lambda symbol, candles: {"mode": "RESEARCH_PAPER", "symbol": symbol},
    )
    result = await runner.run_once()

    assert result["symbol"] == "BTCUSDT"
    assert result["result"]["mode"] == "RESEARCH_PAPER"
    assert result["status"] == "PROCESSED"
    assert result["candle_timestamp"] == "2026-10-05T00:00:00+00:00"


@pytest.mark.asyncio
async def test_forward_runner_does_not_reprocess_same_closed_candle(monkeypatch, tmp_path):
    from app.paper import forward_runner as module

    class FakeCandle:
        close = 100.0
        timestamp = datetime.now(timezone.utc) - timedelta(hours=2)

    async def fake_fetch(*args, **kwargs):
        return [FakeCandle()]

    monkeypatch.setattr(module, "fetch_klines", fake_fetch)

    runner = ForwardPaperRunner(limit=1, state_path=str(tmp_path / "forward.json"))
    calls = 0

    def evaluate(symbol, candles):
        nonlocal calls
        calls += 1
        return {"mode": "RESEARCH_PAPER", "symbol": symbol}

    monkeypatch.setattr(runner.system, "evaluate", evaluate)

    first = await runner.run_once()
    second = await runner.run_once()

    assert first["status"] == "PROCESSED"
    assert second["status"] == "NO_NEW_CLOSED_CANDLE"
    assert calls == 1


@pytest.mark.asyncio
async def test_forward_runner_ignores_open_candle(monkeypatch, tmp_path):
    from app.paper import forward_runner as module

    class FakeCandle:
        close = 100.0
        timestamp = datetime.now(timezone.utc) - timedelta(minutes=10)

    async def fake_fetch(*args, **kwargs):
        return [FakeCandle()]

    monkeypatch.setattr(module, "fetch_klines", fake_fetch)

    runner = ForwardPaperRunner(limit=1, state_path=str(tmp_path / "forward.json"))
    result = await runner.run_once()

    assert result["status"] == "WAITING_FOR_CLOSED_CANDLE"
    assert result["live_trading"] is False
