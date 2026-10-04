from app.telegram_bot import authorized, TelegramDashboard

def test_unauthorized_without_admins(monkeypatch):
    monkeypatch.setattr("app.telegram_bot.settings.telegram_admin_ids", "")
    assert authorized(123456) is False

def test_dashboard_starts_in_paper_mode():
    data=TelegramDashboard().status()
    assert data["mode"]=="PAPER"
    assert data["live_trading"] is False
    assert data["paused"] is False

def test_dashboard_emergency_pauses():
    dashboard=TelegramDashboard()
    result=dashboard.emergency()
    assert result["emergency"] is True
    assert dashboard.status()["paused"] is True
