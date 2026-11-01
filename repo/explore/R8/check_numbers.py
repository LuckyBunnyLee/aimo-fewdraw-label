import json, math, collections, statistics, hashlib
from pathlib import Path
P=Path('explore/R8'); checks=[]
def check(name,value,target,digits=3,basis='independent draw/formula recomputation'):
 checks.append(dict(name=name,value=value,target=target,status='MATCH' if round(value,digits)==round(target,digits) else 'MISMATCH',basis=basis))
def q(b,g,d,n=4):
 pm=lambda p,k: math.comb(n,k)*p**k*(1-p)**(n-k)
 s=lambda p,k: sum(pm(p,j) for j in range(k,n+1))
 return sum(pm(b,k)*(1-s(g,k)*s(d,k)) for k in range(1,n+1))/(1-(1-b)**n)
for p,t in [(.5,.55),(.9,.40),(.95,.28),(.99,.07)]: check('N0 n4 p'+str(p),q(p,p,p),t,2)
for n,t in [(1,.19),(16,.55),(64,.61)]: check('N0 p.9 n'+str(n),q(.9,.9,.9,n),t,2)
for p,t in [(.8,1.34),(.9,1.60),(.95,2.25),(.99,7.91)]: check('LR delta .1 p'+str(p),q(p,p-.1,p-.1)/q(p,p,p),t,2)
raw=Path('explore/W9b/ready63rel/out/DRAWS.jsonl').read_bytes(); assert hashlib.sha256(raw).hexdigest()=='e4c66547ecc6ac1aacc9a6921b5611f3e9e183eec7aab6b90e55cf49edaa01b3'
ds=[json.loads(l) for l in raw.splitlines()]; cells=collections.defaultdict(list)
for r in ds: cells[r['pid'],(r['replicate']-1000)//4,r['family']].append(r)
pids=sorted(set(r['pid'] for r in ds)); fams=['base','surface_gs','surface_dlm']
def tag(c):
 if any(r['status']!='numeric' for a in c for r in a): return 'U'
 a=[sum(bool(r['correct']) for r in x) for x in c]
 return 'F' if a[0]==0 else 'NR' if min(a[1:])<a[0] else 'R'
def ts(pid,w): return tag([cells[pid,w,f] for f in fams])
kept=[p for p in pids if sum(ts(p,w) in ('NR','R') for w in range(0,100,2))>=5]
check('draws',len(ds),40800,0); check('problems',len(pids),34,0); check('kept',len(kept),29,0)
ys=[]; real=[]; sham=[]; jr=[]; js=[]; states=collections.Counter(); bins=[0,0]; tops=[]; effects=[]; numeffects=[]; drift=[]
for p in pids:
 arms=[[r for w in range(100) for r in cells[p,w,f]] for f in fams]
 acc=[sum(bool(r['correct']) for r in a)/len(a) for a in arms]
 num=[sum(bool(r['correct']) for r in a)/sum(r['status']=='numeric' for r in a) for a in arms]
 effects.append(acc[0]-(acc[1]+acc[2])/2); numeffects.append(num[0]-(num[1]+num[2])/2)
 tops.append((effects[-1],p,acc,sum(ts(p,w) in ('NR','R') for w in range(0,100,2))))
 drift.append(sum(bool(r['correct']) for w in range(50,100) for r in cells[p,w,'base'])/200-sum(bool(r['correct']) for w in range(50) for r in cells[p,w,'base'])/200)
 if p not in kept: continue
 tags=[ts(p,w) for w in range(0,100,2)]; ys.append(tags.count('NR')/sum(t in ('NR','R') for t in tags))
 pairs=[]
 for w in range(0,99,3):
  a=ts(p,w); b=tag([cells[p,w+i,'base'] for i in range(3)]); pairs.append((a,b)); states[a,b]+=1
 rt=[a for a,b in pairs if a in ('NR','R')]; st=[b for a,b in pairs if b in ('NR','R')]; joint=[(a,b) for a,b in pairs if a in ('NR','R') and b in ('NR','R')]
 bins[0]+=len(rt); bins[1]+=len(st); real.append(rt.count('NR')/len(rt)); sham.append(st.count('NR')/len(st)); jr.append(sum(a=='NR' for a,b in joint)/len(joint)); js.append(sum(b=='NR' for a,b in joint)/len(joint))
m=statistics.mean
for name,v,t in [('observed even',m(ys),.335),('sham own',m(sham),.263),('real own',m(real),.340),('own difference',m(real)-m(sham),.077),('own ratio',m(sham)/m(real),.77),('joint real',m(jr),.343),('joint sham',m(js),.274),('joint difference',m(jr)-m(js),.069),('solve loss',m(effects),.044),('numeric loss',m(numeffects),.012),('solve drift',m(drift),.002)]: check(name,v,t,2 if 'ratio' in name else 3)
check('real binary triples',bins[0],733,0); check('sham binary triples',bins[1],824,0)
for a,b,t in [('NR','NR',102),('NR','R',121),('R','NR',64),('R','R',396)]: check('joint cell '+a+'/'+b,states[a,b],t,0)
check('joint total',sum(states[a,b] for a in ['NR','R'] for b in ['NR','R']),683,0)
for i,(loss,p,acc,nb) in enumerate(sorted(tops,reverse=True)[:3]):
 check('top harm binary waves '+str(i+1),nb,[0,1,4][i],0)
 if i==0:
  check('top mean harm',loss,.52,2)
  for f,v,t in zip(fams,acc,[1,.08,.89]): check('top accuracy '+f,v,t,2)
# Reaggregate stored bias corrections; do not claim an independent bootstrap replay.
dc=json.loads(Path('explore/W9b/decomp/RESULT.json').read_text()); rows=dc['per_original']
for name,v,t in [('base excess',m(r['Y']-r['N0_base']['corrected'] for r in rows),.077),('pooled excess',m(r['Y']-r['N0_pool']['corrected'] for r in rows),.042),('null component',m(r['N0_base']['corrected'] for r in rows),.258),('edit component',m(r['Q1']['corrected']-r['N0_base']['corrected'] for r in rows),.060),('residual',m(r['Y']-r['Q1']['corrected'] for r in rows),.016)]: check(name,v,t,basis='reaggregation of stored corrected per-problem values; not independent bootstrap')
(P/'NUMBER-CHECKS.json').write_text(json.dumps(dict(checks=checks,top3=sorted(tops,reverse=True)[:3]),indent=2))
print('\n'.join(f"{c['status']} {c['name']}: {c['value']:.9g} vs {c['target']}" for c in checks)); print('TOTAL',len(checks))
