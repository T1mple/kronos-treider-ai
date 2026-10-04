from app.paper.portfolio import PaperPortfolio

def test_paper_portfolio_round_trip():
    p=PaperPortfolio(300)
    p.open("BTCUSDT","long",50,100)
    result=p.close("BTCUSDT",110)
    assert result["pnl"]==5
    assert result["cash"]==305
