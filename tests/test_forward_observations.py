from app.paper.forward import ForwardPaperMonitor

def test_forward_accepts_only_new_candles():
    monitor=ForwardPaperMonitor()
    assert monitor.observe("BTCUSDT","2026-10-05T10:00:00+00:00",100,0.5,0.8,"BUY") is not None
    assert monitor.observe("BTCUSDT","2026-10-05T10:00:00+00:00",101,0.6,0.8,"BUY") is None
    assert monitor.states["BTCUSDT"].processed == 1
    assert monitor.states["BTCUSDT"].skipped == 1

def test_forward_snapshot_is_explicitly_paper_only():
    snapshot=ForwardPaperMonitor().snapshot()
    assert snapshot["mode"]=="FORWARD_PAPER"
    assert snapshot["live_trading"] is False
