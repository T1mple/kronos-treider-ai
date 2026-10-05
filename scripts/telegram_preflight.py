import asyncio
import os
import sys

from aiogram import Bot


async def main() -> int:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    admin_ids = os.getenv("TELEGRAM_ADMIN_IDS", "").strip()

    if not token:
        print("FAIL: TELEGRAM_BOT_TOKEN is not configured")
        return 1
    if not admin_ids:
        print("FAIL: TELEGRAM_ADMIN_IDS is not configured")
        return 1

    bot = Bot(token)
    try:
        me = await bot.get_me()
        webhook = await bot.get_webhook_info()

        print(f"OK: Telegram bot @{me.username or '<no-username>'} id={me.id}")
        print(f"OK: admin IDs configured: {len([x for x in admin_ids.split(',') if x.strip().isdigit()])}")
        print(f"Telegram webhook: {webhook.url or '<none>'}")

        if webhook.url:
            print("FAIL: an outgoing webhook is configured; this project uses long polling")
            return 2

        print("OK: long polling is available")
        return 0
    finally:
        await bot.session.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
