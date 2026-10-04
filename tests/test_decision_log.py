from app.paper.decision_log import DecisionJournal

def test_decision_journal():
    journal=DecisionJournal()
    decision=type("D",(),{"adaptive":{"regime":"TRENDING","ensemble_score":0.5,"confidence":0.8},"allocation":{"approved":True,"notional_usd":10,"reason":"approved"}})()
    item=journal.record("BTCUSDT",decision,100)
    assert item.symbol=="BTCUSDT"
    assert journal.recent(1)[0]["approved"] is True
