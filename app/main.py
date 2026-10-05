import logging
from fastapi import FastAPI
from app.config import settings
from app.risk import RiskEngine
from app.api.routes import router
from app.api.stock_routes import router as market_router
from app.dashboard import dashboard_html

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="Kronos Trader AI", version="0.2.0")
risk = RiskEngine(settings)
app.include_router(router, prefix="/api")
app.include_router(market_router, prefix="/api")

@app.get("/")
async def dashboard():
    return dashboard_html()

@app.get("/health")
async def health():
    return {"status":"ok","mode":settings.trading_mode,"live_trading":settings.live_trading}

@app.get("/risk")
async def risk_status():
    return risk.snapshot()
