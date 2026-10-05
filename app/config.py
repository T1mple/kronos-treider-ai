from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    live_trading: bool = False
    trading_mode: str = "BACKTEST"
    database_url: str = "postgresql+asyncpg://kronos:kronos@postgres:5432/kronos"
    redis_url: str = "redis://redis:6379/0"
    telegram_bot_token: str = ""
    telegram_admin_ids: str = ""
    alpha_vantage_api_key: str = ""
    report_timezone: str = "Asia/Almaty"
    report_hour: int = 9
    report_minute: int = 0
    max_position_usd: float = 50
    max_total_exposure_usd: float = 200
    max_daily_loss_usd: float = 10
    max_concurrent_positions: int = 8
    max_correlated_exposure: float = 0.50
    stop_loss_pct: float = 0.03
    circuit_breaker_loss_usd: float = 10
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
