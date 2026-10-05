import asyncio
import os
import sys

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from redis.asyncio import Redis


def result(name: str, ok: bool, detail: str) -> bool:
    print(f"[{'OK' if ok else 'FAIL'}] {name}: {detail}")
    return ok


async def check_telegram() -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return result("telegram", False, "TELEGRAM_BOT_TOKEN is missing")

    admin_ids = os.getenv("TELEGRAM_ADMIN_IDS", "").strip()
    if not admin_ids:
        return result("telegram", False, "TELEGRAM_ADMIN_IDS is missing")

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            me = (await client.get(f"https://api.telegram.org/bot{token}/getMe")).json()
            webhook = (await client.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")).json()
        except Exception as exc:
            return result("telegram", False, f"API connection failed: {exc}")

    if not me.get("ok"):
        return result("telegram", False, "getMe rejected the token")
    if not webhook.get("ok"):
        return result("telegram", False, "getWebhookInfo failed")

    username = me["result"].get("username") or "<no-username>"
    webhook_url = webhook["result"].get("url") or ""
    if webhook_url:
        return result("telegram", False, f"webhook configured: {webhook_url}")

    return result("telegram", True, f"@{username}, long polling available")


async def check_postgres() -> bool:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return result("postgres", False, "DATABASE_URL is missing")

    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return result("postgres", True, "connection and SELECT 1 succeeded")
    except Exception as exc:
        return result("postgres", False, str(exc))
    finally:
        await engine.dispose()


async def check_redis() -> bool:
    url = os.getenv("REDIS_URL", "").strip()
    if not url:
        return result("redis", False, "REDIS_URL is missing")

    redis = Redis.from_url(url)
    try:
        pong = await redis.ping()
        return result("redis", bool(pong), "PING/PONG succeeded" if pong else "PING failed")
    except Exception as exc:
        return result("redis", False, str(exc))
    finally:
        await redis.aclose()


async def main() -> int:
    checks = await asyncio.gather(check_telegram(), check_postgres(), check_redis())
    print(f"Runtime preflight: {'READY' if all(checks) else 'NOT READY'}")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
