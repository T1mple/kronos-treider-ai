import asyncio
from datetime import datetime, timezone
from app.paper.reporting import PeriodicReporter

class ReportScheduler:
    """Refreshes paper performance reports. It never executes trades."""

    def __init__(self, journal, reporter=None, interval_seconds=3600):
        self.journal = journal
        self.reporter = reporter or PeriodicReporter()
        self.interval_seconds = interval_seconds
        self.running = False
        self.latest = {}

    def snapshot(self):
        return self.latest

    async def refresh(self):
        records = self.journal.recent(10000)
        self.latest = self.reporter.all_periods(records)
        self.latest["generated_at"] = datetime.now(timezone.utc).isoformat()
        return self.latest

    async def loop(self):
        self.running = True
        while self.running:
            try:
                await self.refresh()
            except Exception as exc:
                self.latest = {"error": str(exc)}
            await asyncio.sleep(self.interval_seconds)

    def stop(self):
        self.running = False
