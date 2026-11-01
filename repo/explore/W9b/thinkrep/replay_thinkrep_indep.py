"""Independent replay of the THINKREP score (W9b, written 24 Oct 2026 after the r2 freeze and BEFORE any run output existed;
its sha is recorded in LAUNCH-NOTES.md). Run once, after score_thinkrep.py has written out/RESULT.json.
  python -B replay_thinkrep_indep.py RUN_DIR RESULT_JSON DRAWS_JSONL OUT_JSON
Shares no code with the scorer or thinkrep_core except the frozen answer parser (parse_think.parse), which V14 replayed
separately on 10,388 real thinking draws. Its own code does:
  - record binding (envelope hashes, identity, seed, request sha) from the attempt's frozen REQUESTS file;
  - wave status (INCLUDED / PARTIAL / NOT_REACHED, plus the scorer's recorded max_wave);
  - grading rules O and S;
  - the strict n4 tag;
  - unequal-rater Fleiss kappa and its original bootstrap (2,000, seed 8101945);
  - per-wave AUCs and the mean A4 - point-K gain.
It then compares the result with RESULT.json and DRAWS.jsonl. It writes OUT_JSON only (must not exist) and exits 1 on any mismatch."""
import collections, hashlib, json, sys
from pathlib import Path
import numpy as np
from scipy.stats import rankdata

E = Path('E:/work/research-cycle/explore'); TR = E / 'W9b/thinkrep'; sys.path.insert(0, str(TR))
from parse_think import parse  # noqa: E402  (the frozen parser; nothing else is imported from the pipeline)

RUN, RES, DRAWS, OUT = map(Path, sys.argv[1:5]); assert not OUT.exists()
canon = lambda x: json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
sha = lambda b: hashlib.sha256(b).hexdigest()
res = json.loads(RES.read_bytes()); man = json.loads((RUN / 'MANIFEST.json').read_bytes()); A = man['thinkrep_attempt']
reqs = json.loads((TR / ('REQUESTS.json' if A == 1 else 'REQUESTS-a2.json')).read_bytes())
truths = json.loads((TR / ('TRUTHS.json' if A == 1 else 'TRUTHS-a2.json')).read_bytes())
assert man['request_sha256'] == sha((TR / ('REQUESTS.json' if A == 1 else 'REQUESTS-a2.json')).read_bytes())
cohort = json.loads((TR / 'COHORT.json').read_bytes()); PIDS = cohort['pids']
pred = {r['pid']: r for r in json.loads((E / 'X3/afternoon-20261020/64/PREDICTIONS-V2-BEFORE-FRESH-OUTCOMES.json').read_bytes())['rows']}
rep0 = 2000 if A == 1 else 3000

