from app.paper.forward import ForwardPaperMonitor

def test_forward_processes_once():
    m=ForwardPaperMonitor()
    assert m.accept("BTCUSDT","2026-01-01T00:00:00Z")
    assert not m.accept("BTCUSDT","2026-01-01T00:00:00Z")
    assert m.snapshot()["BTCUSDT"]["processed"]==1
