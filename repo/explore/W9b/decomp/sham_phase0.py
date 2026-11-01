"""SHAM Phase 0 (CPU, READY63 draws, run once). Implements SHAM-SPEC-20261025.md Phase 0.
Usage: python sham_phase0.py selftest | run"""
import json, hashlib, pathlib, sys, collections
import numpy as np
EX = pathlib.Path(r'E:\work\research-cycle\explore'); OUT = EX / 'W9b/decomp'
HF = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
DRAWS = (EX / 'W9b/ready63rel/out/DRAWS.jsonl', 'e4c66547ecc6ac1aacc9a6921b5611f3e9e183eec7aab6b90e55cf49edaa01b3')
sys.path.insert(0, str(EX / 'X3')); import fresh81_pure as f
sys.path.insert(0, str(OUT)); from decomp import N0
B, SEED = 2000, 20261025

def cell(ds): return [dict(status=d['status'], correct=d['correct'] or 0) for d in sorted(ds, key=lambda d: d['replicate'])]
def analyse(draws, rng):
    by = collections.defaultdict(list)
    for d in draws: by[(d['pid'], (d['replicate'] - 1000) // 4, d['family'])].append(d)
    rows = []
    for pid in sorted({k[0] for k in by}):
        real, sham = [], []
        for t in range(33):
            a, b, c = 3 * t, 3 * t + 1, 3 * t + 2
            real.append(f.tag(dict(base=cell(by[(pid, a, 'base')]), surface_gs=cell(by[(pid, a, 'surface_gs')]), surface_dlm=cell(by[(pid, a, 'surface_dlm')])), 4))
            sham.append(f.tag(dict(base=cell(by[(pid, a, 'base')]), surface_gs=cell(by[(pid, b, 'base')]), surface_dlm=cell(by[(pid, c, 'base')])), 4))
        bn = [d for w in range(100) for d in by[(pid, w, 'base')] if d['status'] == 'numeric']
        pb = float(np.mean([d['correct'] == 1 for d in bn])) if bn else float('nan')
        rb, sb = [x for x in real if x in ('NR', 'R')], [x for x in sham if x in ('NR', 'R')]
        rows.append(dict(pid=pid, p_b=pb, N0=N0(pb) if pb > 0 else None, n_real_binary=len(rb), n_sham_binary=len(sb),
                         nr_real=rb.count('NR') / len(rb) if rb else None, nr_sham=sb.count('NR') / len(sb) if sb else None,
                         real_counts=dict(collections.Counter(real)), sham_counts=dict(collections.Counter(sham))))
    use = [r for r in rows if r['n_real_binary'] >= 5 and r['n_sham_binary'] >= 5]; n = len(use)
    R = np.array([r['nr_real'] for r in use]); S = np.array([r['nr_sham'] for r in use]); Z = np.array([r['N0'] for r in use])
    def m(x):
        bt = [float(x[rng.integers(0, n, n)].mean()) for _ in range(B)]
        return dict(est=float(x.mean()), ci95=np.quantile(bt, [.025, .975]).tolist())
    ratio_bt = []
    for _ in range(B):
        ix = rng.integers(0, n, n); ratio_bt.append(S[ix].mean() / R[ix].mean())
    p03 = m(S - Z)
    return dict(n_originals=len(rows), n_used=n, excluded=[r['pid'] for r in rows if r not in use],
                P0_1_false_fragility=m(S), mean_real_NR=m(R), P0_2_delta=m(R - S),
                P0_2_sham_share_of_real=dict(est=float(S.mean() / R.mean()), ci95=np.quantile(ratio_bt, [.025, .975]).tolist()),
                P0_3_sham_minus_N0=p03, P0_3_calibrated_within_0_03=bool(-0.03 < p03['ci95'][0] and p03['ci95'][1] < 0.03),
                mean_N0=float(Z.mean()), per_original=rows)

def selftest():
    rng = np.random.default_rng(3); draws = []
    for i in range(34):
        p = rng.uniform(0.6, 0.99); dl = 0.1 if i % 2 else 0.0
        for fm in ('base', 'surface_gs', 'surface_dlm'):
            pf = p if fm == 'base' else p - dl
            for r in range(1000, 1400): draws.append(dict(pid=f's{i}', family=fm, replicate=r, status='numeric', correct=int(rng.random() < pf)))
    global B; B = 200
    res = analyse(draws, np.random.default_rng(1))
    assert res['P0_3_sham_minus_N0']['ci95'][0] < 0 < res['P0_3_sham_minus_N0']['ci95'][1], res['P0_3_sham_minus_N0']
    assert res['P0_2_delta']['ci95'][0] > 0, res['P0_2_delta']
    print('selftest ok', {k: round(res[k]['est'], 4) for k in ('P0_1_false_fragility', 'mean_real_NR', 'P0_2_delta', 'P0_3_sham_minus_N0')})

def run():
    for line in (OUT / 'SHAM-FREEZE.sha256').read_text().splitlines():
        h, p = line.split(None, 1); assert HF(OUT / p.strip()) == h, ('freeze', p)
    assert HF(DRAWS[0]) == DRAWS[1], 'input hash'
    out = OUT / 'SHAM-PHASE0-RESULT.json'; assert not out.exists(), 'single execution'
    draws = [json.loads(l) for l in open(DRAWS[0], encoding='utf-8')]
    res = dict(freeze_sha256=HF(OUT / 'SHAM-FREEZE.sha256'), script_sha256=HF(__file__), input_sha256=DRAWS[1], **analyse(draws, np.random.default_rng(SEED)))
    out.write_text(json.dumps(res, indent=1, default=float)); print(HF(out))
    print({k: res[k] for k in ('n_used', 'P0_1_false_fragility', 'mean_real_NR', 'P0_2_delta', 'P0_2_sham_share_of_real', 'P0_3_sham_minus_N0', 'P0_3_calibrated_within_0_03', 'mean_N0', 'excluded')})

if __name__ == '__main__':
    selftest() if sys.argv[1] == 'selftest' else run()
