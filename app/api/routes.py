from dataclasses import asdict
from fastapi import APIRouter, HTTPException
from app.api.schemas import ResearchRequest, PaperOrderRequest
from app.paper.engine import PaperTradingEngine
from app.paper.decision_log import DecisionJournal
from app.paper.portfolio import PaperPortfolio
from app.paper.performance import PerformanceAnalyzer
from app.paper.regime_performance import RegimePerformance
from app.paper.reporting import PeriodicReporter
from app.research.runner import ResearchRunner
from app.research.system import ResearchSystem

router=APIRouter()
paper=PaperTradingEngine()
portfolio=PaperPortfolio()
journal=DecisionJournal()
performance=PerformanceAnalyzer()
regime_performance=RegimePerformance()
periodic_reporter=PeriodicReporter()
research_system=ResearchSystem()

@router.get("/status")
async def status():
    return {"mode":"PAPER","live_trading":False,"equity":paper.equity({}),"positions":list(paper.ledger.positions.values())}

@router.get("/portfolio")
async def portfolio_status():
    return portfolio.snapshot()

@router.get("/journal")
async def journal_status(limit:int=20):
    return {"records":journal.recent(max(1,min(limit,100)))}

@router.get("/reports")
async def reports():
    return periodic_reporter.all_periods(journal.recent(10000))


@router.get("/performance")
async def performance_status():
    records=journal.recent(1000)
    pnls=[x["outcome_pnl"] for x in records if x["outcome_pnl"] is not None]
    metrics=performance.analyze(pnls)
    regimes=regime_performance.analyze(records)
    return {"overall":asdict(metrics),"by_regime":{k:asdict(v) for k,v in regimes.items()}}

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
    decision=result.decision
    record=journal.record(request.symbol,type("Decision",(),{"adaptive":decision["adaptive"],"allocation":decision["allocation"]})(),price=None)
    return {"research":runner.as_dict(result),"journal_record":asdict(record)}

@router.post("/journal/{index}/close")
async def close_journal(index:int,pnl:float):
    try: return asdict(journal.close(index,pnl))
    except IndexError: raise HTTPException(status_code=404,detail="journal record not found")


@router.post("/research/unified")
async def unified_research(request: ResearchRequest):
    runner=ResearchRunner()
    result=await runner.run_unified(request.symbol,request.interval,request.limit)
    record_data={
        "adaptive":result["adaptive"],
        "allocation":result["decision"]["allocation"],
    }
    record=journal.record(request.symbol,type("Decision",(),record_data)(),price=None)
    return {"research":result,"journal_record":asdict(record)}



@router.post("/forward/run")
async def forward_run():
    from app.paper.forward_runner import ForwardPaperRunner
    runner=ForwardPaperRunner()
    return await runner.run_once()
\n@router.get("/forward")
async def forward_status():
    return research_system.forward.snapshot()

@router.get("/forward/performance")
async def forward_performance():
    return {
        "overall": research_system.forward.performance(),
        "by_regime": research_system.forward.performance_by_regime(),
    }

@router.get("/system/summary")
async def system_summary():
    records=journal.recent(1000)
    pnls=[x["outcome_pnl"] for x in records if x["outcome_pnl"] is not None]
    metrics=performance.analyze(pnls)
    return {
        "mode":"RESEARCH_PAPER",
        "live_trading":False,
        "journal_records":len(records),
        "performance":asdict(metrics),
        "risk":research_system.risk.state.__dict__.copy(),
    }
