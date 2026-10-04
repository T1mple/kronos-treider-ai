import asyncio
import logging
from app.config import settings
from app.paper.autotest import PaperAutoTester
from app.telegram_bot import TelegramDashboard, authorized

logger = logging.getLogger(__name__)

def format_dict(title, data):
    lines = [f"<b>{title}</b>"]
    for key, value in data.items():
        if isinstance(value, float):
            value = f"{value:.4f}"
        lines.append(f"<b>{key}</b>: {value}")
    return "\n".join(lines)

def build_application():
    from aiogram import Bot, Dispatcher
    from aiogram.filters import Command
    from aiogram.types import Message
    bot = Bot(settings.telegram_bot_token)
    dp = Dispatcher()
    dashboard = TelegramDashboard()
    tester = PaperAutoTester()
    test_task = None

    async def guard(message):
        return bool(message.from_user and authorized(message.from_user.id))

    def result_text(result):
        return ("<b>🧪 KRONOS TRADER AI • PAPER TEST</b>\n"
                f"Symbol: <b>{result.symbol}</b>\n"
                f"Interval: <b>{result.interval}</b>\n"
                f"Candles: <b>{result.candles}</b>\n"
                f"Return: <b>{result.return_pct:+.2f}%</b>\n"
                f"Max DD: <b>{result.max_drawdown_pct:.2f}%</b>\n"
                f"Trades: <b>{result.trades}</b>\n"
                f"Fees: <b>${result.fees:.2f}</b>\n\n"
                f"Kronos direction: <b>{result.kronos_direction:+.3f}</b>\n"
                f"Kronos confidence: <b>{result.kronos_confidence:.1%}</b>\n"
                f"Updated: <b>{result.updated_at}</b>")

    @dp.startup()
    async def startup():
        nonlocal test_task
        test_task = asyncio.create_task(tester.loop(900))

    @dp.shutdown()
    async def shutdown():
        tester.stop()
        if test_task:
            test_task.cancel()
            try:
                await test_task
            except asyncio.CancelledError:
                pass

    @dp.message(Command("status"))
    async def status(message: Message):
        if await guard(message):
            await message.answer(format_dict("Kronos Trader AI", dashboard.status()), parse_mode="HTML")

    @dp.message(Command("balance"))
    async def balance(message: Message):
        if await guard(message):
            await message.answer(format_dict("Balance", dashboard.balance()), parse_mode="HTML")

    @dp.message(Command("positions"))
    async def positions(message: Message):
        if await guard(message): await message.answer(str(dashboard.positions()))

    @dp.message(Command("trades"))
    async def trades(message: Message):
        if await guard(message): await message.answer(str(dashboard.trades()))

    @dp.message(Command("test"))
    async def test(message: Message):
        if not await guard(message): return
        try:
            result = await tester.run_once()
            await message.answer(result_text(result), parse_mode="HTML")
        except Exception as exc:
            await message.answer(f"❌ Paper test error: {exc}")

    @dp.message(Command("performance"))
    async def performance(message: Message):
        if not await guard(message): return
        if tester.latest:
            await message.answer(result_text(tester.latest), parse_mode="HTML")
        else:
            await message.answer("⏳ Первый тест ещё выполняется.")

    @dp.message(Command("pause"))
    async def pause(message: Message):
        if await guard(message):
            dashboard.pause(); await message.answer("⏸ Paper interface paused. Live trading remains disabled.")

    @dp.message(Command("resume"))
    async def resume(message: Message):
        if await guard(message):
            dashboard.resume(); await message.answer("▶️ Paper interface resumed.")

    @dp.message(Command("emergency"))
    async def emergency(message: Message):
        if await guard(message):
            dashboard.emergency(); await message.answer("🚨 Emergency stop active. Live trading remains disabled.")

    @dp.message(Command("kronos"))
    async def kronos(message: Message):
        if await guard(message):
            await message.answer(format_dict("Kronos forecast", await dashboard.kronos()), parse_mode="HTML")

    @dp.message(Command("signals"))
    async def signals(message: Message):
        if await guard(message): await message.answer(str(await dashboard.signals()))

    return bot, dp

async def run():
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    bot, dp = build_application()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run())
