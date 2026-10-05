from dataclasses import dataclass

@dataclass(frozen=True)
class SentimentFactors:
    article_count: int
    bullish: float
    bearish: float
    score: float

def score_news(payload):
    feed=payload.get("feed",[]) if isinstance(payload,dict) else []
    bullish=sum(1 for x in feed if float(x.get("overall_sentiment_score",0))>0.15)
    bearish=sum(1 for x in feed if float(x.get("overall_sentiment_score",0))<-0.15)
    scores=[float(x.get("overall_sentiment_score",0)) for x in feed]
    avg=sum(scores)/len(scores) if scores else 0.0
    return SentimentFactors(len(feed),bullish/len(feed) if feed else 0.0,bearish/len(feed) if feed else 0.0,max(-1.0,min(1.0,avg)))
