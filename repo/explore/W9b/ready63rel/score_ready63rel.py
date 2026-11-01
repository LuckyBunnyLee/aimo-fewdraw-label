"""One-shot scorer for W9b/PREREG-READY63-RELIABILITY-20261021.md. Writes only W9b/ready63rel/out."""
import collections, hashlib, json, sys
from pathlib import Path
import numpy as np
E = Path('E:/work/research-cycle/explore'); DR = Path('D:/research-cycle/cl-ready63-reliability-20261020-1740'); BLK = DR / 'block-1792543703210030707'
sys.path.insert(0, str(E / 'X3')); import fresh81_pure as f
OUT = E / 'W9b/ready63rel/out'; SRC = E / 'CL-5070-recovery-20261020-1740/ready63-reliability'
H = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
BOUND = {  # prereg section 2, plus the prereg itself (sha recorded after writing) and the 81 tag file used for S4
    E / 'W9b/PREREG-READY63-RELIABILITY-20261021.md': 'b147cdfe2be28f31718509b6548c25704fd83f6af180219b1cd670505c204562',
    E / 'X3/afternoon-20261020/64/PREDICTIONS-V2-BEFORE-FRESH-OUTCOMES.json': '833f74c8d34a2450831f1f1f30c07c29180e9f691d41087997566cc8ad4d90bb',
    E / 'X3/afternoon-20261020/64/FREEZE-V2.json': 'b4ab49b5e6ec15d73e4559670de44a57e2af7d9941fa80b28304d39751128e70',
    E / 'X3/afternoon-20261020/SPEC-64.md': 'a83250ca7d662c5a1d5c887c0ff330a6541e1735b2f84f1f92c3dbbfb7cbe273',
    E / 'X3/afternoon-20261020/SPEC-64-BASELINE-CORRECTION.md': '1c838b0315dbd07c0d79a83b58542aa65fd2ee1e47b8837a664ffe8d68e1b399',
    E / 'X3/fresh81_pure.py': '6b9c0e124f4d690c6bd1412aeccfdc8d12b8b20fb2ebe3d0576656c0b59f1e4d',
    E / 'X3/run81_combined_v2_20261020.py': 'cbd003ab52b788665d3d1c38e443b97452df0ad07e977f2998f324814bff2aec',
    SRC / 'MANIFEST.json': '20b593e92d46f9aae50e6b7249e3efeab4f41cf21031664bdc02b39ea9bf17b0',
    DR / 'MANIFEST.json': '20b593e92d46f9aae50e6b7249e3efeab4f41cf21031664bdc02b39ea9bf17b0',
    SRC / 'REQUESTS.json': '3964f3fada3a925e2875869718d06fde776f31cf65a0e7609435b55393bc76d1',
    SRC / 'TRUTHS.json': 'b22e71692b098b2b76cf4ece81b99a230e286ce1d8f7239bfd6e52896811fa04',
    SRC / 'ADMISSION-OVERNIGHT.json': 'b5d50864d3248ac4d1b9bb2717bab028f06b3c48b117a6da5a6431b3df0662d9',
    SRC / 'run_overnight.py': 'e8360555ab1d0edf70275ff163c4d65d2ff31bfc865ed17d0ae0d8983f6e2be9',
    BLK / 'PLAN.json': '0dfa6734b2a0eae170a6a9cb5dead2510ea802c0b75e1b013f9fdd0b77c97302',
    BLK / 'LAUNCH.json': '5163555431698f4595915668ba1e5bed0aff96017b98300e17439883751045e0',
    BLK / 'EXIT.json': '224b80766b5a3961d7333e4afe7bdb8ddb63d817d91a2c31d808065110cdb56c',
    BLK / 'MODEL-BINDING.json': '1b4ff13b6955fe2543d0f000898ee81fceea36f9c8d9de7bacf16b1ed58a69e2',
    BLK / 'ENGINE-CONFIG.json': '0c4964ba389f707a766d7e019724ea60b772d4fc803a3033a6f027a2fbfd23aa',
    BLK / 'PILOT-GATE.json': 'fbaa7bb7a6453de65f7583b1f10ba082cce73696ed58ca90d93b14da0961dfec',
    E / 'CL-handoff-20261019-1344/recovery1740-ready63-reliability-TERMINAL-1792569518757826700.json': '75fb3b5739c414fa6276001da4688815db51f93f3ca7524af94fd8ba86bc9d4f',
    E / 'X3/evening-20261020/81-ready63/strict_n4-ALL-ORIGINALS.json': '46481896331cfd599180376f57c8153cb92ac32fb5b5be873a934262c42c1507',
}
for p, h in BOUND.items():
    assert H(p) == h, f'ABORT hash mismatch {p}'
