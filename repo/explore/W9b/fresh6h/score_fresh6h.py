"""One-shot scorer for W9b/PREREG-FRESH6H-20261021.md (frozen f0aec861) with the deviations D1/D2 fixed in
W9b/fresh6h/COVERAGE-DEVIATION-BEFORE-OUTCOMES.md (2932f8e6). Writes only W9b/fresh6h/out."""
import collections, hashlib, json, sys, time
from fractions import Fraction
from pathlib import Path
import numpy as np
E = Path('E:/work/research-cycle/explore'); W = E / 'W9b/fresh6h'; OUT = W / 'out'
JA = Path('D:/research-cycle/cl-fresh6h-20261021-0935'); BA = JA / 'block-1792600526860630240'
JB = Path('D:/research-cycle/cl-fresh-continuation-20261021'); BB = JB / 'block-1792622117822466573'
X = E / 'X3'; O = X / 'afternoon-20261020'
sys.path.insert(0, str(X)); import fresh81_pure as f
H = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
BOUND = {
    E / 'W9b/PREREG-FRESH6H-20261021.md': 'f0aec861ac491f886b52b0d32867f20869b1603fc9771493798a075b29bcaf5c',
    W / 'COVERAGE-DEVIATION-BEFORE-OUTCOMES.md': '2932f8e61935035efc7022576c78ac711f98a5f70e7b8a19f6fcc2abeee39840',
    W / 'PREDICTIONS-BEFORE-RECORDS.json': 'd8c8549f45d1e8491594a0c0e658de60f862a53af073f7cdfa474ecc7b3e95d1',
    # prereg section 2, job
    JA / 'ROSTER.json': 'b75af74ab88518e448950a49a089ba7d3af67c0aa038406115fc673241d9b05d',
    JA / 'ROSTER.sha256': '6094749a6f72d09c35ece016e01cbfc4e8edd0c334ff98af24d6c049a314dae8',
    JA / 'REQUESTS.json': 'daccdc4f5f81ff48a3b1567301b0879930f205d08345fae72d9c78a3da20b1d7',
    JA / 'TRUTHS.json': 'b06a6f45211c2ce08349c60e71020ade450c3d9fa471eba458dc6d245d45d282',
    JA / 'MANIFEST.json': '67d42df993ae19f1fefb2be262bb9e1df428abba88774418b7f5085d034360c0',
    JA / 'ADMISSION-OVERNIGHT.json': '76cbcdb68b5d06f2ed11dfb5712c40d927e291a164e34f51129e2771c5e9c383',
    JA / 'FRESH-ADMISSION.json': 'da5f0c8709e6608e84af24875b5d9d7b5e82cd8b94b42e8df6005967b957e030',
    JA / 'EXACT-OWNERS.json': '92a9d9032e67d8b7103d8f80abfc4f81d5398d5ff6783235399056ea4c71137c',
    JA / 'GUARD-OWNER.json': '8dc8f85ed13fd0ab54ee9c4b395dfb22a16e476412250e529fcfe31e1c3e7be3',
    JA / 'run_overnight.py': 'e8360555ab1d0edf70275ff163c4d65d2ff31bfc865ed17d0ae0d8983f6e2be9',
    JA / 'request_core.py': '49d2049a8eb9f4c9cefe5f55eddf1b8dc71d400241094ff01dc44110e99f32c0',
    JA / 'publish_terminal.py': '747d9ae7a4967dc137e0d9fdbc45d54f4ac5b5f30eadf3449b6bbb6ba47036e3',
    # prereg section 2, predictor and parser
    O / '64/PREDICTIONS-V2-BEFORE-FRESH-OUTCOMES.json': '833f74c8d34a2450831f1f1f30c07c29180e9f691d41087997566cc8ad4d90bb',
    O / '64/FREEZE-V2.json': 'b4ab49b5e6ec15d73e4559670de44a57e2af7d9941fa80b28304d39751128e70',
    O / '64/FREEZE.json': '9c3489f64d59dd9e65414f57731a985d41738c5bdc84a82082a5a394b3be8921',
    O / 'SPEC-64.md': 'a83250ca7d662c5a1d5c887c0ff330a6541e1735b2f84f1f92c3dbbfb7cbe273',
    O / 'SPEC-64-BASELINE-CORRECTION.md': '1c838b0315dbd07c0d79a83b58542aa65fd2ee1e47b8837a664ffe8d68e1b399',
    O / '56/MODEL-PARAMETERS-FROZEN.json': '7360901b7d38a95c4d0eddc9d134465f476a795613925a30ebbeb85bd1194d7e',
    O / '56/FREEZE.json': 'ec02fdaaf217a7ea8f36398cd37bd94cc2fbc8ec4e3e91e2a3bc9a1cdeb11445',
    O / '56/ALL128-PREDICTIONS-BEFORE-THIS-JOIN.json': '7c1e1ccde2ffecdb5dc6228d30e4bcb054d2fcbc4fd593642bc843be43fd6e1e',
    X / 'harder-packs-20261020/READY-01-mid-hard/REQUESTS.json': '490c120b18da687168182ca5bbf389e9f4e71bf2a1d97547a95f288072914791',
    X / 'run40_20261020.py': '46e3ceea038654e2c9376ded5d95a7fb749fcdc68573a75da29895dc63b77b7b',
    X / 'run52_20261020.py': 'ee29ba60ebeb62a742130d417084d4dbbc1c1bcf0406b8ee3bcb7f946f659530',
    X / 'run64_20261020.py': 'fd4f66ec6edabd0997e05f5cad353bd1382fdaa065cc1d767b101cc93569a24d',
    X / 'correct64_20261020.py': '7236f4abeda30e61f538061525f1e95b74e4ae113fe3fb1f5b2072ff35582102',
    X / 'fresh81_pure.py': '6b9c0e124f4d690c6bd1412aeccfdc8d12b8b20fb2ebe3d0576656c0b59f1e4d',
    E / 'W9b/FRESH-EXCLUSION-INVENTORY-20261021.json': '4176d2611bead517561f0c9b02e9aafae6c7a0a6246a2f99fa4c4eca30d5e9bb',
    # deviation note bindings
    JB / 'MANIFEST.json': 'fece3c06a5d9dde3fe789cf50874c7f115c5920d537f62b77778674542b1208b',
    JB / 'REQUESTS.json': '2ccf7f4fdf80dfa887e160299c23e9970bc0c56cfa882d6138d93915a54c1310',
    JB / 'TRUTHS.json': 'e8a341e484075a874e3ffd97b698afdb3aeb4e74553617950f51d71f3fcb1026',
    JB / 'SUBSET-FREEZE.json': '14b4af069aedf2843a627c373b253e5b056bcbc477d5b4abc301a15cf539e7d0',
    JB / 'PLAN-FREEZE.json': '446b801b2011df59cf86009f4a242e7da9b342778b45fdd1052020c151eb160e',
    JB / 'PRIOR-CLEAN-EXIT.json': '83585055de2a0fde2c38ab3257048f67ac5f8e022fbd45f2a6e01256476caae7',
    BB / 'EXIT.json': 'bcf05a54ae9daf303414affbddb2c8093d8932b939b30dffdee8b54ca2f9c206',
    BA / 'EXIT.json': '78fb5f136a1ce5d215933cd72233d778cce7385f31c2f25d8fd098e72e9d4dd5',
    JA / 'BLOCK-SEALED-METADATA.json': '28f19b435667208d32c22f79e6e49d42b9a28bfd3e0422bd735e648cf702aa3f',
    JA / 'TERMINAL-STATUS-PUBLICATION.json': '448544c4b9855a9e5b2c310c11beca83a5e6e141ca2f95e57674850192b3ebce',
}
for p, h in BOUND.items(): assert H(p) == h, f'ABORT hash mismatch {p}'
J = lambda p: json.loads(Path(p).read_bytes()); ev = lambda i: eval(i) if isinstance(i, str) else i
assert J(BA / 'EXIT.json')['submitted'] == 29681 and J(BB / 'EXIT.json').get('reason') == 'complete', 'ABORT blocks not sealed as stated'

