import argparse
import asyncio
import json
from app.research.runner import ResearchRunner

def main():
    parser=argparse.ArgumentParser(description="Kronos Trader AI research runner")
    parser.add_argument("--symbol",default="BTCUSDT")
    parser.add_argument("--interval",default="1h")
    parser.add_argument("--limit",type=int,default=500)
    parser.add_argument("--train",type=int,default=300)
    parser.add_argument("--test",type=int,default=50)
    parser.add_argument("--step",type=int,default=50)
    args=parser.parse_args()
    result=asyncio.run(ResearchRunner().run(args.symbol,args.interval,args.limit,args.train,args.test,args.step))
    print(json.dumps(ResearchRunner.as_dict(result),indent=2))

if __name__=="__main__":
    main()
