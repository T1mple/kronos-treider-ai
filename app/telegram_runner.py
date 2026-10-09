import asyncio
import html
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.config import settings
from app.paper.autonomous import AutonomousPaperEngine, PaperDecision
from app.telegram_bot import authorized
from app.paper.store import paper_diagnostics, save_state


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

BOT_COMMANDS = [
    ("start", "Запустить робота 24/7"),
    ("status", "Состояние робота"),
    ("pause", "Поставить робота на паузу"),
    ("resume", "Снять робота с паузы"),
    ("report", "Последний отчёт"),
    ("emergency", "Аварийная остановка"),
]


def format_dict(title, data):
    lines = [f"<b>{html.escape(str(title))}</b>"]
    for key, value in data.items():
        if isinstance(value, float):
            value = f"{value:.4f}"
        lines.append(f"<b>{html.escape(str(key))}</b>: {html.escape(str(value))}")
    return "\n".join(lines)


def format_report(report, diagnostics=None):
    lines = [
        "<b>📈 KRONOS PAPER REPORT</b>",
        "",
        f"Equity: <b>USD {report['equity']:.2f}</b>",
        f"Total PnL: <b>USD {report['total_pnl']:+.2f}</b>",
        f"Realized PnL: <b>USD {report['realized_pnl']:+.2f}</b>",
        f"Closed trades: <b>{report['closed_trades']}</b>",
        f"Wins / losses: <b>{report['winning_trades']} / {report['losing_trades']}</b>",
        f"Win rate: <b>{report['win_rate']:.1%}</b>",
        f"Max drawdown: <b>{report['max_drawdown']:.1%}</b>",
        f"Equity snapshots: <b>{report['snapshots']}</b>",
    ]
    if diagnostics:
        actions = diagnostics.get("actions", {})
        reasons = diagnostics.get("reasons", {})
        lines.extend(["", "<b>🔎 DIAGNOSTICS</b>", f"Decisions: <b>{diagnostics.get('decisions', 0)}</b>"])
        if actions:
            lines.append("Actions: <b>" + ", ".join(f"{html.escape(str(k))}={html.escape(str(v))}" for k, v in actions.items()) + "</b>")
        if reasons:
            lines.append("Reasons:")
            for reason, count in list(reasons.items())[:5]:
                lines.append(f"• {html.escape(str(reason))}: <b>{count}</b>")
        latest = diagnostics.get("latest", [])
        if latest:
            lines.append("Latest:")
            for item in latest[-6:]:
                lines.append(f"• {html.escape(str(item['symbol']))}: signal {item['signal']:+.3f}, conf {item['confidence']:.1%}, {html.escape(str(item['action']))} ({html.escape(str(item['reason']))})")
    lines.extend(["", "Mode: <b>PAPER SIMULATION</b>", "Real orders: <b>OFF</b>"])
    return "\n".join(lines)


