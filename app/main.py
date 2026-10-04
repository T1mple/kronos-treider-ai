from fastapi import FastAPI
from app.config import settings
from app.risk import RiskEngine

app = FastAPI(title='Kronos Trader AI', version='0.1.0')
risk = RiskEngine(settings)

@app.get('/health')
async def health():
    return {'status':'ok','mode':settings.trading_mode,'live_trading':settings.live_trading}

@app.get('/risk')
async def risk_status():
    return risk.snapshot()
