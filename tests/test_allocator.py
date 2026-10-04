from app.allocator import CapitalAllocator

def test_allocator_respects_limits():
    a=CapitalAllocator(200,50)
    assert a.allocate(1,1000,0) <= 50
    assert a.allocate(1,1000,180) <= 20
