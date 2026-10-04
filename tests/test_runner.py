import pytest
from datetime import datetime,timedelta
from app.research.runner import ResearchRunner

class FakeValidator:
    def run(self,candles,fn,train_size,test_size,step):
        return []

@pytest.mark.asyncio
async def test_runner_uses_public_data(monkeypatch):
    from app.research import runner
    from app.market_data import Candle
    candles=[Candle(datetime(2026,1,1)+timedelta(hours=i),100+i,101+i,99+i,100+i,1000) for i in range(20)]
    async def fake_fetch(*args,**kwargs): return candles
    monkeypatch.setattr(runner,"fetch_klines",fake_fetch)
    result=await ResearchRunner(FakeValidator()).run(limit=20,train_size=10,test_size=5,step=5)
    assert result.symbol=="BTCUSDT"
    assert result.candles==20
    assert "momentum" in result.strategies
