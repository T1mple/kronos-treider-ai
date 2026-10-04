from app.paper.forward import ForwardPaperMonitor

def test_adaptive_weights_require_minimum_sample():
    m=ForwardPaperMonitor()
    for i in range(4):
        m.observe("BTCUSDT",str(i),100+i,0.8,0.9,"BUY")
        m.observations[-1].strategy="momentum"
        m.observations[-1].regime="TREND"
        m.observations[-1].evaluated=True
        m.observations[-1].outcome_pct=1.0
    assert m.adaptive_weights("TREND", min_samples=5) == {}

def test_adaptive_weights_normalize():
    m=ForwardPaperMonitor()
    for i in range(5):
        m.observe("BTCUSDT",str(i),100+i,0.8,0.9,"BUY")
        m.observations[-1].strategy="momentum"
        m.observations[-1].regime="TREND"
        m.observations[-1].evaluated=True
        m.observations[-1].outcome_pct=1.0
    weights=m.adaptive_weights("TREND", min_samples=5)
    assert abs(sum(weights.values())-1.0) < 1e-9
    assert weights["momentum"] == 1.0
