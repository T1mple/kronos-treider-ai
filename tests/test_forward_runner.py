import pytest

from app.paper.forward_runner import ForwardPaperRunner

@pytest.mark.asyncio
async def test_forward_runner_processes_one_cycle(monkeypatch):
    from app.paper import forward_runner as module

    class FakeCandle:
        close=100.0
        timestamp="2026-10-05T00:00:00+00:00"

    async def fake_fetch(*args, **kwargs):
        return [FakeCandle()]

    monkeypatch.setattr(module, "fetch_klines", fake_fetch)

    runner=ForwardPaperRunner(limit=1)
    monkeypatch.setattr(runner.system, "evaluate", lambda symbol, candles: {"mode":"RESEARCH_PAPER","symbol":symbol})
    result=await runner.run_once()

    assert result["symbol"]=="BTCUSDT"
    assert result["result"]["mode"]=="RESEARCH_PAPER"
    assert runner.snapshot()["live_trading"] is False if "live_trading" in runner.snapshot() else True
