from fastapi import APIRouter, HTTPException
from app.api.schemas import ResearchRequest, PaperOrderRequest
from app.paper.engine import PaperTradingEngine
from app.research.runner import ResearchRunner

router=APIRouter()
paper=PaperTradingEngine()

@router.get("/status")
async def status():
    return {"mode":"PAPER","live_trading":False,"equity":paper.equity({}),"positions":list(paper.ledger.positions.values())}

@router.get("/portfolio")
async def portfolio():
    return {"cash":paper.ledger.cash,"positions":list(paper.ledger.positions.values()),"fills":list(paper.ledger.fills)}

@router.post("/paper/order")
async def paper_order(request: PaperOrderRequest):
    try:
        if request.side.lower()=="buy": fill=paper.buy(request.symbol,request.quantity,request.price)
        elif request.side.lower()=="sell": fill=paper.sell(request.symbol,request.quantity,request.price)
        else: raise HTTPException(status_code=400,detail="side must be buy or sell")
        return fill
    except ValueError as exc:
        raise HTTPException(status_code=400,detail=str(exc))

@router.post("/research")
async def research(request: ResearchRequest):
    runner=ResearchRunner()
    result=await runner.run(request.symbol,request.interval,request.limit,request.train_size,request.test_size,request.step)
    return runner.as_dict(result)
