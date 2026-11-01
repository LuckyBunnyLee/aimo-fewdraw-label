"""AR2 numbers (t106) for report v1.3: the second referee's post hoc analyses (a)-(c) on the SHAM Phase 1 draws
(REFEREE2-v1.2c-AR1.md, "Proposed post hoc analyses"). All [E-post], appendix only; none touches a frozen reading.
Run after the BR2 blind replay matched the first score (lead, 27 Oct), so the inputs are replayed data.
- Per-problem rows are rebuilt with the frozen scorer's own analyse() from the scorer's DRAWS.jsonl (sha 86e0aca0, as in
  the box DONE.json); the rebuild must reproduce RESULT.json's PRIMARY, CAL2 and T4 point estimates exactly.
- (a) PRIMARY split exactly into a numeric-rate part and an accuracy-among-numeric part (midpoint identity, per problem:
  n_S a_S - n_R a_R = (n_S - n_R)(a_S + a_R)/2 + (a_S - a_R)(n_S + n_R)/2; real = gs+dlm pooled, sham = sham_a+sham_b pooled;
  an arm with no numeric answer takes the other arm's accuracy, so its whole difference is numeric-rate).
- (b) T4 with N0 bias-corrected by parametric bootstrap (decomp.corrected, Appendix B), same T2 problems; and CAL2's share
  restricted to problems with all-answer base solve rate >= 0.9 (near the ceiling).
- (c) Prospective reliability: Fleiss kappa of the real and of the sham label over the 12 waves (problems with >= 2 binary
  waves); split-half (even vs odd waves) Pearson r with Spearman-Brown 2r/(1+r) for the per-problem solve change (all 320)
  and the real and the sham label's fragile rate (problems with >= 2 binary waves in each half). Intervals resample problems, B = 2000.
Writes numbers/ar2-t106.json (exclusive create). usage: python -I pair/aimo/report/numbers/make_ar2_t106.py
"""
import collections, hashlib, json, sys
from pathlib import Path
import numpy as np

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
OUT = 'from-box/research/W9d/sham1-score/tree/explore/W9b/sham1/v1.1/out/'
RES, DRW = OUT + 'RESULT.json', OUT + 'DRAWS.jsonl'
SCO, DEC, F81 = 'explore/W9b/sham1/v1.1/score_phase1.py', 'explore/W9b/decomp/decomp.py', 'explore/X3/fresh81_pure.py'
manifest, raw = {}, {}
for rel in (RES, DRW, SCO, DEC, F81):
    p = ROOT / rel; b = p.read_bytes(); manifest[str(p)] = hashlib.sha256(b).hexdigest(); raw[rel] = b
assert manifest[str(ROOT / DRW)] == '86e0aca09bcca52f737b48cc28961808f92cb14e002fba91afe1033c77e5804e'
r = json.loads(raw[RES].decode('utf-8-sig'))
assert r['scorer_sha256'] == manifest[str(ROOT / SCO)]
sys.path.insert(0, str(ROOT / 'explore/W9b/sham1/v1.1')); import score_phase1 as sp
from decomp import corrected, fleiss
draws = [json.loads(line) for line in raw[DRW].decode('utf-8').splitlines() if line.strip()]
fresh = {row['pid']: row['fresh6h'] for row in r['per_original']}
res, rows = sp.analyse(draws, fresh, np.random.default_rng(sp.SEED))
# local numpy/scipy differ from the box's, so N0 can differ in the last bit; everything else must match exactly
close = lambda a, b: np.allclose(np.asarray(a, float), np.asarray(b, float), rtol=0, atol=1e-12)
for k in ('PRIMARY_solve_vs_sham', 'T4_sham_minus_N0'): assert close(res[k]['est'], r[k]['est']) and close(res[k]['ci95'], r[k]['ci95']), k
assert res['CAL2_sham_z'] == r['CAL2_sham_z'] and len(rows) == len(r['per_original'])
for a, b in zip(rows, r['per_original']):
    assert {k: x for k, x in a.items() if k != 'N0'} == {k: x for k, x in b.items() if k != 'N0'} and (a['N0'] is None) == (b['N0'] is None)
    assert a['N0'] is None or abs(a['N0'] - b['N0']) < 1e-12

rng = np.random.default_rng(20261027); B = 2000


def boot(x):
    x = np.asarray(x, float); n = len(x)
    return float(x.mean()), np.quantile([x[rng.integers(0, n, n)].mean() for _ in range(B)], [.025, .975]).tolist()


