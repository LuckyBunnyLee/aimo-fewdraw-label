"""R7 independent, light stdlib checks. No bootstrap, model, or upstream execution."""
import collections, hashlib, json, math, statistics
from pathlib import Path

ROOT = Path('E:/work/research-cycle')
OUT = ROOT / 'explore/R7'
load = lambda p: json.loads((ROOT / p).read_text(encoding='utf-8-sig'))
dc = load('explore/W9b/decomp/RESULT.json')
sh = load('explore/W9b/decomp/SHAM-PHASE0-RESULT.json')
values = {}
for name in ('w9b-t084', 'w9b-t086'):
    values.update(load('pair/aimo/report/numbers/' + name + '.json')['values'])
pins = {}
for path, expected in dc['inputs'].items():
    if path.endswith('DRAWS.jsonl') and 'ready63rel' in path:
        data = Path(path).read_bytes()
        pins[path] = dict(expected=expected, actual=hashlib.sha256(data).hexdigest())
        draws = [json.loads(line) for line in data.splitlines()]
for path, expected in [('explore/W9b/decomp/RESULT.json','f70423eb7b03d70ac5252fdaee8464705b802cd0a3dc8b3d66127d3bb12ace0f'),('explore/W9b/decomp/SHAM-PHASE0-RESULT.json','7cbdc2f0c899ea72ad40e5726c6f8dde1d627f00e4e027572feeece3b92d7b91')]:
    pins[path] = dict(expected=expected, actual=hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
assert all(v['actual']==v['expected'] for v in pins.values())

def q(pb, pg, pd, n=4):
    mass = lambda p: [math.comb(n,k)*p**k*(1-p)**(n-k) for k in range(n+1)]
    b,g,d = mass(pb),mass(pg),mass(pd)
    return sum(b[k]*(1-sum(g[k:])*sum(d[k:])) for k in range(1,n+1))/(1-(1-pb)**n)

checks=[]
def check(key, actual, digits=None, basis='independent draw aggregation/formula'):
    printed=values[key]
    rounded=round(actual,digits) if digits is not None else actual
    checks.append(dict(key=key,actual=actual,printed=printed,status='MATCH' if rounded==printed else 'MISMATCH',basis=basis))

fams=('base','surface_gs','surface_dlm')
cells=collections.defaultdict(list)
by=collections.defaultdict(list)
for d in draws:
    cells[d['pid'],(d['replicate']-1000)//4,d['family']].append(d)
    by[d['pid']].append(d)
assert len(draws)==40800 and all(len(x)==4 for x in cells.values())
def tag(arms):
    if any(d['status']!='numeric' for a in arms for d in a): return 'UNUSABLE'
    b,g,d=[sum(x['correct']==1 for x in a) for a in arms]
    if b==0: return 'FLOOR'
    return 'NR' if min(g,d)<b else 'R'
def acc(ds, numeric=False):
    ds=[d for d in ds if not numeric or d['status']=='numeric']
    return sum(d['status']=='numeric' and d['correct']==1 for d in ds)/len(ds)
rows=[]
for pid,ds in sorted(by.items()):
    even=[tag([cells[pid,w,f] for f in fams]) for w in range(0,100,2)]
    eb=[t for t in even if t in ('R','NR')]
    real=[tag([cells[pid,3*t,f] for f in fams]) for t in range(33)]
    sham=[tag([cells[pid,3*t+j,'base'] for j in range(3)]) for t in range(33)]
    rb=[t for t in real if t in ('R','NR')]; sb=[t for t in sham if t in ('R','NR')]
    allp=[acc([d for d in ds if d['family']==f]) for f in fams]
    nump=[acc([d for d in ds if d['family']==f],True) for f in fams]
    oddp=[acc([d for d in ds if d['family']==f and (d['replicate']-1000)//4%2],True) for f in fams]
    se2=allp[0]*(1-allp[0])/400+sum(p*(1-p)/400 for p in allp[1:])/4
    rows.append(dict(pid=pid,ne=len(eb),Y=eb.count('NR')/len(eb) if eb else None,real=real,sham=sham,nr=len(rb),ns=len(sb),R=rb.count('NR')/len(rb) if rb else None,S=sb.count('NR')/len(sb) if sb else None,p=allp,pn=nump,odd=oddp,delta=allp[0]-sum(allp[1:])/2,dn=nump[0]-sum(nump[1:])/2,se2=se2))
used=[r for r in rows if r['ne']>=5]
su=[r for r in rows if min(r['nr'],r['ns'])>=5]
assert {r['pid'] for r in used}=={r['pid'] for r in su}
mean=statistics.mean
check('dc_n_originals',len(rows)); check('dc_n_used',len(used));check('sh_n_used',len(su))
check('dc_even_bin_min',min(r['ne'] for r in used));check('dc_even_bin_max',max(r['ne'] for r in used))
check('dc_meanY',mean(r['Y'] for r in used),3)
check('sh_false',mean(r['S'] for r in su),3);check('sh_real',mean(r['R'] for r in su),3)
check('sh_delta',mean(r['R']-r['S'] for r in su),3)
check('sh_share',mean(r['S'] for r in su)/mean(r['R'] for r in su),2)
check('sh_cal',mean(r['S']-q(r['pn'][0],r['pn'][0],r['pn'][0]) for r in su),3)
check('sh_bin_real',sum(r['nr'] for r in su));check('sh_bin_sham',sum(r['ns'] for r in su))
check('sh_n_fewer_real',sum(r['nr']<r['ns'] for r in su));check('sh_triples_all',33*len(su))
for arm,field in [('real','real'),('sham','sham')]:
    for state in ['UNUSABLE','NR']:
        check('sh_state_'+arm+'_'+state.lower(),100*sum(r[field].count(state) for r in su)/(33*len(su)),1)
check('dc_delta_solve',mean(r['delta'] for r in rows),3)
check('dc_delta_num',mean(r['dn'] for r in rows),3)
check('dc_tau_solve',math.sqrt(max(0,statistics.variance(r['delta'] for r in rows)-mean(r['se2'] for r in rows))),3)
zs=[]
for r in rows:
    b=r['p'][0]
    for f in r['p'][1:]:
        v=(b*(1-b)+f*(1-f))/400
        if v>0: zs.append((b-f)/math.sqrt(v))
check('dc_z_tests',len(zs));check('dc_z_sig',sum(abs(z)>1.96 for z in zs))
check('dc_z_expected',len(zs)*.05,1)
top=sorted(rows,key=lambda r:-r['delta'])[:3]
check('dc_top_mean_drop',top[0]['delta'],2);check('dc_top3_min_mean_drop',top[-1]['delta'],2)
check('dc_top3_excluded',sum(r['ne']<5 for r in top));check('dc_top_drop',max(r['p'][0]-min(r['p'][1:]) for r in rows),2)
for p in [.5,.9,.95,.99]:check('dc_n0_p'+str(p)[2:],q(p,p,p),2,'independent finite binomial sum')
for n in [1,4,16,64]:check('dc_n0_p9_n'+str(n),q(.9,.9,.9,n),2,'independent finite binomial sum')
for p in [.8,.9,.95,.99]:check('dc_lr_p'+str(p)[2:]+'_d1',q(p,p-.1,p-.1)/q(p,p,p),2,'independent finite binomial sum')
# Corrected results are checked by aggregating pinned per-problem corrections,
# not by independently rerunning the costly parametric bootstrap.
cr=dc['per_original']
check('dc_E_base',mean(r['Y']-r['N0_base']['corrected'] for r in cr),3,'pinned corrected per-problem outputs; bootstrap not rerun')
check('dc_E_pool',mean(r['Y']-r['N0_pool']['corrected'] for r in cr),3,'pinned corrected per-problem outputs; bootstrap not rerun')
check('dc_E_diff',mean(r['N0_pool']['corrected']-r['N0_base']['corrected'] for r in cr),3,'pinned corrected per-problem outputs; bootstrap not rerun')
for key,fn in [('null',lambda r:r['N0_base']['corrected']),('edit',lambda r:r['Q1']['corrected']-r['N0_base']['corrected']),('resid',lambda r:r['Y']-r['Q1']['corrected'])]:
    check('dc_'+key,mean(fn(r) for r in cr),3,'pinned corrected per-problem outputs; bootstrap not rerun')
out=dict(n_draws=len(draws),pins=pins,checks=checks,top3=[dict(pid=r['pid'],delta=r['delta'],n_even_binary=r['ne']) for r in top],limitations='No bootstrap CIs independently rerun; corrected components only reaggregated. No earlier referee material read.')
(OUT/'NUMBER-CHECKS.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(dict(n_draws=len(draws),checks=len(checks),mismatches=[c for c in checks if c['status']!='MATCH']),indent=2))
for c in checks:print(c['key'],format(c['actual'],'.10g'),c['printed'],c['status'])
