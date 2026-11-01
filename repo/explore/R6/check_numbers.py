"""CPU-only blind referee arithmetic; reads only paper-number outputs and pinned draws."""
import collections, hashlib, json, math, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
dc = json.loads((ROOT/'explore/W9b/decomp/RESULT.json').read_text())
sh = json.loads((ROOT/'explore/W9b/decomp/SHAM-PHASE0-RESULT.json').read_text())
num = json.loads((ROOT/'pair/aimo/report/numbers/w9b-t084.json').read_text())
for p,h in num['_manifest'].items():
    assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
path = ROOT/'explore/W9b/ready63rel/out/DRAWS.jsonl'
assert hashlib.sha256(path.read_bytes()).hexdigest()==dc['inputs'][str(path)]
rows=[json.loads(l) for l in path.read_text().splitlines()]
cells=collections.defaultdict(list)
for r in rows: cells[r['pid'],r['family'],(r['replicate']-1000)//4].append(r)
pids=sorted({r['pid'] for r in rows})
families=['base','surface_gs','surface_dlm']
def tag(arms):
    if not sum((r['correct'] or 0) for r in arms[0]): return 'FLOOR'
    if any(r['status']!='numeric' for a in arms for r in a): return 'UNUSABLE'
    c=[sum((r['correct'] or 0) for r in a) for a in arms]
    return 'NR' if min(c[1:])<c[0] else 'R'
def rate(tags):
    b=[t for t in tags if t in ['NR','R']]
    return b.count('NR')/len(b) if b else None
def q(pb,pg,pd,n=4):
    pm=lambda p,k: math.comb(n,k)*p**k*(1-p)**(n-k)
    return sum(pm(pb,k)*(1-sum(pm(pg,j) for j in range(k,n+1))*sum(pm(pd,j) for j in range(k,n+1))) for k in range(1,n+1))/(1-(1-pb)**n)
out=[]
def check(label,value,key,digits=3):
    expected=num['values'][key]
    out.append(dict(label=label,rederived=value,paper=expected,status='MATCH' if round(value,digits)==expected else 'MISMATCH'))
for p in [.5,.9,.95,.99]:check(f'N0({p})',q(p,p,p),'dc_n0_p'+str(p)[2:],2)
for n in [1,4,16,64]:check(f'N0(.9), n={n}',q(.9,.9,.9,n),f'dc_n0_p9_n{n}',2)
for p in [.8,.9,.95,.99]:
    check(f'LR p={p}, delta=.1',q(p,p-.1,p-.1)/q(p,p,p),'dc_lr_p'+str(p)[2:]+'_d1',2)
real=[]; sham=[]; ys=[]; solve=[]; numeric=[]; significant=0; tested=0; details=[]
for pid in pids:
    rt=[tag([cells[pid,f,w] for f in families]) for w in range(0,99,3)]
    st=[tag([cells[pid,'base',w+j] for j in range(3)]) for w in range(0,99,3)]
    nr=sum(t in ['NR','R'] for t in rt); ns=sum(t in ['NR','R'] for t in st)
    if nr>=5 and ns>=5:real.append(rate(rt));sham.append(rate(st))
    ev=[tag([cells[pid,f,w] for f in families]) for w in range(0,100,2)]
    if sum(t in ['NR','R'] for t in ev)>=5:ys.append(rate(ev))
    arms=[[r for w in range(100) for r in cells[pid,f,w]] for f in families]
    ps=[sum((r['correct'] or 0) for r in a)/len(a) for a in arms]
    pn=[sum((r['correct'] or 0) for r in a)/sum(r['status']=='numeric' for r in a) for a in arms]
    delta=ps[0]-(ps[1]+ps[2])/2
    se2=ps[0]*(1-ps[0])/400+sum(p*(1-p)/400 for p in ps[1:])/4
    solve.append(delta);numeric.append(pn[0]-(pn[1]+pn[2])/2)
    for pf in ps[1:]:
        se=math.sqrt((ps[0]*(1-ps[0])+pf*(1-pf))/400)
        if se>0:tested+=1;significant+=abs((ps[0]-pf)/se)>1.96
    details.append(dict(pid=pid,delta=delta,se2=se2,maxdrop=max(ps[0]-p for p in ps[1:])))
check('Sham prevalence, mean problem rate',statistics.mean(sham),'sh_false')
check('Real prevalence, mean problem rate',statistics.mean(real),'sh_real')
check('Real minus sham',statistics.mean(real)-statistics.mean(sham),'sh_delta')
check('Sham/real rate ratio',statistics.mean(sham)/statistics.mean(real),'sh_share',2)
check('Observed even-wave fragile rate',statistics.mean(ys),'dc_meanY')
check('Mean all-answer solve drop',statistics.mean(solve),'dc_delta_solve')
check('Mean numeric-only drop',statistics.mean(numeric),'dc_delta_num')
check('Noise-corrected SD',math.sqrt(max(0,statistics.variance(solve)-statistics.mean(r['se2'] for r in details))),'dc_tau_solve')
check('Significant rewrite comparisons',significant,'dc_z_sig',0)
check('Testable rewrite comparisons',tested,'dc_z_tests',0)
check('Largest arm drop',max(r['maxdrop'] for r in details),'dc_top_drop',2)
top=sorted(details,key=lambda r:-r['delta'])[:3]
check('Top three excluded',sum(r['pid'] in dc['excluded'] for r in top),'dc_top3_excluded',0)
# Recombine the pinned output's bias-corrected per-problem estimators;
# this checks aggregation, not a fresh stochastic bias-bootstrap replay.
per=dc['per_original']; m=statistics.mean
null=m(r['N0_base']['corrected'] for r in per);pool=m(r['N0_pool']['corrected'] for r in per);qq=m(r['Q1']['corrected'] for r in per);y=m(ys)
for label,val,key in [('Corrected base null',null,'dc_null'),('Base-only excess',y-null,'dc_E_base'),('Pooled excess',y-pool,'dc_E_pool'),('Excess difference',pool-null,'dc_E_diff'),('Edit component',qq-null,'dc_edit'),('Residual',y-qq,'dc_resid')]:check(label,val,key)
check('Sham calibration',m(sham)-m(q(r['p_b'],r['p_b'],r['p_b']) for r in sh['per_original'] if r['n_real_binary']>=5 and r['n_sham_binary']>=5),'sh_cal')
result=dict(pins='all four producer pins and DRAWS pin match',n_draws=len(rows),n_problems=len(pids),n_sham_used=len(sham),checks=out,top_three=top,limitations='No fresh CI/bootstrap replay; corrected null aggregation uses pinned per-problem corrected estimates.')
(Path(__file__).parent/'NUMBER-CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

