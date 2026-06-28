"""AR-131 CPI/PPI release-morning cross-asset gap-dispersion fade.

QFA-compatible research model. On explicit public CPI/PPI release dates, after
the 8:30 ET release is known and regular-session open has occurred, the model
measures each ETF's opening gap (release-day open vs prior close), normalizes by
prior gap history only, and at the release-day close fades the top-vs-bottom
cross-asset gap dispersion for the next 2 closes. The signal deliberately
uses no release-day close/high/low/volume feature, and never places orders by
itself.
"""
from __future__ import annotations
import math
from typing import Any
import pandas as pd

UNIVERSE=('TIP', 'SCHP', 'TLT', 'IEF', 'SHY', 'UUP', 'GLD', 'DBC', 'USO', 'XLE', 'XLRE', 'SPY', 'QQQ')
EVENT_DATES=frozenset(['2019-01-11', '2019-01-15', '2019-02-13', '2019-02-14', '2019-03-12', '2019-03-13', '2019-04-10', '2019-04-11', '2019-05-09', '2019-05-10', '2019-06-11', '2019-06-12', '2019-07-11', '2019-07-12', '2019-08-09', '2019-08-13', '2019-09-11', '2019-09-12', '2019-10-08', '2019-10-10', '2019-11-13', '2019-11-14', '2019-12-11', '2019-12-12', '2020-01-14', '2020-01-15', '2020-02-13', '2020-02-19', '2020-03-11', '2020-03-12', '2020-04-09', '2020-04-10', '2020-05-12', '2020-05-13', '2020-06-10', '2020-06-11', '2020-07-10', '2020-07-14', '2020-08-11', '2020-08-12', '2020-09-10', '2020-09-11', '2020-10-13', '2020-10-14', '2020-11-12', '2020-11-13', '2020-12-10', '2020-12-11', '2021-01-13', '2021-01-15', '2021-02-10', '2021-02-17', '2021-03-10', '2021-03-12', '2021-04-09', '2021-04-13', '2021-05-12', '2021-05-13', '2021-06-10', '2021-06-15', '2021-07-13', '2021-07-14', '2021-08-11', '2021-08-12', '2021-09-10', '2021-09-14', '2021-10-13', '2021-10-14', '2021-11-09', '2021-11-10', '2021-12-10', '2021-12-14', '2022-01-12', '2022-01-13', '2022-02-10', '2022-02-15', '2022-03-10', '2022-03-15', '2022-04-12', '2022-04-13', '2022-05-11', '2022-05-12', '2022-06-10', '2022-06-14', '2022-07-13', '2022-07-14', '2022-08-10', '2022-08-11', '2022-09-13', '2022-09-14', '2022-10-12', '2022-10-13', '2022-11-10', '2022-11-15', '2022-12-09', '2022-12-13', '2023-01-12', '2023-01-18', '2023-02-14', '2023-02-16', '2023-03-14', '2023-03-15', '2023-04-12', '2023-04-13', '2023-05-10', '2023-05-11', '2023-06-13', '2023-06-14', '2023-07-12', '2023-07-13', '2023-08-10', '2023-08-11', '2023-09-13', '2023-09-14', '2023-10-11', '2023-10-12', '2023-11-14', '2023-11-15', '2023-12-12', '2023-12-13', '2024-01-11', '2024-01-12', '2024-02-13', '2024-02-16', '2024-03-12', '2024-03-14', '2024-04-10', '2024-04-11', '2024-05-14', '2024-05-15', '2024-06-12', '2024-06-13', '2024-07-11', '2024-07-12', '2024-08-13', '2024-08-14', '2024-09-11', '2024-09-12', '2024-10-10', '2024-10-11', '2024-11-13', '2024-11-14', '2024-12-11', '2024-12-12', '2025-01-14', '2025-01-15', '2025-02-12', '2025-02-13', '2025-03-12', '2025-03-13', '2025-04-10', '2025-04-11', '2025-05-13', '2025-05-15', '2025-06-11', '2025-06-12', '2025-07-15', '2025-07-16', '2025-08-12', '2025-08-14', '2025-09-10', '2025-09-11', '2025-10-15', '2025-10-16', '2025-11-13', '2025-12-10'])
LOOKBACK=120
HOLD_DAYS=2
DISPERSION_THRESHOLD=0.75

def _finite(x: Any, default: float=0.0) -> float:
    try:
        y=float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default

def generate_signals(context) -> dict[str, float]:
    symbols=list(getattr(context,'symbols',[]) or [])
    flat={s:0.0 for s in symbols}
    prices=getattr(context,'prices',None)
    if prices is None or len(prices)==0:
        return flat
    df=prices.copy()
    df['timestamp']=pd.to_datetime(df['timestamp'], utc=True)
    as_of=pd.Timestamp(getattr(context,'as_of',df['timestamp'].max()))
    as_of=as_of.tz_convert('UTC') if as_of.tzinfo else as_of.tz_localize('UTC')
    df=df[df['timestamp']<=as_of]
    op=df.pivot(index='timestamp',columns='symbol',values='open').sort_index()
    close=df.pivot(index='timestamp',columns='symbol',values='close').sort_index().ffill()
    use=[s for s in UNIVERSE if s in symbols and s in op.columns and s in close.columns]
    if len(use)<6 or len(close)<LOOKBACK+2:
        return flat
    idx=close.index
    dates=[x.strftime('%Y-%m-%d') for x in idx]
    last=None
    for i,d in enumerate(dates):
        if d in EVENT_DATES:
            last=i
    if last is None:
        return flat
    age=len(idx)-1-last
    if age<0 or age>=HOLD_DAYS:
        return flat
    gaps=op[use]/close[use].shift(1)-1.0
    if last<LOOKBACK+1:
        return flat
    z={}
    for s in use:
        hist=gaps[s].iloc[last-LOOKBACK:last].dropna()
        sd=_finite(hist.std(ddof=1))
        g=_finite(gaps[s].iloc[last], float('nan'))
        if len(hist)>=60 and sd>1e-8 and math.isfinite(g):
            z[s]=max(-5.0,min(5.0,(g-_finite(hist.mean()))/sd))
    if len(z)<6:
        return flat
    vals=list(z.values())
    mean=sum(vals)/len(vals)
    disp=(sum((v-mean)**2 for v in vals)/(len(vals)-1))**0.5 if len(vals)>1 else 0.0
    if disp<DISPERSION_THRESHOLD:
        return flat
    ranked=sorted(z.items(), key=lambda kv: kv[1])
    k=max(2,min(3,len(ranked)//4))
    longs=[s for s,_ in ranked[:k]]
    shorts=[s for s,_ in ranked[-k:]]
    decay=max(0.0,1.0-age/HOLD_DAYS)
    out=dict(flat)
    for s in longs:
        out[s]=0.5*decay/k
    for s in shorts:
        out[s]=-0.5*decay/k
    return out
