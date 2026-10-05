import asyncio
import logging
from app.config import settings
from app.paper.autonomous import AutonomousPaperEngine, PaperDecision
from app.telegram_bot import authorized


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

BOT_COMMANDS = [
    ("start", "Запустить робота 24/7"),
    ("status", "Состояние робота"),
    ("pause", "Поставить робота на паузу"),
    ("report", "Последний отчёт"),
    ("emergency", "Аварийная остановка"),
]


def format_dict(title, data):
    lines = [f"<b>{title}</b>"]
    for key, value in data.items():
        if isinstance(value, float):
            value = f"{value:.4f}"
        lines.append(f"<b>{key}</b>: {value}")
    return "\n".join(lines)


def format_report(report):
    return (
        "<b>📈 KRONOS PAPER REPORT</b>\n\n"
        f"Equity: <b>USD {report['equity']:.2f}</b>\n"
        f"Total PnL: <b>USD {report['total_pnl']:+.2f}</b>\n"
        f"Realized PnL: <b>USD {report['realized_pnl']:+.2f}</b>\n"
        f"Closed trades: <b>{report['closed_trades']}</b>\n"
        f"Wins / losses: <b>{report['winning_trades']} / {report['losing_trades']}</b>\n"
        f"Win rate: <b>{report['win_rate']:.1%}</b>\n"
        f"Max drawdown: <b>{report['max_drawdown']:.1%}</b>\n"
        f"Equity snapshots: <b>{report['snapshots']}</b>\n\n"
        "Mode: <b>PAPER SIMULATION</b>\n"
        "Real orders: <b>OFF</b>"
    )


def build_application():
    from aiogram import Bot, Dispatcher
    from aiogram.types import BotCommand
    from aiogram.filters import Command, CommandStart
    from aiogram.types import Message, BotCommandScopeDefault

    bot = Bot(settings.telegram_bot_token)
    dp = Dispatcher()
    autonomous = AutonomousPaperEngine()
    autonomous_task = None

    async def notify_paper_event(event: PaperDecision):
        if not _admin_ids():
            logger.warning("No Telegram admin IDs configured; paper event was not sent")
            return
        icon = "🟢" if event.action == "BUY" else "🔴" if event.action == "SELL" else "⚠️"
        await bot.send_message(
            chat_id=_admin_ids()[0],
            text=(
                f"<b>{icon} KRONOS PAPER {event.action}</b>\n\n"
                f"Symbol: <b>{event.symbol}</b>\n"
                f"Price: <b>${event.price:,.2f}</b>\n"
                f"Quantity: <b>{event.quantity:.8f}</b>\n"
                f"Signal: <b>{event.signal:+.3f}</b>\n"
                f"Kronos confidence: <b>{event.kronos_confidence:.1%}</b>\n"
                f"Reason: <b>{event.reason}</b>\n\n"
                "Mode: <b>PAPER SIMULATION</b>\n"
                "Real orders: <b>OFF</b>"
            ),
            parse_mode="HTML",
        )

    def _admin_ids():
        return [int(x.strip()) for x in settings.telegram_admin_ids.split(",") if x.strip().isdigit()]

    async def guard(message):
        return bool(message.from_user and authorized(message.from_user.id))


    @dp.startup()
    async def startup():
        nonlocal autonomous_task
        try:
            me = await bot.get_me()
            logger.info("Telegram connected as @%s (id=%s)", me.username, me.id)
        except Exception:
            logger.exception("Telegram API connection failed during startup")
            raise

        admin_ids = _admin_ids()
        if not admin_ids:
            logger.warning("TELEGRAM_ADMIN_IDS is empty; bot will answer no authorized users")
        else:
            logger.info("Telegram admin IDs configured: %s", admin_ids)

        await bot.set_my_commands(
            [BotCommand(command=command, description=description) for command, description in BOT_COMMANDS],
            scope=BotCommandScopeDefault(),
        )
        logger.info("Telegram bot started; commands registered")

    @dp.shutdown()
    async def shutdown():
        autonomous.stop()
        if autonomous_task:
            autonomous_task.cancel()
            try:
                await autonomous_task
            except asyncio.CancelledError:
                pass
        await bot.session.close()

    @dp.message(CommandStart())
    async def start(message: Message):
        nonlocal autonomous_task
        if not await guard(message):
            await message.answer("Доступ запрещён.")
            return
        if autonomous_task and not autonomous_task.done():
            await message.answer("ℹ️ KRONOS уже запущен.", parse_mode="HTML")
            return
        autonomous.start()
        await autonomous.initialize()
        autonomous_task = asyncio.create_task(autonomous.loop(900, on_event=notify_paper_event))
        await message.answer(
            "🚀 <b>KRONOS ЗАПУЩЕН</b>\n\n"
            "Робот работает 24/7 в PAPER-режиме.\n"
            "Я буду присылать важные события и отчёты автоматически.\n"
            "Реальные ордера: <b>OFF</b>.",
            parse_mode="HTML",
        )

    @dp.message(Command("status"))
    async def status(message: Message):
        if not await guard(message):
            return
        snap = autonomous.snapshot()
        state = snap["risk"]
        await message.answer(
            format_dict("📊 KRONOS STATUS", {
                "service": "RUNNING" if state.get("service_active") else "PAUSED",
                "mode": snap["mode"],
                "cash": snap["cash"],
                "equity": snap["equity"],
                "positions": len(snap["positions"]),
                "daily_pnl": state.get("daily_pnl", 0.0),
                "exposure": state.get("total_exposure", 0.0),
            }),
            parse_mode="HTML",
        )


    @dp.message(Command("pause"))
    async def pause(message: Message):
        nonlocal autonomous_task
        if not await guard(message):
            return
        autonomous.pause()
        if autonomous_task:
            autonomous_task.cancel()
            try:
                await autonomous_task
            except asyncio.CancelledError:
                pass
            autonomous_task = None
        await autonomous.initialize()
        await autonomous.run_once()
        await message.answer("⏸ <b>KRONOS НА ПАУЗЕ</b>\nНовые расчёты и PAPER-сделки остановлены.", parse_mode="HTML")

    @dp.message(Command("report"))
    async def report(message: Message):
        if not await guard(message):
            return
        snap = autonomous.snapshot()
        report_data = await autonomous.report()
        state = snap["risk"]
        service = "RUNNING" if state.get("service_active") else "PAUSED"
        await message.answer(
            format_report(report_data) + f"\nService: <b>{service}</b>",
            parse_mode="HTML",
        )

    @dp.message(Command("emergency"))
    async def emergency(message: Message):
        nonlocal autonomous_task
        if not await guard(message):
            return
        autonomous.emergency_stop()
        if autonomous_task:
            autonomous_task.cancel()
            try:
                await autonomous_task
            except asyncio.CancelledError:
                pass
            autonomous_task = None
        await autonomous.initialize()
        await autonomous.run_once()
        await message.answer("🚨 <b>KRONOS АВАРИЙНО ОСТАНОВЛЕН</b>\nДля безопасности повторный запуск заблокирован до ручного изменения состояния.", parse_mode="HTML")

    return bot, dp


async def run():
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не настроен")
    bot, dp = build_application()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())
