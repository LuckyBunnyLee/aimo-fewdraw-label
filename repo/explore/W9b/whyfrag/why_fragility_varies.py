"""WHY-FRAGILITY-VARIES (exploratory, CPU). Implements W9b/WHY-FRAGILITY-VARIES-SPEC-20261023.md; one execution on real data.
Usage: python why_fragility_varies.py selftest   (synthetic draws only)
       python why_fragility_varies.py run        (real data, once; refuses if RESULT.json exists)"""
import json, hashlib, pathlib, re, sys, collections, math
from fractions import Fraction
import numpy as np
from scipy.stats import rankdata
EX = pathlib.Path(r'E:\work\research-cycle\explore'); W = EX / 'W9b'; OUT = W / 'whyfrag'
HF = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
SPEC = (W / 'WHY-FRAGILITY-VARIES-SPEC-20261023.md', '2746021885e0cae3dfcf02069e98bdbc1a2667a5aa25c7c5c039a061e4734245')
INPUTS = {W / 'ready63rel/out/DRAWS.jsonl': 'e4c66547ecc6ac1aacc9a6921b5611f3e9e183eec7aab6b90e55cf49edaa01b3',
          EX / 'X3/READY63-reviewed-MATH-20261020/MEMBERS-WITH-PROOFS.json': '1b27513c326e7c084c95f5921123d0c957764865804bc3e926b61e483954756d',
          EX / 'X3/fresh81_pure.py': '6b9c0e124f4d690c6bd1412aeccfdc8d12b8b20fb2ebe3d0576656c0b59f1e4d',
          W / 'fresh6h/out/PER-ORIGINAL.jsonl': '0e6a6657b948e78a088bd83d6fc5174ee4f4c239b3e6e110dd54358cd52ed49e',
          W / 'fresh6h/out/DRAWS.jsonl': '3c7bafdb25199f6fe44dbeb0c22c47954a386c01c7a147164aecf7dc8fdeaaf9',
          pathlib.Path('D:/research-cycle/cl-fresh6h-20261021-0935/ROSTER.json'): 'b75af74ab88518e448950a49a089ba7d3af67c0aa038406115fc673241d9b05d'}
sys.path.insert(0, str(EX / 'X3')); import fresh81_pure as f
FAMS = ('base', 'surface_gs', 'surface_dlm'); B, NPERM, SEED = 2000, 2000, 20261023
PROPS = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11']

def binom(k, p, n=4): return math.comb(n, k) * p ** k * (1 - p) ** (n - k)
def nr_prob(pb, pg, pd):
    """P(NR | all 12 numeric, base >= 1) with independent Binomial(4, p) correct counts per family."""
    num = sum(binom(b, pb) * binom(s1, pg) * binom(s2, pd) for b in range(1, 5) for s1 in range(5) for s2 in range(5) if min(s1, s2) < b)
    den = 1 - binom(0, pb)
    return num / den if den > 0 else float('nan')
def to_frac(a):
    try: return Fraction(str(a).strip())
    except (ValueError, ZeroDivisionError): return None
def proof_steps(p): return sum(len(re.sub(r'\s', '', s)) >= 3 for s in re.split(r'\.|;|⇒|=>|→', p or ''))
def text_props(base, gs_text, gs_id, orig_id, answer):
    a = to_frac(answer)
    return dict(L=math.log(len(base.split())), T1=None if a is None else float(a.denominator != 1),
                T2=None if a is None else math.log10(1 + abs(float(a))), T5=float(gs_text.count(gs_id)), T6=float(len(orig_id) == 1))
def draw_props(dr):
    """dr: {family: [draw dicts with status, correct, tokens, wave]} -> T4, T7-T11, N0, N1."""
    acc = {fm: np.mean([d['status'] == 'numeric' and d['correct'] == 1 for d in dr[fm]]) for fm in FAMS}
    cn = {fm: [d['correct'] == 1 for d in dr[fm] if d['status'] == 'numeric'] for fm in FAMS}
    pn = {fm: (np.mean(cn[fm]) if cn[fm] else float('nan')) for fm in FAMS}
    pooled = sum(map(sum, cn.values())) / max(1, sum(map(len, cn.values())))
    per_wave = collections.defaultdict(int)
    for d in dr['base']: per_wave[d['wave']] += int(d['status'] == 'numeric' and d['correct'] == 1)
    cnt = np.array(list(per_wave.values()), float); pb = acc['base']
    var = float(np.var(cnt, ddof=1)) if len(cnt) > 1 else float('nan')
    tok = [d['tokens'] for d in dr['base'] if d.get('tokens')]
    surf = [d for fm in FAMS[1:] for d in dr[fm]]
    return dict(T4=math.log(np.median(tok)) if tok else None, T7=float(pb), T8=var, overdispersion=var / (4 * pb * (1 - pb)) if 0 < pb < 1 else None,
                T9=float(acc['base'] - acc['surface_gs']), T10=float(acc['base'] - acc['surface_dlm']),
                T11=float(np.mean([d['status'] != 'numeric' for d in surf])), N0=nr_prob(pooled, pooled, pooled), N1=nr_prob(pn['base'], pn['surface_gs'], pn['surface_dlm']))

