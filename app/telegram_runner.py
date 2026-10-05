import asyncio
import logging
from app.config import settings
from app.paper.autotest import PaperAutoTester
from app.paper.autonomous import AutonomousPaperEngine, PaperDecision
from app.telegram_bot import TelegramDashboard, authorized


logger = logging.getLogger(__name__)

BOT_COMMANDS = [
    ("start", "Запуск Kronos"),
    ("help", "Список команд"),
    ("status", "Состояние системы"),
    ("balance", "Баланс"),
    ("positions", "Позиции"),
    ("trades", "История сделок"),
    ("signals", "Сигналы"),
    ("kronos", "Прогноз Kronos"),
    ("risk", "Состояние риска"),
    ("pause", "Пауза paper-режима"),
    ("resume", "Возобновить paper-режим"),
    ("emergency", "Аварийная остановка"),
    ("test", "Paper-тест"),
    ("performance", "Результаты"),
    ("reports", "Отчёты"),
    ("competition", "Сравнение стратегий"),
    ("stocks", "Список акций"),
    ("stock", "Анализ акции"),
    ("etf", "Анализ ETF"),
    ("sectors", "Сектора"),
    ("market", "Состояние рынка"),
]


def format_dict(title, data):
    lines = [f"<b>{title}</b>"]
    for key, value in data.items():
        if isinstance(value, float):
            value = f"{value:.4f}"
        lines.append(f"<b>{key}</b>: {value}")
    return "\n".join(lines)