# --- SCORE-ONCE guard, before the first record is read
OUT.mkdir(exist_ok=True)
with open(W / 'SCORE-ONCE-STARTED.json', 'x', encoding='utf8') as g:
    g.write(json.dumps(dict(started=time.strftime('%Y-%m-%d %H:%M:%S %z'), scorer_sha256=H(__file__), prereg='f0aec861', deviation_note='2932f8e6')))

FAMS = ['base', 'surface_gs', 'surface_dlm']; SEED = 21061021; NB = 2000
roster = J(JA / 'ROSTER.json')['selected']; ANS = {r['problem_id']: r['answer'] for r in roster}; PIDS = [r['problem_id'] for r in roster]
pred = {r['pid']: r for r in J(W / 'PREDICTIONS-BEFORE-RECORDS.json')['rows']}; assert list(pred) == PIDS
reqA = {q['identity_sha256']: q for q in J(JA / 'REQUESTS.json')}; truA = J(JA / 'TRUTHS.json')
reqB_list = J(JB / 'REQUESTS.json'); reqB = {q['identity_sha256']: q for q in reqB_list}; truB = J(JB / 'TRUTHS.json')
unsub = set(J(JA / 'BLOCK-SEALED-METADATA.json')['unsubmitted_ids']); comp = [q['identity_sha256'] for q in reqB_list[:2203]]; w2keys = [q['identity_sha256'] for q in reqB_list[2203:]]
assert set(comp) == unsub and all(reqB[k] == reqA[k] for k in comp), 'ABORT completion requests differ'
assert all(Fraction(str(truB[k])) == Fraction(str(truA[k])) for k in comp), 'ABORT completion truths differ'
sub600 = J(JB / 'SUBSET-FREEZE.json')['selected']