def build_application():
    from aiogram import Bot, Dispatcher
    from aiogram.types import BotCommand
    from aiogram.filters import Command, CommandStart
    from aiogram.types import Message, BotCommandScopeDefault

    bot = Bot(settings.telegram_bot_token)
    dp = Dispatcher()
    autonomous = AutonomousPaperEngine()
    autonomous_task = None
    daily_report_task = None

    async def notify_text(text):
        admin_ids = _admin_ids()
        if not admin_ids:
            logger.warning("No Telegram admin IDs configured; notification was not sent")
            return False
        try:
            for chat_id in admin_ids:
                await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", disable_notification=False)
            return True
        except Exception:
            logger.exception("Telegram notification failed")
            return False

    async def notify_paper_event(event: PaperDecision):
        """Send a detailed Telegram message for each simulated trade."""
        is_buy = event.action == "BUY"
        icon = "🟢" if is_buy else "🔴"
        notional = event.price * event.quantity
        lines = [
            f"<b>{icon} KRONOS PAPER: {'ПОКУПКА' if is_buy else 'ПРОДАЖА'}</b>",
            "",
            f"Монета: <b>{html.escape(event.symbol)}</b>",
            f"Цена исполнения: <b>${event.price:,.4f}</b>",
            f"Количество: <b>{event.quantity:.8f}</b>",
            f"Объём сделки: <b>${notional:,.2f}</b>",
        ]
        if not is_buy:
            lines.append(f"Реализованный PnL: <b>${event.realized_pnl:+,.2f}</b>")
        lines.extend([
            f"Сигнал: <b>{event.signal:+.3f}</b> | уверенность: <b>{event.kronos_confidence:.1%}</b>",
            f"Причина: {html.escape(event.reason)}",
            "",
            "Режим: <b>PAPER SIMULATION</b>",
            "Реальные ордера: <b>OFF</b>",
        ])
        await notify_text("\n".join(lines))

    async def notify_cycle(events):
        """Notify only on actual simulated trades or operational errors, not HOLD noise."""
        for event in events:
            if event.action in {"BUY", "SELL"}:
                await notify_paper_event(event)
            elif event.action == "ERROR":
                await notify_text(
                    f"⚠️ <b>KRONOS: ОШИБКА ЦИКЛА</b>\n\n"
                    f"Инструмент: <b>{html.escape(event.symbol)}</b>\n"
                    f"Причина: {html.escape(event.reason)}\n\n"
                    "Режим: <b>PAPER SIMULATION</b>\n"
                    "Реальные ордера: <b>OFF</b>"
                )

    def _admin_ids():
        # Keep admin IDs unique so one notification is never sent twice
        # because the same ID was configured more than once.
        return list(dict.fromkeys(
            int(x.strip())
            for x in settings.telegram_admin_ids.split(",")
            if x.strip().isdigit()
        ))

    async def guard(message):
        return bool(message.from_user and authorized(message.from_user.id))


    async def telegram_loop():
        """Run the single autonomous PAPER worker for this Telegram process."""
        await autonomous.initialize()
        while True:
            try:
                events = await autonomous.run_once()
                await notify_cycle(events)
                await asyncio.sleep(900)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Telegram PAPER worker cycle failed")
                await asyncio.sleep(60)

    async def ensure_worker():
        nonlocal autonomous_task
        if autonomous_task and not autonomous_task.done():
            return False
        if autonomous.risk.state.circuit_breaker or autonomous.risk.state.paused or not autonomous.risk.state.service_active:
            return False
        autonomous_task = asyncio.create_task(telegram_loop())
        return True

    async def daily_report_loop():
        """Send one automatic daily report at the configured local time."""
        tz = ZoneInfo(settings.report_timezone)
        while True:
            now = datetime.now(tz)
            target = now.replace(hour=settings.report_hour, minute=settings.report_minute, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            await asyncio.sleep(max(1.0, (target - now).total_seconds()))
            try:
                report_data = await autonomous.report()
                diagnostics = await paper_diagnostics(100)
                snap = autonomous.snapshot()
                state = snap["risk"]
                service = "RUNNING" if state.get("service_active") else "PAUSED"
                await notify_text(format_report(report_data, diagnostics) + f"\nService: <b>{service}</b>\n<b>🕘 Daily report</b>")
                logger.info("Daily Telegram report sent")
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Daily Telegram report failed")

    @dp.startup()
    async def startup():
        nonlocal autonomous_task, daily_report_task
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
        await autonomous.initialize()
        # PAPER is the Telegram worker's service. Start exactly one worker
        # here so the bot is actually 24/7, not merely reporting RUNNING.
        await ensure_worker()
        daily_report_task = asyncio.create_task(daily_report_loop())
        logger.info("Daily Telegram report scheduler started for %s:%02d %s", settings.report_hour, settings.report_minute, settings.report_timezone)

    @dp.shutdown()
    async def shutdown():
        autonomous.stop()
        for task in (autonomous_task, daily_report_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        await bot.session.close()

    @dp.message(CommandStart())
    async def start(message: Message):
        nonlocal autonomous_task
        if not await guard(message):
            await message.answer("Доступ запрещён.")
            return
        await autonomous.initialize()
        # /start launches an inactive PAPER service, but does not silently
        # clear an emergency circuit breaker. /resume is the explicit recovery.
        if autonomous.risk.state.circuit_breaker:
            await message.answer(
                "🚨 <b>KRONOS ЗАБЛОКИРОВАН</b>\n"
                "После аварийной остановки используй /resume для ручного восстановления.",
                parse_mode="HTML",
            )
            return
        if autonomous_task and not autonomous_task.done():
            await message.answer("▶️ <b>KRONOS УЖЕ АКТИВЕН</b>\nPAPER-режим работает 24/7.", parse_mode="HTML")
            return
        autonomous.risk.state.paused = False
        autonomous.risk.state.service_active = True
        await save_state(autonomous.paper, autonomous.risk)
        started = await ensure_worker()
        if not started:
            await message.answer("⚠️ Не удалось запустить PAPER worker. Проверь логи.", parse_mode="HTML")
            return
        await message.answer(
            "🚀 <b>KRONOS ЗАПУЩЕН</b>\n\n"
            "Робот работает 24/7 в PAPER-режиме.\n"
            "Я буду присылать важные события и отчёты автоматически.\n"
            "Реальные ордера: <b>OFF</b>.",
            parse_mode="HTML",
        )

    @dp.message(Command("resume"))
    async def resume(message: Message):
        nonlocal autonomous_task
        if not await guard(message):
            return
        await autonomous.initialize()
        autonomous.risk.state.circuit_breaker = False
        autonomous.risk.state.paused = False
        autonomous.risk.state.service_active = True
        await save_state(autonomous.paper, autonomous.risk)
        started = await ensure_worker()
        if not started:
            await message.answer("▶️ <b>KRONOS УЖЕ АКТИВЕН</b>\nPAPER-режим активен.", parse_mode="HTML")
            return
        await message.answer(
            "▶️ <b>KRONOS СНЯТ С ПАУЗЫ</b>\n\n"
            "PAPER-режим активен. Реальные ордера: <b>OFF</b>.",
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
                "circuit_breaker": state.get("circuit_breaker", False),
            }),
            parse_mode="HTML",
        )


    @dp.message(Command("pause"))
    async def pause(message: Message):
        nonlocal autonomous_task
        if not await guard(message):
            return
        autonomous.pause()
        await save_state(autonomous.paper, autonomous.risk)
        if autonomous_task:
            autonomous_task.cancel()
            try:
                await autonomous_task
            except asyncio.CancelledError:
                pass
            autonomous_task = None
        await message.answer("⏸ <b>KRONOS НА ПАУЗЕ</b>\nНовые расчёты и PAPER-сделки остановлены.", parse_mode="HTML")

    @dp.message(Command("report"))
    async def report(message: Message):
        if not await guard(message):
            return
        try:
            snap = autonomous.snapshot()
            report_data = await autonomous.report()
            diagnostics = await paper_diagnostics(100)
            state = snap["risk"]
            service = "RUNNING" if state.get("service_active") else "PAUSED"
            await message.answer(
                format_report(report_data, diagnostics) + f"\nService: <b>{service}</b>",
                parse_mode="HTML",
            )
        except Exception:
            logger.exception("Telegram /report failed")
            await message.answer(
                "⚠️ <b>Не удалось сформировать отчёт.</b> Ошибка записана в лог Telegram.",
                parse_mode="HTML",
            )

    @dp.message(Command("emergency"))
    async def emergency(message: Message):
        nonlocal autonomous_task
        if not await guard(message):
            return
        autonomous.emergency_stop()
        await save_state(autonomous.paper, autonomous.risk)
        if autonomous_task:
            autonomous_task.cancel()
            try:
                await autonomous_task
            except asyncio.CancelledError:
                pass
            autonomous_task = None
        await message.answer("🚨 <b>KRONOS АВАРИЙНО ОСТАНОВЛЕН</b>\nДля безопасности повторный запуск заблокирован до ручного изменения состояния.", parse_mode="HTML")

    return bot, dp


async def run():
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не настроен")
    bot, dp = build_application()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run())