def rk(x): return rankdata(x)
def resid(y, Z):
    if Z is None or Z.shape[1] == 0: return y - y.mean()
    X = np.c_[np.ones(len(y)), Z]; return y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
def pcorr(y, x, Z=None):
    """Spearman (partial if Z): rank everything, residualise on ranked controls, Pearson."""
    if np.std(x) == 0 or np.std(y) == 0: return None
    ry, rx = rk(y), rk(x); RZ = None if Z is None else np.column_stack([rk(z) for z in Z.T])
    a, b = resid(ry, RZ), resid(rx, RZ)
    return None if a.std() == 0 or b.std() == 0 else float(np.corrcoef(a, b)[0, 1])
def boot_ci(fn, n, rng):
    v = []
    for _ in range(B):
        ix = rng.integers(0, n, n); r = fn(ix)
        if r is not None and not (isinstance(r, float) and math.isnan(r)): v.append(r)
    return dict(ci95=np.quantile(v, [.025, .975]).tolist() if v else None, valid=len(v))
def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [None] * len(ps); m = len(ps); run = 0
    for k, i in enumerate(order): run = max(run, min(1, (m - k) * ps[i])); adj[i] = run
    return adj
def logit_coef(y, X):
    X = np.c_[np.ones(len(y)), X]; b = np.zeros(X.shape[1])
    for _ in range(30):
        p = 1 / (1 + np.exp(-X @ b)); H = X.T @ (X * (p * (1 - p))[:, None]) + 1e-8 * np.eye(len(b)); b += np.linalg.solve(H, X.T @ (y - p))
    return float(b[-1])

