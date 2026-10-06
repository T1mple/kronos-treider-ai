from app.portfolio.allocator import PortfolioAllocator
def test_allocator_total_capital():
    rows=PortfolioAllocator(300).allocate([{"name":"A","score":2},{"name":"B","score":1}])
    assert abs(sum(x.notional_usd for x in rows)-100)<1e-6
    assert all(x.notional_usd <= 50.0 for x in rows)
