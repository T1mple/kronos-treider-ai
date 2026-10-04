import asyncio
from dataclasses import dataclass

@dataclass
class RetryPolicy:
    attempts:int=3
    base_delay:float=.5
    max_delay:float=5.0

async def retry_async(fn, policy=None):
    policy=policy or RetryPolicy()
    last=None
    for attempt in range(policy.attempts):
        try: return await fn()
        except Exception as exc:
            last=exc
            if attempt+1<policy.attempts:
                await asyncio.sleep(min(policy.max_delay,policy.base_delay*(2**attempt)))
    raise last