assert not OUT.exists(), 'one-shot guard'
J = lambda p: json.loads(Path(p).read_bytes()); ev = lambda i: eval(i) if isinstance(i, str) else i
METHODS = f.METHODS; BASE = f.BASE; FAMS = ['base', 'surface_gs', 'surface_dlm']; W = 100; G81 = 0.10096153846153844
reqs = {q['identity_sha256']: q for q in J(SRC / 'REQUESTS.json')}; truth = J(SRC / 'TRUTHS.json'); assert len(reqs) == 40800
pred = {r['pid']: r for r in J(E / 'X3/afternoon-20261020/64/PREDICTIONS-V2-BEFORE-FRESH-OUTCOMES.json')['rows']}
tag81 = {r['pid']: r['label'] for r in J(E / 'X3/evening-20261020/81-ready63/strict_n4-ALL-ORIGINALS.json')}
exitj = J(BLK / 'EXIT.json')
files = {p.stem: p for p in (BLK / 'records').iterdir() if len(p.name) == 69 and p.suffix == '.json'}
ignored = sorted(p.name for p in (BLK / 'records').iterdir() if p.stem not in files)

# --- bind + parse (section 3)
draw = {}; fails = []; seen = set()
for key, q in reqs.items():
    qi = ev(q['identity']); v = dict(status='missing', answer=None, correct=None); fin = None; tok = 0
    try:
        assert key in files, 'missing record'
        r = f.envelope(json.loads(files[key].read_bytes()))
        assert r['identity_sha256'] == key and key not in seen, 'key'
        assert ev(r['identity']) == qi and str(r['seed']) == str(q['seed']) and r['request_sha256'] == f.sha(f.canon(q)), 'identity/seed/request'
        seen.add(key); v = f.parse(r['raw'], r['finish_reason'], r['error'], truth[key]); fin = r['finish_reason']; tok = r['output_tokens']
    except Exception as exc:
        fails.append(dict(key=key, error=repr(exc))); v = dict(status='binding_fail', answer=None, correct=None)
    draw[key] = dict(key=key, pid=qi['problem_id'], family=qi['family'], replicate=qi['replicate'], finish=fin, tokens=tok, **v)
assert not (set(files) - set(reqs)), 'unexpected record names'
by = collections.defaultdict(list)
for d in draw.values(): by[(d['pid'], d['family'])].append(d)
PIDS = sorted({d['pid'] for d in draw.values()}); assert len(PIDS) == 34 and set(PIDS) <= set(pred)
for pid in PIDS:
    assert len({str(truth[d['key']]) for fam in FAMS for d in by[(pid, fam)]}) == 1, f'truth not unique {pid}'
def nonnum(d): return d if d['status'] == 'numeric' else dict(d, correct=None)
waves = collections.defaultdict(dict)  # waves[w][pid] = (strict tag, n2B tag)
for pid in PIDS:
    srt = {fam: sorted(by[(pid, fam)], key=lambda d: d['replicate']) for fam in FAMS}
    for fam in FAMS: assert [d['replicate'] for d in srt[fam]] == list(range(1000, 1400))
    for w in range(W):
        cells = {fam: [nonnum(d) for d in srt[fam][4 * w:4 * w + 4]] for fam in FAMS}
        half = f.sides(cells); waves[w][pid] = (f.tag(cells, 4), f.tag(half['A'], 2))

