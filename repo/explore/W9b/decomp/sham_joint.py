"""SHAM joint-eligibility sensitivity (W9b, 25 Oct 2026; R7 referee must-fixes 1, 3/G13, 5). Exploratory, post hoc, CPU, runs once.
Reads existing draws only; correctness is read as stored (no regrading); tags use the frozen fresh81_pure.tag.
(a) Joint: the SHAM Phase 0 triples (waves 3t, 3t+1, 3t+2; t = 0..32), kept only where BOTH the real and the sham tag are binary.
    Problems: the 29 used by Phase 0 with >= 5 jointly binary triples. Per problem NR share among joint triples, real and sham;
    mean real, mean sham, mean(real - sham), ratio of means; 95% problem bootstrap (2,000, seed 20261025) and template-cluster bootstrap for the difference.
    Plus the real-state x sham-state table over all 33 triples of the 29 problems.
(b) Drift: requests were queued wave-major (REQUESTS.json order), so wave index tracks time. Per problem, base all-answer solve rate and numeric rate
    in waves 50-99 minus waves 0-49; mean over the 34 problems with a problem bootstrap. Same for the sham NR share, triples 17-32 minus 0-16 (29 problems).
(c) Second-wave AUC (DECOMP S1): rebuild y, base-only N0 and pooled N0 exactly as decomp.fresh6h_S1, assert the stored AUCs, then report the base-only AUC
    with the undefined-N0 problems (base 0/4 correct, scored 1.0 in S1) excluded, with a bootstrap CI.
usage: python -I explore/W9b/decomp/sham_joint.py selftest | run"""
import json, hashlib, pathlib, sys, collections
import numpy as np
EX = pathlib.Path(r'E:\work\research-cycle\explore'); W = EX / 'W9b'; OUT = W / 'decomp'
sys.path.insert(0, str(EX / 'X3')); import fresh81_pure as f
sys.path.insert(0, str(OUT)); import decomp as dm
HF = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
PIN = {W / 'ready63rel/out/DRAWS.jsonl': 'e4c66547ecc6ac1aacc9a6921b5611f3e9e183eec7aab6b90e55cf49edaa01b3',
       EX / 'X3/READY63-reviewed-MATH-20261020/MEMBERS-WITH-PROOFS.json': '1b27513c326e7c084c95f5921123d0c957764865804bc3e926b61e483954756d',
       EX / 'X3/fresh81_pure.py': '6b9c0e124f4d690c6bd1412aeccfdc8d12b8b20fb2ebe3d0576656c0b59f1e4d',
       W / 'fresh6h/out/PER-ORIGINAL.jsonl': '0e6a6657b948e78a088bd83d6fc5174ee4f4c239b3e6e110dd54358cd52ed49e',
       W / 'fresh6h/out/DRAWS.jsonl': '3c7bafdb25199f6fe44dbeb0c22c47954a386c01c7a147164aecf7dc8fdeaaf9',
       OUT / 'SHAM-PHASE0-RESULT.json': '7cbdc2f0c899ea72ad40e5726c6f8dde1d627f00e4e027572feeece3b92d7b91',
       OUT / 'RESULT.json': 'f70423eb7b03d70ac5252fdaee8464705b802cd0a3dc8b3d66127d3bb12ace0f',
       OUT / 'decomp.py': 'a37aebe72f582fd24ff9353ea273ed05abe70cf2ab6f5b1efff0a9bf85bb6929',
       EX / 'CL-5070-recovery-20261020-1740/ready63-reliability/REQUESTS.json': '3964f3fada3a925e2875869718d06fde776f31cf65a0e7609435b55393bc76d1'}
B, SEED = 2000, 20261025
STATES = ('NR', 'R', 'UNUSABLE', 'FLOOR')


def cell(ds): return [dict(status=d['status'], correct=d['correct'] or 0) for d in sorted(ds, key=lambda d: d['replicate'])]


def boot(fn, n, rng, groups=None):
    out, ug = [], None if groups is None else sorted(set(groups))
    for _ in range(B):
        ix = rng.integers(0, n, n) if groups is None else np.concatenate([np.where(groups == g)[0] for g in rng.choice(ug, len(ug), replace=True)])
        v = fn(ix)
        if v is not None and np.isfinite(v): out.append(v)
    return dict(ci95=np.quantile(out, [.025, .975]).tolist(), valid=len(out))


