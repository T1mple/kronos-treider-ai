from datetime import datetime,timedelta
from app.market_data import Candle
from app.research.walk_forward import WalkForwardValidator

def test_walk_forward_produces_out_of_sample_windows():
    candles=[]
    for i in range(20):
        p=100+i
        candles.append(Candle(datetime(2026,1,1)+timedelta(days=i),p,p+1,p-1,p,1000))
    results=WalkForwardValidator().run(candles,lambda c:1.0,train_size=10,test_size=5,step=5)
    assert len(results)==1
    assert results[0].test_start==10