cells = collections.defaultdict(list)
for d in draws: cells[(d['pid'], d['family'])].append(d)
REAL, SHAM = ('surface_gs', 'surface_dlm'), ('sham_a', 'sham_b')

# (a) split of the primary
num_part, acc_part, dnum, dacc, total = [], [], [], [], []
for row in rows:
    arm = {}
    for name, fams in (('R', REAL), ('S', SHAM)):
        ds = [d for f in fams for d in cells[(row['pid'], f)]]; num = [d for d in ds if d['status'] == 'numeric']
        arm[name] = (len(num) / len(ds), (sum(d['correct'] for d in num) / len(num)) if num else None)
    (nR, aR), (nS, aS) = arm['R'], arm['S']
    if aR is None and aS is None: aR = aS = 0.0
    elif aR is None: aR = aS
    elif aS is None: aS = aR
    num_part.append((nS - nR) * (aS + aR) / 2); acc_part.append((aS - aR) * (nS + nR) / 2); dnum.append(nS - nR); dacc.append(aS - aR)
    total.append(row['delta_vs_sham'])
assert np.allclose(np.add(num_part, acc_part), total, atol=1e-12)

# (b) bias-corrected T4 and CAL2 near the ceiling
O = [row for row in rows if row['n_real_bin'] >= sp.MIN_OWN and row['n_sham_bin'] >= sp.MIN_OWN and row['N0'] is not None]
assert len(O) == r['T4_sham_minus_N0']['n']
cache = {}
def N0c(p): return cache.setdefault(p, sp.N0(p))
t4bc, n0bc = [], []
for row in O:
    m = sum(1 for d in cells[(row['pid'], 'base')] if d['status'] == 'numeric')
    c = corrected(N0c, [row['p_b_numeric']], [m], rng)
    assert abs(c['plug'] - row['N0']) < 1e-12
    n0bc.append(c['corrected']); t4bc.append(row['nr_sham_own'] - c['corrected'])
n = 4 * r['waves']; zs = []
for row in rows:
    if row['p_base'] < 0.9: continue
    for a, b in (('base', 'sham_a'), ('base', 'sham_b'), ('sham_a', 'sham_b')):
        pa, pb = row['p_' + a], row['p_' + b]; se = (pa * (1 - pa) / n + pb * (1 - pb) / n) ** .5
        if se > 0: zs.append((pa - pb) / se)

# (c) reliability
def tags(pid, fams, waves):
    out = []
    for w in waves:
        c = {k: sorted([d for d in cells[(pid, f)] if d['wave'] == w], key=lambda d: d['replicate']) for k, f in zip(('base', 'surface_gs', 'surface_dlm'), ('base',) + fams)}
        out.append(sp.f.tag(c, 4))
    return out
W = list(range(r['waves'])); EV, OD = W[0::2], W[1::2]
lab = {row['pid']: {'R': tags(row['pid'], REAL, W), 'S': tags(row['pid'], SHAM, W)} for row in rows}
def kap(kind, pids):
    return fleiss([(lab[p][kind].count('NR'), lab[p][kind].count('R')) for p in pids])
def kboot(kind):
    pids = [p for p in lab if lab[p][kind].count('NR') + lab[p][kind].count('R') >= 2]; m = len(pids); bt = []
    for _ in range(B):
        k = kap(kind, [pids[i] for i in rng.integers(0, m, m)])
        if k is not None: bt.append(k)
    return kap(kind, pids), np.quantile(bt, [.025, .975]).tolist(), m, B - len(bt)
def solve_half(pid, waves):
    s = lambda fams: np.mean([d['correct'] for f in fams for d in cells[(pid, f)] if d['wave'] in waves])
    return s(SHAM) - s(REAL)
def frag_half(pid, waves, kind='R'):
    t = [lab[pid][kind][w] for w in waves]; b = [x for x in t if x in ('NR', 'R')]
    return (b.count('NR') / len(b) if b else None, len(b))
def split_half(pairs):
    x = np.array(pairs, float); m = len(x)
    def sb(ix):
        rr = np.corrcoef(x[ix, 0], x[ix, 1])[0, 1]; return 2 * rr / (1 + rr)
    bt = [v for v in (sb(rng.integers(0, m, m)) for _ in range(B)) if np.isfinite(v)]
    rr = float(np.corrcoef(x[:, 0], x[:, 1])[0, 1])
    return rr, float(2 * rr / (1 + rr)), np.quantile(bt, [.025, .975]).tolist(), m
