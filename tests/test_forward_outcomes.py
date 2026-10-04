from app.paper.forward import ForwardPaperMonitor

def test_forward_outcome_scoring():
    m=ForwardPaperMonitor()
    m.observe("BTCUSDT","1",100,0.8,0.9,"BUY")
    result=m.evaluate(102)
    assert result[0]["correct"] is True
    assert result[0]["outcome_pct"] == 2.0
    assert m.performance()["accuracy_pct"] == 100.0

def test_sell_outcome_scoring():
    m=ForwardPaperMonitor()
    m.observe("BTCUSDT","1",100,-0.8,0.9,"SELL")
    result=m.evaluate(98)
    assert result[0]["correct"] is True