def build_application():
    from aiogram import Bot, Dispatcher
    from aiogram.types import BotCommand
    from aiogram.filters import Command
    from aiogram.types import Message, BotCommandScopeDefault

    bot = Bot(settings.telegram_bot_token)
    dp = Dispatcher()
    dashboard = TelegramDashboard()
    tester = PaperAutoTester()
    autonomous = AutonomousPaperEngine()
    test_task = None
    autonomous_task = None
    last_report_key = None

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
    async def notify_auto_result(result):
        """Autonomous PAPER monitor: send only meaningful research events to the admin."""
        nonlocal last_report_key
        direction = float(getattr(result, "kronos_direction", 0.0))
        confidence = float(getattr(result, "kronos_confidence", 0.0))
        bucket = "LONG" if direction >= 0.25 else "SHORT" if direction <= -0.25 else "NEUTRAL"
        key = (bucket, round(confidence, 1))
        if bucket == "NEUTRAL" or confidence < 0.60 or key == last_report_key:
            return
        last_report_key = key
        await bot.send_message(
            chat_id=(_admin_ids()[0] if _admin_ids() else None),
            text=(
                "<b>🤖 KRONOS AUTONOMOUS PAPER SIGNAL</b>\n\n"
                f"Symbol: <b>{result.symbol}</b>\n"
                f"Direction: <b>{bucket}</b>\n"
                f"Kronos direction: <b>{direction:+.3f}</b>\n"
                f"Confidence: <b>{confidence:.1%}</b>\n"
                f"Backtest return: <b>{result.return_pct:+.2f}%</b>\n"
                f"Max DD: <b>{result.max_drawdown_pct:.2f}%</b>\n"
                f"Trades in test: <b>{result.trades}</b>\n\n"
                "Mode: <b>PAPER / RESEARCH</b>\n"
                "Real orders: <b>OFF</b>"
            ),
            parse_mode="HTML",
        )

    def _admin_ids():
        return [int(x.strip()) for x in settings.telegram_admin_ids.split(",") if x.strip().isdigit()]

    async def guard(message):
        return bool(message.from_user and authorized(message.from_user.id))

    def result_text(result):
        return (
            "<b>🧪 KRONOS TRADER AI • PAPER TEST</b>\n"
            f"Symbol: <b>{result.symbol}</b>\n"
            f"Interval: <b>{result.interval}</b>\n"
            f"Candles: <b>{result.candles}</b>\n"
            f"Return: <b>{result.return_pct:+.2f}%</b>\n"
            f"Max DD: <b>{result.max_drawdown_pct:.2f}%</b>\n"
            f"Trades: <b>{result.trades}</b>\n"
            f"Fees: <b>{result.fees:.2f} USD</b>\n\n"
            f"Kronos direction: <b>{result.kronos_direction:+.3f}</b>\n"
            f"Kronos confidence: <b>{result.kronos_confidence:.1%}</b>\n"
            f"Updated: <b>{result.updated_at}</b>"
        )

    @dp.startup()
    async def startup():
        nonlocal test_task, autonomous_task
        await bot.set_my_commands(
            [BotCommand(command=command, description=description) for command, description in BOT_COMMANDS],
            scope=BotCommandScopeDefault(),
        )
        test_task = asyncio.create_task(tester.loop(900, on_result=notify_auto_result))
        autonomous_task = asyncio.create_task(autonomous.loop(900, on_event=notify_paper_event))
        logger.info("Telegram bot started; commands registered")

    @dp.shutdown()
    async def shutdown():
        tester.stop()
        if test_task:
            test_task.cancel()
            try:
                await test_task
            except asyncio.CancelledError:
                pass
        await bot.session.close()

    @dp.message(Command("start"))
    async def start(message: Message):
        user_id = message.from_user.id if message.from_user else "unknown"
        if await guard(message):
            await message.answer(
                "<b>🤖 KRONOS TRADER AI</b>\n\n"
                "Система запущена. Реальная торговля отключена.\n"
                "Режим: <b>PAPER / BACKTEST</b>\n\n"
                "Используй меню команд ниже."
            )
        else:
            await message.answer(
                "<b>🤖 KRONOS TRADER AI</b>\n\n"
                "Бот работает, но этот Telegram-пользователь ещё не авторизован.\n"
                f"Твой Telegram ID: <code>{user_id}</code>\n\n"
                "Добавь этот ID в TELEGRAM_ADMIN_IDS в .env и перезапусти Telegram-контейнер."
            )

    @dp.message(Command("help"))
    async def help_command(message: Message):
        await start(message)

    @dp.message(Command("status"))
    async def status(message: Message):
        if await guard(message):
            await message.answer(format_dict("Kronos Trader AI", dashboard.status()), parse_mode="HTML")

    @dp.message(Command("balance"))
    async def balance(message: Message):
        if await guard(message):
            await message.answer(format_dict("Баланс", dashboard.balance()), parse_mode="HTML")

    @dp.message(Command("positions"))
    async def positions(message: Message):
        if await guard(message):
            await message.answer(str(dashboard.positions()))

    @dp.message(Command("trades"))
    async def trades(message: Message):
        if await guard(message):
            await message.answer(str(dashboard.trades()))

    @dp.message(Command("test"))
    async def test(message: Message):
        if not await guard(message):
            return
        try:
            result = await tester.run_once()
            await message.answer(result_text(result), parse_mode="HTML")
        except Exception as exc:
            await message.answer(f"❌ Ошибка бумажного теста: {exc}")

    @dp.message(Command("performance"))
    async def performance(message: Message):
        if not await guard(message):
            return
        if tester.latest:
            await message.answer(result_text(tester.latest), parse_mode="HTML")
        else:
            await message.answer("⏳ Первый тест ещё выполняется.")

    @dp.message(Command("pause"))
    async def pause(message: Message):
        if await guard(message):
            dashboard.pause()
            await message.answer("⏸ Бумажная торговля приостановлена. Реальная торговля отключена.")

    @dp.message(Command("resume"))
    async def resume(message: Message):
        if await guard(message):
            dashboard.resume()
            await message.answer("▶️ Бумажный режим возобновлён.")

    @dp.message(Command("emergency"))
    async def emergency(message: Message):
        if await guard(message):
            dashboard.emergency()
            await message.answer("🚨 АВАРИЙНАЯ ОСТАНОВКА активирована. Реальная торговля отключена.")

    @dp.message(Command("kronos"))
    async def kronos(message: Message):
        if await guard(message):
            await message.answer(format_dict("Прогноз Kronos", await dashboard.kronos()), parse_mode="HTML")

    @dp.message(Command("signals"))
    async def signals(message: Message):
        if await guard(message):
            await message.answer(str(await dashboard.signals()))

    @dp.message(Command("reports"))
    async def reports(message: Message):
        if not await guard(message):
            return
        data = dashboard.reports()
        labels = {
            "daily": "📅 День",
            "weekly": "📆 Неделя",
            "monthly": "🗓 Месяц",
            "quarterly": "📊 Квартал",
            "half_year": "📈 Полгода",
            "yearly": "🏦 Год",
        }
        lines = ["<b>📊 ОТЧЁТЫ KRONOS TRADER AI</b>", "Режим: PAPER / research", ""]
        for key, label in labels.items():
            metrics = data[key]["metrics"]
            lines.append(
                f"<b>{label}</b> · сделок {metrics['trades']} · "
                f"P&L {metrics['total_pnl']:+.2f} · win-rate {metrics['win_rate']:.1%}"
            )
        await message.answer("\n".join(lines), parse_mode="HTML")

    @dp.message(Command("competition"))
    async def competition(message: Message):
        if not await guard(message):
            return
        try:
            rows = await dashboard.competition()
            lines = ["<b>🏆 СОРЕВНОВАНИЕ РОБОТОВ</b>", "Одинаковые комиссии и проскальзывание.", ""]
            for row in rows:
                lines.append(
                    f"{row['rank']}. <b>{row['name']}</b> | доходность {row['return_pct']:+.2f}% | "
                    f"DD {row['max_drawdown_pct']:.2f}% | сделок {row['trades']} | score {row['score']:+.2f}"
                )
            await message.answer("\n".join(lines), parse_mode="HTML")
        except Exception as exc:
            await message.answer(f"❌ Ошибка соревнования: {exc}")

    return bot, dp


async def run():
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не настроен")
    bot, dp = build_application()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())
