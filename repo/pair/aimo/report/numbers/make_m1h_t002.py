"""M1h numbers (t002) for report draft v0.2: the checks the v0.1 cold read asked for
(pair/aimo/report/COLD-READ-v0.1-M1h.md). Every value is computed here from raw, sha-pinned records:
- rel_kappa_ci: percentile bootstrap over READY63 originals of the unequal-rater Fleiss kappa (NR vs R).
- f6h_sel_*: does word count predict which reached fresh6h originals got a binary tag (selection check),
  and A4 minus word count after inverse-probability weighting by word-count decile (post hoc).
- mde_*: minimum detectable gain (two-sided, 80% power) for each frozen null row, from that row's own
  stored interval by a normal approximation: MDE = (z_{a/2} + z_{0.8}) * width / (2 z_{a/2}).
- a4_*: feature counts of the frozen A4 parameters, for the definition in Section 3.
All post hoc, written after the outcomes were read; nothing here was preregistered.
Writes numbers/m1h-t002.json (exclusive create). No models, GPU, network or sealed data.
usage: python -I pair/aimo/report/numbers/make_m1h_t002.py
"""
import hashlib, json, random
from pathlib import Path
from statistics import NormalDist

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
SEED = 20261022
B = 2000
manifest = {}
PINS = {'explore/W9b/ready63rel/out/RESULT.json': None, 'explore/W9b/fresh6h/out/PER-ORIGINAL.jsonl': None,
        'explore/W9b/fresh6h/PREDICTIONS-BEFORE-RECORDS.json': None, 'explore/W9b/fresh6h/out/RESULT.json': None,
        'explore/X3/evening-20261020/81-ready63/RESULT.json': None,
        'explore/X1/prefix113_once/run-1792449357639288400/results.json': None,
        'pair/aimo/paper/numbers/w9b-t039.json': None, 'pair/aimo/paper/numbers/w9b-t040.json': None,
        'explore/X3/afternoon-20261020/56/MODEL-PARAMETERS-FROZEN.json': None,
        'explore/X3/afternoon-20261020/56/FREEZE.json': None}


def raw(rel):
    p = ROOT / rel
    b = p.read_bytes()
    manifest[str(p)] = hashlib.sha256(b).hexdigest()
    return b.decode('utf-8-sig')


def load(rel): return json.loads(raw(rel))


v, ptr = {}, {}


def put(k, val, src, pointer):
    assert k not in v, k
    v[k] = val; ptr[k] = src + ' :: ' + pointer


def pct(xs, lo=2.5, hi=97.5):
    xs = sorted(xs); n = len(xs)
    return [xs[int(lo / 100 * (n - 1))], xs[int(hi / 100 * (n - 1))]]


def auc(pos, neg, wp=None, wn=None):
    """Mann-Whitney AUC with optional weights; ties count half."""
    wp = wp or [1.0] * len(pos); wn = wn or [1.0] * len(neg)
    allv = sorted([(x, 1, w) for x, w in zip(pos, wp)] + [(x, 0, w) for x, w in zip(neg, wn)])
    num = 0.0; negbelow = 0.0; i = 0
    while i < len(allv):
        j = i; tp = tn = 0.0
        while j < len(allv) and allv[j][0] == allv[i][0]:
            if allv[j][1]: tp += allv[j][2]
            else: tn += allv[j][2]
            j += 1
        num += tp * (negbelow + 0.5 * tn); negbelow += tn; i = j
    return num / (sum(wp) * sum(wn))


rng = random.Random(SEED)

# ---- 1. Kappa interval, READY63 repeats ----
RR = 'explore/W9b/ready63rel/out/RESULT.json'
rr = load(RR)
subj = [(o['counts'].get('NR', 0), o['counts'].get('R', 0)) for o in rr['S4']['per_original'].values()]
subj = [s for s in subj if sum(s) >= 2]


def kappa(ss):
    pi = [(a * (a - 1) + b * (b - 1)) / ((a + b) * (a + b - 1)) for a, b in ss]
    p = sum(a for a, _ in ss) / sum(a + b for a, b in ss); pe = p * p + (1 - p) * (1 - p)
    return (sum(pi) / len(pi) - pe) / (1 - pe)