# --- per-wave metrics
P = {k: np.array([pred[pid]['NR_scores'][k] for pid in PIDS]) for k in METHODS}
TPL = np.array([pred[pid]['template_family'] for pid in PIDS])
def tags(w, ep): return [waves[w][pid][ep] for pid in PIDS]
def wave_stats(ix, ep):
    """ix: original indices (with repetition). Returns per-wave dicts of AUC/Brier/acc per method."""
    out = []
    for w in range(W):
        t = np.array(tags(w, ep))[ix]; b = np.isin(t, ['NR', 'R']); y = (t[b] == 'NR').astype(int)
        m = {k: f.metrics(y, P[k][ix][b]) for k in METHODS}
        out.append(dict(n=int(b.sum()), NR=int(y.sum()), m=m, allR=float(np.mean(y == 0)) if len(y) else None))
    return out
def summarize(ws):
    o = {}
    for k in METHODS:
        g = [s['m'][k]['AUC'] - s['m'][BASE]['AUC'] for s in ws if s['m'][BASE]['AUC'] is not None]
        bg = [s['m'][BASE]['Brier'] - s['m'][k]['Brier'] for s in ws if s['n']]
        o[k] = dict(mean_AUC=float(np.mean([s['m'][k]['AUC'] for s in ws if s['m'][k]['AUC'] is not None])) if g else None,
                    mean_AUC_gain=float(np.mean(g)) if g else None, defined_waves=len(g),
                    mean_Brier=float(np.mean([s['m'][k]['Brier'] for s in ws if s['n']])) if bg else None,
                    mean_Brier_gain=float(np.mean(bg)) if bg else None,
                    mean_acc05=float(np.mean([s['m'][k]['accuracy05'] for s in ws if s['n']])) if bg else None)
    o['AllR_accuracy_mean'] = float(np.mean([s['allR'] for s in ws if s['n']]))
    return o
ALL = np.arange(len(PIDS)); result = {}
for ep_i, ep in enumerate(['strict_n4', 'hashed_n2B']):
    ws = wave_stats(ALL, ep_i); obs = summarize(ws)
    per_gain = [s['m']['interaction-A4']['AUC'] - s['m'][BASE]['AUC'] for s in ws if s['m'][BASE]['AUC'] is not None]
    boots = {}
    for mode in ['original', 'template']:
        rng = np.random.default_rng(8101945); ug = sorted(set(TPL)); vals = []
        for _ in range(2000):
            ix = rng.choice(len(PIDS), len(PIDS), replace=True) if mode == 'original' else np.concatenate([np.flatnonzero(TPL == g) for g in rng.choice(ug, len(ug), replace=True)])
            vals.append(summarize(wave_stats(ix, ep_i)))
        boots[mode] = {k: {meas: (lambda a: dict(ci95=np.quantile(a, [.025, .975]).tolist() if a else None, valid=len(a)))([v[k][meas] for v in vals if v[k][meas] is not None])
                           for meas in ['mean_AUC_gain', 'mean_Brier_gain']} for k in METHODS}
    counts = [dict(collections.Counter(tags(w, ep_i))) for w in range(W)]
    result[ep] = dict(observed=obs, bootstrap=boots, per_wave_primary_gain=per_gain, per_wave_counts=counts,
                      per_wave_binary=[s['n'] for s in ws], per_wave_NR=[s['NR'] for s in ws])
pg = np.array(result['strict_n4']['per_wave_primary_gain'])
placement = dict(gain81=G81, frac_below=float(np.mean(pg < G81)), frac_at_or_below=float(np.mean(pg <= G81)), min=float(pg.min()), median=float(np.median(pg)), max=float(pg.max()), defined=len(pg))

# --- S4 reliability of the strict label
s4 = {}
for i, pid in enumerate(PIDS):
    t = tags_p = [waves[w][pid][0] for w in range(W)]; bn = [x for x in t if x in ('NR', 'R')]
    s4[pid] = dict(tag81=tag81[pid], counts=dict(collections.Counter(t)), binary_waves=len(bn), NR_fraction=(bn.count('NR') / len(bn)) if bn else None,
                   agree81_all=float(np.mean([x == tag81[pid] for x in t])))