def bind(block, reqs, truth, keys):
    files = {p.stem: p for p in (block / 'records').iterdir() if len(p.name) == 69 and p.suffix == '.json'}
    out = {}; seen = set()
    for key in keys:
        q = reqs[key]; qi = ev(q['identity']); v = dict(status='missing', answer=None, correct=None); fin = None; tok = 0; err = None
        if key in files:
            try:
                r = f.envelope(json.loads(files[key].read_bytes()))
                assert r['identity_sha256'] == key and key not in seen, 'key'
                assert ev(r['identity']) == qi and str(r['seed']) == str(q['seed']) and r['request_sha256'] == f.sha(f.canon(q)), 'identity/seed/request'
                assert Fraction(str(truth[key])) == Fraction(str(ANS[qi['problem_id']])), 'truth != roster answer'
                seen.add(key); v = f.parse(r['raw'], r['finish_reason'], r['error'], truth[key]); fin = r['finish_reason']; tok = r['output_tokens']
            except Exception as exc:
                v = dict(status='binding_fail', answer=None, correct=None); err = repr(exc)
        out[key] = dict(key=key, pid=qi['problem_id'], family=qi['family'], replicate=qi['replicate'], finish=fin, tokens=tok, err=err, present=key in files, **v)
    return out, set(files)

drA, filesA = bind(BA, reqA, truA, [k for k in reqA if k not in unsub])
assert filesA <= set(reqA) - unsub, 'ABORT unexpected record names in fresh6h block'
for k in unsub: q = ev(reqA[k]['identity']); drA[k] = dict(key=k, pid=q['problem_id'], family=q['family'], replicate=q['replicate'], finish=None, tokens=0, err=None, present=False, status='not_submitted', answer=None, correct=None)
drB, filesB = bind(BB, reqB, truB, list(reqB))
assert filesB <= set(reqB), 'ABORT unexpected record names in continuation block'

def nonnum(d): return d if d['status'] == 'numeric' else dict(d, correct=None)
def agreement(ds):
    a = [Fraction(d['answer']) for d in ds if d['status'] == 'numeric']
    if not a: return 0.0
    c = collections.Counter(a); top = max(c.values()); return top / len(ds)