def ready63(draws, members):
    by = collections.defaultdict(list)
    for d in draws: d = dict(d, wave=(d['replicate'] - 1000) // 4); by[(d['pid'], d['family'])].append(d)
    rows = []
    for m in members:
        pid = m['problem_id']; ws = collections.defaultdict(dict)
        for fm in FAMS:
            for d in by[(pid, fm)]: ws[d['wave']].setdefault(fm, []).append(d)
        tags = {w: f.tag({fm: [dict(status=d['status'], correct=d['correct'] or 0) for d in sorted(c[fm], key=lambda d: d['replicate'])] for fm in FAMS}, 4)
                for w, c in ws.items()}
        def frac(par):
            t = [tags[w] for w in tags if w % 2 == par and tags[w] in ('NR', 'R')]
            return (t.count('NR') / len(t) if t else None), len(t)
        (ye, ne), (yo, no) = frac(0), frac(1)
        odd = {fm: [d for d in by[(pid, fm)] if d['wave'] % 2 == 1] for fm in FAMS}
        mem = {x['family']: x['problem'] for x in m['members']}; c = m['certificate']
        rows.append(dict(pid=pid, template=m['template_family'], Y=ye, n_even_binary=ne, Y_odd=yo, n_odd_binary=no,
                         T3=float(proof_steps(m.get('proof'))), **text_props(mem['base'], mem['surface_gs'], c['gs_identifier'], c['original_identifier'], m['derived_answer']),
                         **draw_props(odd)))
    use = [r for r in rows if r['n_even_binary'] >= 5]
    return rows, use

def analyse_ready63(use, rng):
    n = len(use); Y = np.array([r['Y'] for r in use]); col = lambda k: np.array([np.nan if r[k] is None else r[k] for r in use], float)
    L, N0, N1 = col('L'), col('N0'), col('N1'); out = dict(n=n)
    both = [r for r in use if r['Y_odd'] is not None and r['n_odd_binary'] >= 5]
    sh = pcorr(np.array([r['Y'] for r in both]), np.array([r['Y_odd'] for r in both])); out['split_half'] = dict(n=len(both), rho=sh, spearman_brown=None if sh is None else 2 * sh / (1 + sh))
    A1 = {}
    for k, x in (('N0', N0), ('N1', N1)):
        A1[k] = dict(rho=pcorr(Y, x), ci=boot_ci(lambda ix: pcorr(Y[ix], x[ix]), n, rng))
    X = np.c_[np.ones(n), N0]; coef = np.linalg.lstsq(X, Y, rcond=None)[0]; pred = X @ coef
    A1['ols_Y_on_N0'] = dict(intercept=float(coef[0]), slope=float(coef[1]), R2=float(1 - ((Y - pred) ** 2).sum() / ((Y - Y.mean()) ** 2).sum()))
    A1['mean_Y_minus_N0'] = dict(est=float(np.mean(Y - N0)), ci=boot_ci(lambda ix: float(np.mean(Y[ix] - N0[ix])), n, rng))
    A1['Y_range'] = [float(Y.min()), float(Y.max())]; A1['N0_range'] = [float(N0.min()), float(N0.max())]; A1['N1_range'] = [float(np.nanmin(N1)), float(np.nanmax(N1))]
    out['A1'] = A1
    A2 = {}; perm_p = {}
    for k in ['L'] + PROPS:
        x = col(k); ok = ~np.isnan(x); Yk, xk, Lk, Nk = Y[ok], x[ok], L[ok], N0[ok]; m = int(ok.sum())
        e = dict(n=m, rho=pcorr(Yk, xk), rho_ci=boot_ci(lambda ix: pcorr(Yk[ix], xk[ix]), m, rng))
        if k != 'L':
            e['partial_L'] = pcorr(Yk, xk, Lk[:, None]); e['partial_L_ci'] = boot_ci(lambda ix: pcorr(Yk[ix], xk[ix], Lk[ix][:, None]), m, rng)
            Z = np.c_[Lk, Nk]; obs = pcorr(Yk, xk, Z); e['partial_L_N0'] = obs
            e['partial_L_N0_ci'] = boot_ci(lambda ix: pcorr(Yk[ix], xk[ix], Z[ix]), m, rng)
            if obs is not None:
                null = [pcorr(rng.permutation(Yk), xk, Z) for _ in range(NPERM)]
                perm_p[k] = (1 + sum(v is not None and abs(v) >= abs(obs) - 1e-12 for v in null)) / (1 + NPERM)
        A2[k] = e
    keys = list(perm_p); adj = holm([perm_p[k] for k in keys])
    for k, a in zip(keys, adj): A2[k]['perm_p_L_N0'] = perm_p[k]; A2[k]['holm_p_L_N0'] = a
    out['A2'] = A2
    od = col('overdispersion'); out['overdispersion_median'] = float(np.nanmedian(od)); out['overdispersion_range'] = [float(np.nanmin(od)), float(np.nanmax(od))]
    return out

def fresh6h(po, draws, roster, rng):
    ros = {r['problem_id']: r for r in roster}; out = {}
    w2 = collections.defaultdict(lambda: collections.defaultdict(list))
    for d in draws:
        if d['src'] == 'continuation' and d['replicate'] >= 4: w2[d['pid']][d['family']].append(dict(d, wave=d['replicate'] // 4))
    def rows_for(pids, with_draws):
        rows = []
        for p in pids:
            r = ros[p]; mem = {m['family']: m['problem'] for m in r['members']}; c = r['certificate']; t = po[p]['D1']['strict']
            row = dict(pid=p, y=int(t == 'NR'), **text_props(mem['base'], mem['surface_gs'], c['gs_identifier'], c['original_identifier'], r['answer']))
            if with_draws: row.update(draw_props(w2[p]))
            rows.append(row)
        return rows
    binary = [p for p, x in po.items() if x.get('D1') and x['D1'].get('reached') and x['D1']['strict'] in ('NR', 'R')]
    sets = dict(W2_600=rows_for([p for p in binary if po[p].get('W2') and len(w2[p]['base']) == 4 and all(len(w2[p][fm]) == 4 for fm in FAMS)], True),
                D1_all=rows_for(binary, False))
    for name, rows in sets.items():
        keys = (['L', 'T1', 'T2', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'N0', 'N1'] if name == 'W2_600' else ['L', 'T1', 'T2', 'T5', 'T6'])
        y = np.array([r['y'] for r in rows]); res = dict(n=len(rows), NR=int(y.sum()))
        for k in keys:
            x = np.array([np.nan if r.get(k) is None else r[k] for r in rows], float); ok = ~np.isnan(x); yk, xk = y[ok], x[ok]
            Lk = np.array([r['L'] for r in rows])[ok]; m = int(ok.sum())
            e = dict(n=m, auc=f.auc(yk, xk), auc_ci=boot_ci(lambda ix: f.auc(yk[ix], xk[ix]), m, rng))
            if k != 'L' and np.std(xk) > 0:
                z = lambda a: (a - a.mean()) / a.std() if a.std() > 0 else a * 0
                e['logit_coef_given_L'] = logit_coef(yk, np.c_[z(Lk), z(xk)])
                e['logit_coef_ci'] = boot_ci(lambda ix: logit_coef(yk[ix], np.c_[z(Lk[ix]), z(xk[ix])]) if np.std(xk[ix]) > 0 else None, m, rng)
            res[k] = e
        out[name] = res
    return out

def run(selftest=False):
    rng = np.random.default_rng(SEED)
    if selftest:
        # synthetic: 34 originals, fragility driven only by accuracy (exchangeable) -> N0 should track Y, gaps ~0
        srng = np.random.default_rng(1); draws, members = [], []
        for i in range(34):
            p = srng.uniform(0.4, 0.99); pid = f'syn-{i}'
            members.append(dict(problem_id=pid, template_family='t', proof='a. b; c => d', derived_answer=str(i),
                                certificate=dict(gs_identifier='qq', original_identifier='x'), members=[dict(family=fm, problem='find x qq ' * (1 + i % 5)) for fm in FAMS]))
            for fm in FAMS:
                for r in range(1000, 1400):
                    num = srng.random() > 0.03
                    draws.append(dict(pid=pid, family=fm, replicate=r, status='numeric' if num else 'abstain', correct=int(num and srng.random() < p), tokens=500))
        rows, use = ready63(draws, members); res = analyse_ready63(use, rng)
        assert res['A1']['N0']['rho'] >= res['split_half']['rho'] - 0.1, (res['A1']['N0'], res['split_half']); assert abs(nr_prob(1, 1, 1)) < 1e-12 and abs(nr_prob(.99, .99, .99) - 0.0742) < 1e-3
        print('selftest ok', res['n'], round(res['A1']['N0']['rho'], 3), round(res['split_half']['rho'], 3), res['A2']['T9']['partial_L_N0']); return
    assert HF(SPEC[0]) == SPEC[1], 'spec hash'
    for p, h in INPUTS.items(): assert HF(p) == h, ('input hash', p)
    out = OUT / 'RESULT.json'; assert not out.exists(), 'single execution: RESULT.json exists'
    (OUT / 'RUN-STARTED.json').write_text(json.dumps(dict(spec=SPEC[1], script=HF(__file__))))
    draws = [json.loads(l) for l in open(W / 'ready63rel/out/DRAWS.jsonl', encoding='utf-8')]
    members = json.loads((EX / 'X3/READY63-reviewed-MATH-20261020/MEMBERS-WITH-PROOFS.json').read_text(encoding='utf-8'))
    rows, use = ready63(draws, members); r63 = analyse_ready63(use, rng)
    po = {x['pid']: x for x in map(json.loads, open(W / 'fresh6h/out/PER-ORIGINAL.jsonl', encoding='utf-8'))}
    fd = [json.loads(l) for l in open(W / 'fresh6h/out/DRAWS.jsonl', encoding='utf-8')]
    roster = json.loads(pathlib.Path('D:/research-cycle/cl-fresh6h-20261021-0935/ROSTER.json').read_bytes())['selected']
    f6 = fresh6h(po, fd, roster, rng)
    res = dict(spec_sha256=SPEC[1], script_sha256=HF(__file__), inputs={str(p): h for p, h in INPUTS.items()},
               ready63=dict(n_originals=len(rows), n_used=len(use), excluded=[r['pid'] for r in rows if r['n_even_binary'] < 5], **r63),
               fresh6h=f6, per_original=rows)
    out.write_text(json.dumps(res, indent=1, default=float)); print(HF(out))

if __name__ == '__main__':
    run(selftest=sys.argv[1] == 'selftest')
