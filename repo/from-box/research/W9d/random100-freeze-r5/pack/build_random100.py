"""CPU-only deterministic exclusive-create build; run on BX, never consumes outcomes."""
import hashlib, json, pathlib, random, sys
from fractions import Fraction
P = pathlib.Path
H = lambda b: hashlib.sha256(b).hexdigest()
C = lambda x: json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
PINS = {'REQUESTS.json':'daccdc4f5f81ff48a3b1567301b0879930f205d08345fae72d9c78a3da20b1d7',
 'TRUTHS.json':'b06a6f45211c2ce08349c60e71020ade450c3d9fa471eba458dc6d245d45d282',
 'ROSTER.json':'b75af74ab88518e448950a49a089ba7d3af67c0aa038406115fc673241d9b05d',
 'MANIFEST.json':'67d42df993ae19f1fefb2be262bb9e1df428abba88774418b7f5085d034360c0'}
PROTOCOL='W9d-random100-fresh-20261026'
SELECT='W9d-random100-cohort-20261026'
ORDER='W9d-random100-order-20261026'
FAMILIES=['base','surface_gs','surface_dlm']
def build(src, out):
    src,out=P(src),P(out); out.mkdir(exist_ok=False)
    data={}
    for n,h in PINS.items():
        b=(src/n).read_bytes(); assert H(b)==h,n; data[n]=json.loads(b)
    roster=data['ROSTER.json']['selected']; assert len(roster)==2657
    pool=[r['problem_id'] for r in roster[:2474]]; assert len(set(pool))==2474
    ids=sorted(pool,key=lambda p:(H((SELECT+'|'+p).encode()),p))[:100]
    cohort=dict(protocol=PROTOCOL, selection_seed=SELECT,pool_size=2474,
                pool_rule='first 2474 of pinned approved reached-prefix roster',selected=ids)
    with (out/'COHORT.json').open('xb') as f:f.write(C(cohort))
    templates={}; truth={}; oldkeys=set()
    for q in data['REQUESTS.json']:
        oldkeys.add(q['identity_sha256']); i=q['identity']; p=i['problem_id']
        if p in ids and i['replicate']==0 and i['family'] in FAMILIES:
            templates[p,i['family']]=q
            truth.setdefault(p,set()).add(str(data['TRUTHS.json'][q['identity_sha256']]))
    ans={r['problem_id']:str(r['answer']) for r in roster}
    assert len(templates)==300 and all(len(truth[p])==1 and Fraction(next(iter(truth[p])))==Fraction(ans[p]) for p in ids)
    reqs=[]; truths={}
    for w in range(28):
        rng=random.Random(ORDER+f'|wave{w}'); ps=ids[:];rng.shuffle(ps)
        for p in ps:
            fams=FAMILIES[:];rng.shuffle(fams)
            for fam in fams:
                q=templates[p,fam]; old=q['identity']
                for r in range(4):
                    ident=dict(protocol=PROTOCOL,model=old['model'],revision=old['revision'],problem_id=p,
                        family=fam,variant_id={'base':'original','surface_gs':'gs','surface_dlm':'dlm'}[fam],
                        replicate=4*w+r,text_sha256=H(q['problem'].encode()))
                    key=H(C(ident));assert key not in oldkeys and key not in truths
                    reqs.append(dict(order_index=len(reqs),wave=w,identity=ident,identity_sha256=key,
                        seed=int(key[:16],16)&((1<<63)-1),system=q['system'],problem=q['problem'],settings=q['settings'],
                        scope='EXPLORATORY_ONLY',production_labels_authorized=False))
                    truths[key]=next(iter(truth[p]))
    assert len(reqs)==33600 and all(q['identity']['protocol']==PROTOCOL for q in reqs)
    for name,obj in [('REQUESTS.json',reqs),('TRUTHS.json',truths)]:
        with (out/name).open('xb') as f:f.write(C(obj))
    orig=data['MANIFEST.json']
    m=dict(protocol=PROTOCOL,scope='EXPLORATORY_ONLY',requests=33600,waves_built=28,waves_planned=25,
        originals=100,families=FAMILIES,draws_per_family_per_wave=4,requests_per_wave=1200,
        request_sha256=H((out/'REQUESTS.json').read_bytes()),truth_sha256=H((out/'TRUTHS.json').read_bytes()),
        cohort_sha256=H((out/'COHORT.json').read_bytes()),settings=orig['settings'],model_revision=orig['model_revision'],
        inference_mode=orig['inference_mode'],max_active=32,max_new_tokens=4096,global_token_cap=35000000,gpu_hour_cap=6.0,
        inputs=PINS,minimum_complete_waves=20)
    with (out/'MANIFEST.json').open('xb') as f:f.write(C(m))
    return m
if __name__=='__main__': print(json.dumps(build(sys.argv[1],sys.argv[2]),indent=2))