agree_by81 = {c: float(np.mean([s4[p]['agree81_all'] for p in PIDS if s4[p]['tag81'] == c])) for c in sorted(set(tag81[p] for p in PIDS))}
both = [(waves[w][p][0], tag81[p]) for p in PIDS for w in range(W) if waves[w][p][0] in ('NR', 'R') and tag81[p] in ('NR', 'R')]
subj = [(s4[p]['counts'].get('NR', 0), s4[p]['counts'].get('R', 0)) for p in PIDS if s4[p]['binary_waves'] >= 2]
Pi = [(a * (a - 1) + b * (b - 1)) / ((a + b) * (a + b - 1)) for a, b in subj]; pNR = sum(a for a, b in subj) / sum(a + b for a, b in subj)
Pe = pNR ** 2 + (1 - pNR) ** 2; kappa = (np.mean(Pi) - Pe) / (1 - Pe) if Pe < 1 else None
S4 = dict(per_original=s4, agreement_with_81_all_tags=float(np.mean([s4[p]['agree81_all'] for p in PIDS])), agreement_by_81_class=agree_by81,
          agreement_with_81_binary_both=float(np.mean([a == b for a, b in both])) if both else None, binary_pairs=len(both),
          fleiss_kappa_NR_R=dict(kappa=float(kappa) if kappa is not None else None, subjects=len(subj), pooled_NR=pNR,
                                 formula='unequal-rater Fleiss: P_i=sum n_ij(n_ij-1)/(n_i(n_i-1)), P_e from pooled proportions'))

# --- diagnostics: pair_stats per wave (strict n4)
diag = []
for w in range(W):
    rows = [dict(label=waves[w][pid][0], scores=pred[pid]['NR_scores'], template=pred[pid]['template_family'], words=len(pred[pid]['problem'].split())) for pid in PIDS]
    rows = [r for r in rows if r['label'] in ('NR', 'R')]
    s, _, _ = f.pair_stats(rows, seed=8101945 + w)
    diag.append({k: v.get('upper_tail') for k, v in s['null'].items()})

status = collections.Counter((d['family'], d['status']) for d in draw.values())
no_usable = [p for p in PIDS if s4[p]['binary_waves'] == 0]
res = dict(scope='EXPLORATORY repeated-measurement secondary-endpoint check of frozen X3-64 V2 on the same 34 READY63 originals scored in 81; NOT an independent fresh test',
           bound_sha256={str(p): h for p, h in BOUND.items()}, scorer_sha256=H(__file__), ignored_non_record_files=len(ignored),
           operational=dict(attempts=len(draw), binding_failures=len(fails), binding_failure_list=fails[:50], status_by_family={f'{a}|{b}': n for (a, b), n in sorted(status.items())},
                            truncated=sum(d['status'] == 'truncated' for d in draw.values()), output_tokens=sum(d['tokens'] for d in draw.values()),
                            exit_elapsed_s=exitj.get('elapsed'), exit_tokens=exitj.get('global_generated_tokens'), originals_with_no_binary_wave=no_usable),
           primary=dict(estimand='mean over defined waves of AUC_w(interaction-A4)-AUC_w(point-K), strict n4', **{'observed': result['strict_n4']['observed']['interaction-A4']['mean_AUC_gain'], 'defined_waves': result['strict_n4']['observed']['interaction-A4']['defined_waves'],
                        'original_bootstrap': result['strict_n4']['bootstrap']['original']['interaction-A4']['mean_AUC_gain'], 'template_bootstrap': result['strict_n4']['bootstrap']['template']['interaction-A4']['mean_AUC_gain']}),
           placement_of_81=placement, endpoints=result, S4=S4, diagnostics_per_wave=diag)
OUT.mkdir(parents=True, exist_ok=False)
(OUT / 'RESULT.json').write_text(json.dumps(res, indent=1, default=float), encoding='utf-8')
with open(OUT / 'DRAWS.jsonl', 'w', encoding='utf-8') as fh:
    for d in draw.values(): fh.write(json.dumps(d) + '\n')
print(json.dumps(dict(operational=res['operational'], primary=res['primary'], placement=placement), indent=1, default=float))
