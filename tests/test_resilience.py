import asyncio
from app.ops.resilience import retry_async, RetryPolicy

def test_retry_async():
    state={"n":0}
    async def fn():
        state["n"]+=1
        if state["n"]<2: raise RuntimeError("temporary")
        return 7
    assert asyncio.run(retry_async(fn,RetryPolicy(attempts=2,base_delay=0)))==7
