from datetime import datetime, timezone

def quote_age_seconds(timestamp):
    try:
        ts=datetime.fromisoformat(str(timestamp).replace("Z","+00:00"))
        return max(0.0,(datetime.now(timezone.utc)-ts).total_seconds())
    except (TypeError,ValueError):
        return float("inf")

def is_stale(timestamp,max_age_seconds=15):
    return quote_age_seconds(timestamp)>max_age_seconds