def label(draws, pids, reps):
    """Per original: strict n4 tag, n2B side tags, in-wave and side-B base agreement, reached flag."""
    by = collections.defaultdict(list)
    for d in draws.values():
        if d['replicate'] in reps: by[(d['pid'], d['family'])].append(d)
    res = {}
    for pid in pids:
        cells = {fam: [nonnum(d) for d in sorted(by[(pid, fam)], key=lambda d: d['replicate'])] for fam in FAMS}
        assert all([d['replicate'] for d in cells[fam]] == list(reps) for fam in FAMS), pid
        reached = any(d['present'] for fam in FAMS for d in cells[fam]); half = f.sides(cells)
        res[pid] = dict(reached=reached, strict=f.tag(cells, 4), sideA=f.tag(half['A'], 2), sideB=f.tag(half['B'], 2),
                        agree4=agreement(cells['base']), agreeB=agreement(half['B']['base']))
    return res

def kappa(a, b):
    a = np.asarray(a); b = np.asarray(b); po = float(np.mean(a == b)); pe = sum(float(np.mean(a == c)) * float(np.mean(b == c)) for c in ['NR', 'R'])
    return dict(n=int(len(a)), agreement=po, kappa=(po - pe) / (1 - pe) if pe < 1 else None, NR_a=int(np.sum(a == 'NR')), NR_b=int(np.sum(b == 'NR')))

def contrasts(lab, pids, tagkey, b2key):
    """AUCs and gains on binary rows; original bootstrap over all reached originals in pids."""
    P = [p for p in pids if lab[p]['reached']]
    t = np.array([lab[p][tagkey] for p in P]); a4 = np.array([pred[p]['interaction-A4'] for p in P])
    ln = np.array([pred[p]['words'] for p in P], dtype=float); b2 = np.array([1 - lab[p][b2key] for p in P])
    def stat(ix):
        tt = t[ix]; m = np.isin(tt, ['NR', 'R']); y = (tt[m] == 'NR').astype(int)
        aa, al, ab = f.auc(y, a4[ix][m]), f.auc(y, ln[ix][m]), f.auc(y, b2[ix][m])
        return None if None in (aa, al, ab) else (aa, al, ab, aa - al, aa - ab)
    obs = stat(np.arange(len(P))); rng = np.random.default_rng(SEED); bs = []; undef = 0
    for _ in range(NB):
        s = stat(rng.integers(0, len(P), len(P)))
        if s is None: undef += 1
        else: bs.append(s)
    bs = np.array(bs); names = ['AUC_A4', 'AUC_length', 'AUC_baseagree', 'P1_A4_minus_length', 'P2_A4_minus_baseagree']
    m = np.isin(t, ['NR', 'R']); y = (t[m] == 'NR').astype(int)
    out = dict(reached=len(P), binary=int(m.sum()), NR=int(y.sum()), R=int((1 - y).sum()), bootstrap_valid=len(bs), bootstrap_undefined=undef,
               tag_counts=dict(collections.Counter(t.tolist())))
    for i, nm in enumerate(names):
        out[nm] = dict(est=obs[i] if obs else None, ci95=np.percentile(bs[:, i], [2.5, 97.5]).tolist(), ci975=np.percentile(bs[:, i], [1.25, 98.75]).tolist())
    p = a4[m]; out['panel_A4'] = dict(Brier=float(np.mean((p - y) ** 2)), acc05=float(np.mean((p >= .5) == y)), AllR_acc=float(np.mean(y == 0)), NR_prevalence=float(y.mean()))
    return out

def operational(draws, exitj):
    st = collections.Counter(f"{d['family']}|{d['status']}" for d in draws.values())
    return dict(attempts=len(draws), status_by_family=dict(sorted(st.items())), truncated=sum(d['status'] == 'truncated' for d in draws.values()),
                binding_fail=sum(d['status'] == 'binding_fail' for d in draws.values()), missing=sum(d['status'] == 'missing' for d in draws.values()),
                not_submitted=sum(d['status'] == 'not_submitted' for d in draws.values()), output_tokens=sum(d['tokens'] for d in draws.values()),
                exit_new_tokens=exitj.get('new_tokens'), exit_elapsed_s=exitj.get('elapsed'),
                binding_errors=collections.Counter((d['err'] or '')[:60] for d in draws.values() if d['err']).most_common(5))