files = {p.stem: p for p in RUN.glob('block-*/records/*.json')}
wave = {q['identity_sha256']: (q['identity']['replicate'] - rep0) // 4 for q in reqs}
present = collections.Counter(wave[k] for k in files)
max_wave = res['operational']['wave_status'].index('NOT_USED') if 'NOT_USED' in res['operational']['wave_status'] else 20
last = max(present) if present else -1
inc = [w for w in range(min(20, max_wave)) if present[w] == 408 or (present[w] and w < last)]

status = {}
for q in reqs:
    k = q['identity_sha256']
    if wave[k] not in inc:
        continue
    if k not in files:
        status[k] = dict(status='missing', correct=None); continue
    try:
        e = json.loads(files[k].read_bytes()); r = e['record']
        assert e['record_sha256'] == sha(canon(r)) and r['raw_sha256'] == sha(r['raw'].encode()) and r['output_tokens'] == len(r['token_ids'])
        assert r['identity'] == q['identity'] and str(r['seed']) == str(q['seed']) and r['request_sha256'] == sha(canon(q))
        status[k] = parse(r['raw'], r['finish_reason'], r['error'], truths[k])
    except Exception:  # noqa: BLE001
        status[k] = dict(status='binding_fail', correct=None)

UNGRADABLE_O = {'missing', 'binding_fail', 'error'}


def tag(ks, rule):
    s = {}
    for fam in ('base', 'surface_gs', 'surface_dlm'):
        c = 0
        for k in ks[fam]:
            st = status[k]['status']
            if (rule == 'O' and st in UNGRADABLE_O) or (rule == 'S' and st != 'numeric'):
                return 'UNUSABLE'
            c += status[k]['correct'] if st == 'numeric' else 0
        s[fam] = c
    return 'FLOOR' if s['base'] == 0 else ('NR' if min(s['surface_gs'], s['surface_dlm']) < s['base'] else 'R')


cell = collections.defaultdict(lambda: collections.defaultdict(list))
for q in reqs:
    k = q['identity_sha256']
    if k in status:
        cell[(wave[k], q['identity']['problem_id'])][q['identity']['family']].append(k)
T = {rule: {w: {p: tag(cell[(w, p)], rule) for p in PIDS} for w in inc} for rule in ('O', 'S')}


def fleiss(nr, nb):
    m = nb >= 2
    if not m.any():
        return None
    a, n = nr[m], nb[m]; b = n - a; Pi = (a * (a - 1) + b * (b - 1)) / (n * (n - 1)); p = a.sum() / n.sum(); Pe = p * p + (1 - p) ** 2
    return float((Pi.mean() - Pe) / (1 - Pe)) if Pe < 1 else None


def kappa(rule):
    nb = np.array([sum(T[rule][w][p] in ('NR', 'R') for w in inc) for p in PIDS]); nr = np.array([sum(T[rule][w][p] == 'NR' for w in inc) for p in PIDS])
    rng = np.random.default_rng(8101945); bs = []
    for _ in range(2000):
        ix = rng.integers(0, len(PIDS), len(PIDS)); v = fleiss(nr[ix], nb[ix])
        if v is not None and not np.isnan(v):
            bs.append(v)
    return dict(kappa=fleiss(nr, nb), NR_tags=int(nr.sum()), binary=int(nb.sum()), ci95=np.quantile(bs, [.025, .975]).tolist() if bs else None)


def auc(y, s):
    y = np.asarray(y, int); n1 = y.sum(); n0 = len(y) - n1
    return None if not n1 or not n0 else float((rankdata(np.round(s, 12))[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def gain(rule):
    g = []
    for w in inc:
        ps = [p for p in PIDS if T[rule][w][p] in ('NR', 'R')]; y = [T[rule][w][p] == 'NR' for p in ps]
        a = auc(y, [pred[p]['NR_scores']['interaction-A4'] for p in ps]); b = auc(y, [pred[p]['NR_scores']['point-K'] for p in ps])
        if a is not None:
            g.append(a - b)
    return float(np.mean(g)) if g else None


mine = dict(attempt=A, included_waves=inc, kappa_O=kappa('O'), kappa_S=kappa('S'), gain_O=gain('O'), gain_S=gain('S'),
            status_counts=dict(collections.Counter(v['status'] for v in status.values())))
d_rows = {json.loads(l)['key']: json.loads(l) for l in open(DRAWS, encoding='utf-8')}
close = lambda a, b: (a is None and b is None) or (a is not None and b is not None and abs(a - b) < 1e-9)
checks = dict(
    included_waves=inc == res['operational']['included_waves'],
    draw_set=set(d_rows) == set(status),
    draw_status=all(d_rows[k]['status'] == status[k]['status'] for k in status) if set(d_rows) == set(status) else False,
    kappa_O=close(mine['kappa_O']['kappa'], res['P1_kappa_O']['kappa']),
    kappa_O_ci=all(close(a, b) for a, b in zip(mine['kappa_O']['ci95'] or [None] * 2, res['P1_kappa_O']['bootstrap']['ci95'] or [None] * 2)),
    NR_tags_O=mine['kappa_O']['NR_tags'] == res['P1_kappa_O']['NR_tags'],
    kappa_S=close(mine['kappa_S']['kappa'], res['S1_strict']['kappa']['kappa']),
    gain_O=close(mine['gain_O'], res['P3_repeat_gain_O']['observed']),
    gain_S=close(mine['gain_S'], res['S1_strict']['gain']['observed']))
mine['checks'] = checks; mine['all_match'] = all(checks.values())
mine['result_sha256'] = sha(RES.read_bytes()); mine['replay_sha256'] = sha(Path(__file__).read_bytes())
with open(OUT, 'x', encoding='utf-8') as fh:
    json.dump(mine, fh, indent=1)
print(json.dumps(dict(checks=checks, all_match=mine['all_match'], kappa_O=mine['kappa_O']), indent=1))
sys.exit(0 if mine['all_match'] else 1)
