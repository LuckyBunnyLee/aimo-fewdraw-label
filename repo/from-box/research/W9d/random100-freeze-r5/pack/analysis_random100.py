"""Frozen before outcomes: pure all-answer solve loss and strict numeric reliability."""
import collections, numpy as np
FAM=['base','surface_gs','surface_dlm']
def interval(x,seed,B=2000):
    x=np.asarray(x,float)
    if not len(x):return dict(est=None,ci95=None,n=0)
    rng=np.random.default_rng(seed)
    draws=[float(x[rng.integers(0,len(x),len(x))].mean()) for _ in range(B)]
    return dict(est=float(x.mean()),ci95=np.quantile(draws,[.025,.975]).tolist(),n=len(x))
def kappa(rows):
    if len(rows)<2:return None
    a=np.array([r['nr'] for r in rows],float);n=np.array([r['binary'] for r in rows],float)
    q=a.sum()/n.sum();pe=q*q+(1-q)**2
    if pe==1:return None
    return float((((a*(a-1)+(n-a)*(n-a-1))/(n*(n-1))).mean()-pe)/(1-pe))
def analyse(draws,tag,B=2000):
    pids=sorted({r['pid'] for r in draws});waves=sorted({r['wave'] for r in draws})
    cells=collections.defaultdict(list)
    for r in draws:cells[r['pid'],r['wave'],r['family']].append(r)
    rows=[]
    for p in pids:
        tags=[]; rates={};half=[];mid=len(waves)//2
        for w in waves:
            c={fm:cells[p,w,fm] for fm in FAM};assert all(len(v)==4 for v in c.values())
            tags.append(tag(c,4))
        for fm in FAM:rates[fm]=float(np.mean([r['correct'] for w in waves for r in cells[p,w,fm]]))
        for ws in (waves[:mid],waves[mid:]):
            ps={fm:np.mean([r['correct'] for w in ws for r in cells[p,w,fm]]) for fm in FAM}
            half.append(float(ps['base']-(ps['surface_gs']+ps['surface_dlm'])/2))
        rows.append(dict(pid=p,solve_loss=rates['base']-(rates['surface_gs']+rates['surface_dlm'])/2,
            rates=rates,nr=tags.count('NR'),binary=tags.count('NR')+tags.count('R'),tags=dict(collections.Counter(tags)),
            numeric_fraction=sum(r['status']=='numeric' for w in waves for fm in FAM for r in cells[p,w,fm])/(12*len(waves)),
            half_change=half[1]-half[0]))
    status={fm:dict(collections.Counter(r['status'] for r in draws if r['family']==fm)) for fm in FAM}
    finish={fm:dict(collections.Counter(str(r['finish']) for r in draws if r['family']==fm)) for fm in FAM}
    if len(waves)<20:return dict(reading='not measured under the planned exposure',waves=len(waves),status=status,finish=finish)
    primary=interval([r['solve_loss'] for r in rows],20261026,B);lo,hi=primary['ci95']
    eligible=[r for r in rows if r['binary']>=5];k=kappa(eligible);bt=[]
    if k is not None:
        rng=np.random.default_rng(20261027)
        for _ in range(B):
            v=kappa([eligible[i] for i in rng.integers(0,len(eligible),len(eligible))])
            if v is not None:bt.append(v)
    return dict(primary=primary,reading='solve loss' if lo>0 else 'solve gain' if hi<0 else 'unresolved',
        caveat='no contemporaneous sham; not independently calibrated as edit-specific',waves=len(waves),originals=len(rows),
        reliability=dict(est=k,ci95=np.quantile(bt,[.025,.975]).tolist() if len(bt)>=.95*B else None,
            eligible=len(eligible),share=len(eligible)/len(rows),defined_resamples=len(bt),planned_resamples=B,
            reading='not estimable' if k is None else 'descriptive conditional on numeric eligibility'),
        by_eligibility={str(b):interval([r['solve_loss'] for r in rows if (r['binary']>=5)==b],20261029+int(b),B) for b in (False,True)},
        half_change=interval([r['half_change'] for r in rows],20261028,B),status=status,finish=finish,per_original=rows)