def joint(draws, used, tmpl, rng):
    by = collections.defaultdict(list)
    for d in draws: by[(d['pid'], (d['replicate'] - 1000) // 4, d['family'])].append(d)
    rows, xt = [], collections.Counter()
    for pid in used:
        pairs = []
        for t in range(33):
            a, b, c = 3 * t, 3 * t + 1, 3 * t + 2
            r = f.tag(dict(base=cell(by[(pid, a, 'base')]), surface_gs=cell(by[(pid, a, 'surface_gs')]), surface_dlm=cell(by[(pid, a, 'surface_dlm')])), 4)
            s = f.tag(dict(base=cell(by[(pid, a, 'base')]), surface_gs=cell(by[(pid, b, 'base')]), surface_dlm=cell(by[(pid, c, 'base')])), 4)
            pairs.append((r, s)); xt[(r, s)] += 1
        jb = [(r, s) for r, s in pairs if r in ('NR', 'R') and s in ('NR', 'R')]
        sb = [(t, s) for t, (r, s) in enumerate(pairs) if s in ('NR', 'R')]
        early, late = [s for t, s in sb if t <= 16], [s for t, s in sb if t >= 17]
        rows.append(dict(pid=pid, template=tmpl[pid], n_joint=len(jb), real_counts=dict(collections.Counter(r for r, _ in pairs)),
                         sham_counts=dict(collections.Counter(s for _, s in pairs)),
                         nr_real=sum(r == 'NR' for r, _ in jb) / len(jb) if jb else None, nr_sham=sum(s == 'NR' for _, s in jb) / len(jb) if jb else None,
                         sham_nr_early=early.count('NR') / len(early) if early else None, sham_nr_late=late.count('NR') / len(late) if late else None))
    use = [r for r in rows if r['n_joint'] >= 5]; n = len(use)
    R = np.array([r['nr_real'] for r in use]); S = np.array([r['nr_sham'] for r in use]); G = np.array([r['template'] for r in use])
    mean_ci = lambda x: dict(est=float(x.mean()), ci_original=boot(lambda ix: float(x[ix].mean()), n, rng), ci_template=boot(lambda ix: float(x[ix].mean()), n, rng, G))
    el = [r for r in rows if r['sham_nr_early'] is not None and r['sham_nr_late'] is not None]
    dl = np.array([r['sham_nr_late'] - r['sham_nr_early'] for r in el])
    return dict(n_considered=len(rows), n_used=n, excluded=[r['pid'] for r in rows if r['n_joint'] < 5], n_joint_triples=int(sum(r['n_joint'] for r in use)),
                n_joint_triples_all29=int(sum(r['n_joint'] for r in rows)), n_templates_used=len(set(G)),
                real=mean_ci(R), sham=mean_ci(S), real_minus_sham=mean_ci(R - S),
                ratio_sham_over_real=dict(est=float(S.mean() / R.mean()), ci_original=boot(lambda ix: float(S[ix].mean() / R[ix].mean()), n, rng)),
                state_table={f'{r}|{s}': xt[(r, s)] for r in STATES for s in STATES}, n_triples_all=sum(xt.values()),
                sham_drift_late_minus_early=dict(n=len(el), **mean_ci_simple(dl, rng)), per_original=rows)


def mean_ci_simple(x, rng):
    return dict(est=float(x.mean()), ci_original=boot(lambda ix: float(x[ix].mean()), len(x), rng))


def drift(draws, rng):
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    for d in draws:
        if d['family'] == 'base': by[d['pid']][((d['replicate'] - 1000) // 4) >= 50].append(d)
    ds, dn = [], []
    for pid in sorted(by):
        e, l = by[pid][False], by[pid][True]; assert len(e) == len(l) == 200
        sr = lambda x: np.mean([d['status'] == 'numeric' and d['correct'] == 1 for d in x]); nr = lambda x: np.mean([d['status'] == 'numeric' for d in x])
        ds.append(sr(l) - sr(e)); dn.append(nr(l) - nr(e))
    ds, dn = np.array(ds), np.array(dn)
    return dict(n=len(ds), base_solve_late_minus_early=mean_ci_simple(ds, rng), base_numeric_late_minus_early=mean_ci_simple(dn, rng))


def order_check(reqs):
    """Mean queue position of each wave's requests: wave-major order means it rises with the wave index."""
    pos = collections.defaultdict(list)
    for q in reqs: pos[(q['identity']['replicate'] - 1000) // 4].append(q['order_index'])
    m = [float(np.mean(pos[w])) for w in range(100)]
    return dict(waves=len(pos), per_wave_requests=sorted({len(v) for v in pos.values()}), wave_major=bool(all(max(pos[w]) < min(pos[w + 1]) for w in range(99))),
                first_wave_mean_pos=m[0], last_wave_mean_pos=m[-1])


def s1_sensitivity(po, fdraws, stored, rng):
    w2 = collections.defaultdict(lambda: collections.defaultdict(list))
    for d in fdraws:
        if d['src'] == 'continuation' and d['replicate'] >= 4: w2[d['pid']][d['family']].append(d)
    ys, nb, npool = [], [], []
    for p, x in po.items():
        if not (x.get('D1') and x['D1'].get('reached') and x['D1']['strict'] in ('NR', 'R') and x.get('W2')): continue
        if not all(len(w2[p][fm]) == 4 for fm in dm.FAMS): continue
        cn = {fm: [d['correct'] == 1 for d in w2[p][fm] if d['status'] == 'numeric'] for fm in dm.FAMS}
        if not cn['base']: continue
        pb = float(np.mean(cn['base'])); pp = sum(map(sum, cn.values())) / sum(map(len, cn.values()))
        ys.append(int(x['D1']['strict'] == 'NR')); nb.append(dm.N0(pb)); npool.append(dm.N0(pp))
    y, a, b = np.array(ys), np.array(nb), np.array(npool)
    und = np.isnan(a); a1 = np.nan_to_num(a, nan=1.0)
    assert len(y) == stored['n'] and abs(f.auc(y, a1) - stored['auc_base']) < 1e-12 and abs(f.auc(y, b) - stored['auc_pool']) < 1e-12
    assert int(und.sum()) == stored['base_zero_of_4'] and not np.isnan(b).any()
    k = ~und; yk, ak, bk = y[k], a[k], b[k]
    return dict(n=int(len(y)), n_undefined=int(und.sum()), undefined_y=[int(v) for v in y[und]],
                auc_base_scored1=float(f.auc(y, a1)), auc_base_excl=float(f.auc(yk, ak)), auc_base_excl_ci=boot(lambda ix: f.auc(yk[ix], ak[ix]), int(k.sum()), rng),
                auc_pool_excl=float(f.auc(yk, bk)), auc_base_scored0=float(f.auc(y, np.nan_to_num(a, nan=0.0))))


def selftest():
    rng = np.random.default_rng(3); draws = []
    for i in range(12):
        p = rng.uniform(0.7, 0.95)
        for fm in dm.FAMS:
            for r in range(1000, 1400): draws.append(dict(pid=f's{i}', family=fm, replicate=r, status='numeric', correct=int(rng.random() < p)))
    global B; B = 100
    res = joint(draws, [f's{i}' for i in range(12)], {f's{i}': f't{i % 4}' for i in range(12)}, np.random.default_rng(1))
    lo, hi = res['real_minus_sham']['ci_original']['ci95']; assert lo < 0 < hi, (lo, hi)
    assert res['n_triples_all'] == 12 * 33 and res['state_table']['UNUSABLE|UNUSABLE'] == 0
    dr = drift(draws, np.random.default_rng(2)); lo, hi = dr['base_solve_late_minus_early']['ci_original']['ci95']; assert lo < 0 < hi
    print('selftest ok', round(res['real_minus_sham']['est'], 4), res['n_used'], round(dr['base_solve_late_minus_early']['est'], 4))
    B = 2000


def run():
    for p, h in PIN.items(): assert HF(p) == h, ('input hash', p)
    out = OUT / 'SHAM-JOINT-RESULT.json'; assert not out.exists(), 'single execution'
    rng = np.random.default_rng(SEED)
    draws = [json.loads(l) for l in open(W / 'ready63rel/out/DRAWS.jsonl', encoding='utf-8')]
    members = json.loads((EX / 'X3/READY63-reviewed-MATH-20261020/MEMBERS-WITH-PROOFS.json').read_text(encoding='utf-8'))
    tmpl = {m['problem_id']: m['template_family'] for m in members}
    sh = json.loads((OUT / 'SHAM-PHASE0-RESULT.json').read_text(encoding='utf-8'))
    used = sorted(r['pid'] for r in sh['per_original'] if r['pid'] not in set(sh['excluded'])); assert len(used) == 29
    res = dict(script_sha256=HF(__file__), inputs={str(p): h for p, h in PIN.items()},
               n_templates_all34=len(set(tmpl.values())), n_templates_used29=len({tmpl[p] for p in used}))
    res['joint'] = joint(draws, used, tmpl, rng)
    for r in res['joint']['per_original']:  # Phase 0's per-original state counts must be reproduced exactly
        p0 = [x for x in sh['per_original'] if x['pid'] == r['pid']][0]
        assert r['real_counts'] == p0['real_counts'] and r['sham_counts'] == p0['sham_counts'], r['pid']
    res['drift'] = drift(draws, rng)
    res['order'] = order_check(json.loads((EX / 'CL-5070-recovery-20261020-1740/ready63-reliability/REQUESTS.json').read_text(encoding='utf-8')))
    po = {x['pid']: x for x in map(json.loads, open(W / 'fresh6h/out/PER-ORIGINAL.jsonl', encoding='utf-8'))}
    fd = [json.loads(l) for l in open(W / 'fresh6h/out/DRAWS.jsonl', encoding='utf-8')]
    res['s1'] = s1_sensitivity(po, fd, json.loads((OUT / 'RESULT.json').read_text(encoding='utf-8'))['S1'], rng)
    with open(out, 'x', encoding='utf-8') as fh: json.dump(res, fh, indent=1, default=float)
    print(HF(out))
    j = res['joint']
    print({k: j[k] for k in ('n_used', 'excluded', 'n_joint_triples', 'n_templates_used')}, {k: j[k]['est'] for k in ('real', 'sham', 'real_minus_sham', 'ratio_sham_over_real')},
          j['real_minus_sham']['ci_original'], j['real_minus_sham']['ci_template'])
    print(j['state_table']); print(j['sham_drift_late_minus_early']); print(res['drift']); print(res['order']); print({k: v for k, v in res['s1'].items()})


if __name__ == '__main__':
    selftest() if sys.argv[1] == 'selftest' else run()