def splithalf(lab, pids):
    P = [p for p in pids if lab[p]['reached'] and lab[p]['sideA'] in ('NR', 'R') and lab[p]['sideB'] in ('NR', 'R')]
    return kappa([lab[p]['sideA'] for p in P], [lab[p]['sideB'] for p in P])

R = dict(scope='EXPLORATORY; X3-64-matched NOT organiser-matched', prereg='f0aec861', deviation_note='2932f8e6', scorer_sha256=H(__file__), pointK='not computable here: scipy rebuild parity 9.23e-4 (old128) / 7.96e-4 (v2-38) > 1e-6; see PREDICTIONS-BEFORE-RECORDS.json')
# PRIMARY: fresh6h block only
labA = label(drA, PIDS, (0, 1, 2, 3))
R['primary'] = dict(operational=operational(drA, J(BA / 'EXIT.json')), not_reached=sum(not v['reached'] for v in labA.values()),
                    strict=contrasts(labA, PIDS, 'strict', 'agree4'),
                    S1_sideA_label_sideB_agreement=contrasts(labA, PIDS, 'sideA', 'agreeB'),
                    S2_sideA_label_inwave_agreement=contrasts(labA, PIDS, 'sideA', 'agree4'),
                    wave_reliability=dict(originals_with_second_wave=0, note='primary set has replicates 0-3 only', split_half_n2B=splithalf(labA, PIDS)))
# D1: completion merged
drD1 = {k: (drB[k] if k in unsub else drA[k]) for k in reqA}; labD1 = label(drD1, PIDS, (0, 1, 2, 3))
R['D1_completion'] = dict(operational=operational(drD1, {}), not_reached=sum(not v['reached'] for v in labD1.values()), strict=contrasts(labD1, PIDS, 'strict', 'agree4'),
                          split_half_n2B=splithalf(labD1, PIDS))
# D2: wave 2 on the 600
drW2 = {k: drB[k] for k in w2keys}; labW2 = label(drW2, sub600, (4, 5, 6, 7))
t1 = [labD1[p]['strict'] for p in sub600]; t2 = [labW2[p]['strict'] for p in sub600]
both = [i for i in range(600) if t1[i] in ('NR', 'R') and t2[i] in ('NR', 'R')]
R['D2_wave2'] = dict(operational=operational(drW2, J(BB / 'EXIT.json')), cross_table={f'{a}->{b}': c for (a, b), c in sorted(collections.Counter(zip(t1, t2)).items())},
                     agreement_all=float(np.mean(np.array(t1) == np.array(t2))), between_wave_kappa=kappa([t1[i] for i in both], [t2[i] for i in both]),
                     wave1_on_600=contrasts(labD1, sub600, 'strict', 'agree4'), wave2_on_600=contrasts(labW2, sub600, 'strict', 'agree4'))
R['D2_wave2']['operational']['note'] = 'exit tokens cover completion+wave2 together'
(OUT / 'RESULT.json').write_text(json.dumps(R, indent=1, default=float), encoding='utf8', newline='\n')
with open(OUT / 'PER-ORIGINAL.jsonl', 'w', encoding='utf8', newline='\n') as g:
    for p in PIDS: g.write(json.dumps(dict(pid=p, primary=labA[p], D1=labD1[p], W2=labW2.get(p))) + '\n')
with open(OUT / 'DRAWS.jsonl', 'w', encoding='utf8', newline='\n') as g:
    for src, dd in [('fresh6h', drA), ('continuation', drB)]:
        for d in dd.values(): g.write(json.dumps(dict(src=src, **{k: d[k] for k in ['key', 'pid', 'family', 'replicate', 'status', 'answer', 'correct', 'finish', 'tokens']})) + '\n')
print('DONE', H(OUT / 'RESULT.json'))
