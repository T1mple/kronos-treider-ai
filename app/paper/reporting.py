from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from app.paper.performance import PerformanceAnalyzer

PERIODS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
    "quarterly": timedelta(days=90),
    "half_year": timedelta(days=182),
    "yearly": timedelta(days=365),
}

@dataclass
class PeriodReport:
    period: str
    start: str
    end: str
    metrics: dict

class PeriodicReporter:
    """Build calendar-relative paper performance reports from decision records."""

    def __init__(self, analyzer=None):
        self.analyzer = analyzer or PerformanceAnalyzer()

    def report(self, records, period, now=None):
        if period not in PERIODS:
            raise ValueError(f"unsupported period: {period}")
        end = now or datetime.now(timezone.utc)
        start = end - PERIODS[period]
        pnls = []
        for record in records:
            timestamp = self._parse_timestamp(record.get("timestamp"))
            pnl = record.get("outcome_pnl")
            if timestamp and pnl is not None and start <= timestamp <= end:
                pnls.append(float(pnl))
        return PeriodReport(period, start.isoformat(), end.isoformat(), asdict(self.analyzer.analyze(pnls)))

    def all_periods(self, records, now=None):
        return {name: asdict(self.report(records, name, now)) for name in PERIODS}

    @staticmethod
    def _parse_timestamp(value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