k0 = kappa(subj)
assert abs(k0 - rr['S4']['fleiss_kappa_NR_R']['kappa']) < 1e-12 and len(subj) == rr['S4']['fleiss_kappa_NR_R']['subjects']
kb = pct([kappa([rng.choice(subj) for _ in subj]) for _ in range(B)])
put('rel_kappa_ci', [round(x, 2) for x in kb], RR, f'percentile bootstrap over the {len(subj)} originals in /S4/per_original with >=2 binary waves, B={B}, seed {SEED}; 2 dp')

# ---- 2. fresh6h selection into the scorable (binary) subset ----
PO, PR, FR = 'explore/W9b/fresh6h/out/PER-ORIGINAL.jsonl', 'explore/W9b/fresh6h/PREDICTIONS-BEFORE-RECORDS.json', 'explore/W9b/fresh6h/out/RESULT.json'
pred = {r['pid']: r for r in load(PR)['rows']}
tags = {}
for line in raw(PO).splitlines():
    d = json.loads(line)
    if d['primary'] and d['primary']['reached']: tags[d['pid']] = d['primary']['strict']
fr = load(FR)['primary']['strict']
assert len(tags) == fr['reached']
reached = sorted(tags)
binary = [p for p in reached if tags[p] in ('NR', 'R')]
assert len(binary) == fr['binary']
words = {p: pred[p]['words'] for p in reached}
put('f6h_sel_binary_share', round(100 * len(binary) / len(reached), 1), PO, 'binary / reached under /primary/strict, percent, 1 dp')
isb = [p for p in reached if tags[p] in ('NR', 'R')]; nob = [p for p in reached if tags[p] not in ('NR', 'R')]
sel = auc([words[p] for p in nob], [words[p] for p in isb])
selb = []
for _ in range(B):
    s = [rng.choice(reached) for _ in reached]
    a = [words[p] for p in s if tags[p] not in ('NR', 'R')]; b = [words[p] for p in s if tags[p] in ('NR', 'R')]
    selb.append(auc(a, b))