sol = [(solve_half(row['pid'], set(EV)), solve_half(row['pid'], set(OD))) for row in rows]
fr = [(frag_half(row['pid'], EV), frag_half(row['pid'], OD)) for row in rows]
fr = [(e[0], o[0]) for e, o in fr if e[1] >= 2 and o[1] >= 2]
frs = [(frag_half(row['pid'], EV, 'S'), frag_half(row['pid'], OD, 'S')) for row in rows]
frs = [(e[0], o[0]) for e, o in frs if e[1] >= 2 and o[1] >= 2]

v, ptr = {}, {}
def put(key, value, pointer):
    assert key not in v; v[key] = value; ptr[key] = pointer
r4 = lambda x: round(x, 4); r3 = lambda x: round(x, 3); r2 = lambda x: round(x, 2)
SRC = 'post hoc on ' + DRW + ' via frozen score_phase1.analyse rows'
e, c = boot(num_part); put('ph_a_num', r4(e), SRC + ' :: mean (n_S - n_R)(a_S + a_R)/2; 4 dp'); put('ph_a_num_ci', [r4(t) for t in c], SRC + ' :: problem bootstrap B=2000; 4 dp')
e, c = boot(acc_part); put('ph_a_acc', r4(e), SRC + ' :: mean (a_S - a_R)(n_S + n_R)/2; 4 dp'); put('ph_a_acc_ci', [r4(t) for t in c], SRC + ' :: problem bootstrap B=2000; 4 dp')
put('ph_a_num_share', r2(float(np.mean(num_part)) / float(np.mean(total))), SRC + ' :: numeric-rate part / PRIMARY est; 2 dp')
e, c = boot(dnum); put('ph_a_dnum', r4(e), SRC + ' :: mean n_S - n_R (numeric-answer rate, copies minus rewrites); 4 dp'); put('ph_a_dnum_ci', [r4(t) for t in c], SRC + ' :: problem bootstrap; 4 dp')
e, c = boot(t4bc); put('ph_b_t4bc', r4(e), SRC + ' :: mean nr_sham_own - bias-corrected N0 (decomp.corrected, R=2000), T2 problems; 4 dp'); put('ph_b_t4bc_ci', [r4(t) for t in c], SRC + ' :: problem bootstrap; 4 dp')
put('ph_b_t4bc_n', len(O), SRC + ' :: T4 problems')
put('ph_b_cal2_ceil', r3(float(np.mean(np.abs(zs) > 1.96))), SRC + ' :: CAL2 share |z|>1.96, problems with p_base >= 0.9; 3 dp')
put('ph_b_cal2_ceil_tests', len(zs), SRC + ' :: CAL2 tests with nonzero SE, p_base >= 0.9')
for kind, key in (('R', 'real'), ('S', 'sham')):
    k, c, m, und = kboot(kind)
    put(f'ph_c_kappa_{key}', r3(k), SRC + f' :: Fleiss kappa NR/R over 12 waves, {key} label, >= 2 binary waves; 3 dp')
    put(f'ph_c_kappa_{key}_ci', [r2(t) for t in c], SRC + f' :: problem bootstrap B=2000 ({und} undefined); 2 dp')
    put(f'ph_c_kappa_{key}_n', m, SRC + f' :: problems with >= 2 binary waves, {key} label')
for name, pairs in (('solve', sol), ('frag', fr), ('frag_sham', frs)):
    rr, sb, c, m = split_half(pairs)
    put(f'ph_c_sb_{name}', r2(sb), SRC + f' :: Spearman-Brown of even/odd-wave Pearson r ({rr:.4f}); 2 dp')
    put(f'ph_c_sb_{name}_ci', [r2(t) for t in c], SRC + ' :: problem bootstrap B=2000; 2 dp')
    put(f'ph_c_sb_{name}_n', m, SRC + ' :: problems')

out = (Path(sys.argv[1]) if len(sys.argv) > 1 else HERE) / 'ar2-t106.json'  # optional dry-run folder
with open(out, 'x', encoding='utf-8') as fh:
    json.dump(dict(tier='SHAM Phase 1 post hoc analyses (a)-(c) requested by the second referee; [E-post], run after the BR2 blind replay matched. AR2 t106 producer for report v1.3.',
                   values=v, raw_pointers=ptr, _manifest=manifest), fh, indent=1, ensure_ascii=False)
print(json.dumps(v, indent=0), hashlib.sha256(out.read_bytes()).hexdigest())
