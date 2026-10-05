from math import sqrt

def returns(closes):
    return [closes[i]/closes[i-1]-1 for i in range(1,len(closes)) if closes[i-1]]

def correlation(a,b):
    n=min(len(a),len(b)); a,b=returns(a[-n:]),returns(b[-n:]); n=min(len(a),len(b))
    if n<2: return 0.0
    a,b=a[-n:],b[-n:]; ma=sum(a)/n; mb=sum(b)/n
    da=[x-ma for x in a]; db=[x-mb for x in b]
    den=sqrt(sum(x*x for x in da)*sum(x*x for x in db))
    return sum(x*y for x,y in zip(da,db))/den if den else 0.0

def concentration(exposures):
    total=sum(max(0.0,float(x)) for x in exposures.values())
    if total<=0: return 0.0
    return sum((float(x)/total)**2 for x in exposures.values())
