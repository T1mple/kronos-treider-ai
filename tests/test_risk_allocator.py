from app.research.risk_allocator import ResearchRiskAllocator

def test_allocator_rejects_daily_loss():
    d=ResearchRiskAllocator().allocate(1.0,1.0,0.01,300,daily_pnl=-10)
    assert not d.approved

def test_allocator_scales_by_confidence():
    d=ResearchRiskAllocator().allocate(0.8,0.9,0.005,300)
    assert d.approved
    assert 0 < d.notional_usd <= 50
