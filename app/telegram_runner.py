import asyncio
import logging
from app.config import settings
from app.telegram_bot import TelegramDashboard, authorized

logger=logging.getLogger(__name__)


def format_dict(title, data):
    lines=[f"<b>{title}</b>"]
    for key,value in data.items():
        lines.append(f"<b>{key}</b>: {value}")
    return "\n".join(lines)


def build_application():
    """Create the aiogram application when Telegram dependencies/config are available."""
    from aiogram import Bot, Dispatcher
    from aiogram.filters import Command
    from aiogram.types import Message

    bot=Bot(settings.telegram_bot_token)
    dp=Dispatcher()
    dashboard=TelegramDashboard()

    async def guard(message: Message):
        return bool(message.from_user and authorized(message.from_user.id))

    @dp.message(Command("status"))
    async def status(message: Message):
        if not await guard(message): return
        await message.answer(format_dict("Kronos Trader AI",dashboard.status()),parse_mode="HTML")

    @dp.message(Command("balance"))
    async def balance(message: Message):
        if not await guard(message): return
        await message.answer(format_dict("Balance",dashboard.balance()),parse_mode="HTML")

    @dp.message(Command("positions"))
    async def positions(message: Message):
        if not await guard(message): return
        await message.answer(str(dashboard.positions()))

    @dp.message(Command("trades"))
    async def trades(message: Message):
        if not await guard(message): return
        await message.answer(str(dashboard.trades()))

    @dp.message(Command("pause"))
    async def pause(message: Message):
        if not await guard(message): return
        await message.answer("⏸ Paper engine paused")
        dashboard.pause()

    @dp.message(Command("resume"))
    async def resume(message: Message):
        if not await guard(message): return
        dashboard.resume()
        await message.answer("▶️ Paper engine resumed")

    @dp.message(Command("emergency"))
    async def emergency(message: Message):
        if not await guard(message): return
        dashboard.emergency()
        await message.answer("🚨 Emergency stop active. Live trading remains disabled.")

    @dp.message(Command("kronos"))
    async def kronos(message: Message):
        if not await guard(message): return
        result=await dashboard.kronos()
        await message.answer(format_dict("Kronos forecast",result),parse_mode="HTML")

    @dp.message(Command("signals"))
    async def signals(message: Message):
        if not await guard(message): return
        result=await dashboard.signals()
        await message.answer(str(result))

    return bot,dp


async def run():
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    bot,dp=build_application()
    await dp.start_polling(bot)


if __name__=="__main__":
    asyncio.run(run())