put('f6h_sel_auc_words', round(sel, 3), PO, 'AUC of word count (PREDICTIONS-BEFORE-RECORDS /rows/*/words) for NOT getting a binary tag, over reached originals; 3 dp')
put('f6h_sel_auc_words_ci', [round(x, 3) for x in pct(selb)], PO, f'percentile bootstrap over reached originals, B={B}, seed {SEED}; 3 dp')
order = sorted(reached, key=lambda p: (words[p], p))
third = [order[:len(order) // 3], order[len(order) // 3:2 * len(order) // 3], order[2 * len(order) // 3:]]
for i, grp in enumerate(third, 1):
    put(f'f6h_sel_share_t{i}', round(100 * sum(tags[p] in ('NR', 'R') for p in grp) / len(grp), 1), PO,
        f'binary share in word-count third {i} of reached originals (sorted by words, then pid), percent, 1 dp')
# Inverse-probability weighting by word-count decile: reweights scored originals to the reached population.
dec = {}
for i, p in enumerate(order): dec[p] = min(9, i * 10 // len(order))
share = {d: sum(tags[p] in ('NR', 'R') for p in order if dec[p] == d) / sum(dec[p] == d for p in order) for d in range(10)}
w = {p: 1 / share[dec[p]] for p in binary}


def ipw_p1(ps):
    pos = [p for p in ps if tags[p] == 'NR']; neg = [p for p in ps if tags[p] == 'R']
    wp = [w[p] for p in pos]; wn = [w[p] for p in neg]
    return (auc([pred[p]['interaction-A4'] for p in pos], [pred[p]['interaction-A4'] for p in neg], wp, wn)
            - auc([words[p] for p in pos], [words[p] for p in neg], wp, wn))


unw = auc([pred[p]['interaction-A4'] for p in binary if tags[p] == 'NR'], [pred[p]['interaction-A4'] for p in binary if tags[p] == 'R']) \
    - auc([words[p] for p in binary if tags[p] == 'NR'], [words[p] for p in binary if tags[p] == 'R'])
assert abs(unw - fr['P1_A4_minus_length']['est']) < 1e-9, (unw, fr['P1_A4_minus_length']['est'])
put('f6h_sel_ipw_p1', round(ipw_p1(binary), 3), PO + ' + ' + PR, 'A4 minus word-count AUC on binary originals, weighted by 1/(binary share of word-count decile among reached); 3 dp')
put('f6h_sel_ipw_p1_ci', [round(x, 3) for x in pct([ipw_p1([rng.choice(binary) for _ in binary]) for _ in range(B)])], PO,
    f'percentile bootstrap over binary originals with the decile weights held fixed, B={B}, seed {SEED}; 3 dp')

# ---- 3. Minimum detectable gain for each frozen null row ----
Z80 = NormalDist().inv_cdf(0.80)


def mde(ci, level):
    z = NormalDist().inv_cdf(1 - (1 - level) / 2)
    return (z + Z80) * (ci[1] - ci[0]) / (2 * z)


X81 = 'explore/X3/evening-20261020/81-ready63/RESULT.json'
PF = 'explore/X1/prefix113_once/run-1792449357639288400/results.json'
T39, T40 = 'pair/aimo/paper/numbers/w9b-t039.json', 'pair/aimo/paper/numbers/w9b-t040.json'
frs = load(FR)['primary']['strict']
rows = [('mde_pfx', load(PF)['metrics']['frozen_entropy_change']['delta_saved_length_ci95'], 0.95, PF, '/metrics/frozen_entropy_change/delta_saved_length_ci95'),
        ('mde_val_p', load(T39)['values']['val_p_gain_ci'], 0.95, T39, '/values/val_p_gain_ci (from explore/X1/amended0055 bootstraps)'),
        ('mde_x170', load(T40)['values']['x170_gain_ci'], 0.95, T40, '/values/x170_gain_ci (from explore/X1/170 result text)'),
        ('mde_f81', load(X81)['endpoints']['strict_n4']['bootstrap']['original']['interval95']['interaction-A4']['AUCgain'], 0.95, X81, '/endpoints/strict_n4/bootstrap/original/interval95/interaction-A4/AUCgain'),
        ('mde_rel', rr['primary']['original_bootstrap']['ci95'], 0.95, RR, '/primary/original_bootstrap/ci95'),
        ('mde_f6h_p1', frs['P1_A4_minus_length']['ci975'], 0.975, FR, '/primary/strict/P1_A4_minus_length/ci975'),
        ('mde_f6h_p2', frs['P2_A4_minus_baseagree']['ci975'], 0.975, FR, '/primary/strict/P2_A4_minus_baseagree/ci975')]
for k, ci, level, src, pp in rows:
    put(k, round(mde(ci, level), 3), src, pp + f'; MDE at two-sided level {1 - level:.3f}, 80% power, normal approximation from interval width; 3 dp')

# ---- 4. A4 definition counts ----
MP, FZ = 'explore/X3/afternoon-20261020/56/MODEL-PARAMETERS-FROZEN.json', 'explore/X3/afternoon-20261020/56/FREEZE.json'
nfeat = len(load(MP)['interaction-A4']['feature_mean']); ncat = len(load(FZ)['training_source_categories'])
put('a4_text_features', nfeat - ncat, MP, '/interaction-A4/feature_mean length minus FREEZE /training_source_categories length')
put('a4_source_cats', ncat, FZ, '/training_source_categories length (set to zero at prediction)')

assert set(manifest) == {str(ROOT / k) for k in PINS}, set(manifest) ^ {str(ROOT / k) for k in PINS}
out = {'tier': 'Exploratory, post hoc; M1h t002 producer (cold-read checks for report draft v0.2). Written after all outcomes were read.',
       'values': v, 'raw_pointers': ptr, 'checks': ['kappa point estimate equals the stored RESULT value', 'unweighted fresh6h P1 equals the stored RESULT value'],
       '_manifest': manifest, 'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (HERE / 'm1h-t002.json').open('x', encoding='utf-8') as f:
    json.dump(out, f, indent=1)
print(json.dumps(v))
