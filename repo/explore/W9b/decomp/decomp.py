"""DECOMP (exploratory, CPU). Implements W9b/decomp/DECOMP-SPEC-20261025.md; one execution on real data.
Usage: python decomp.py selftest   (synthetic draws with known p and delta)
       python decomp.py run        (real data, once; refuses if RESULT.json exists or the freeze does not verify)"""
import json, hashlib, pathlib, sys, collections, math
import numpy as np
from scipy.stats import rankdata, binom as BN
EX = pathlib.Path(r'E:\work\research-cycle\explore'); W = EX / 'W9b'; OUT = W / 'decomp'
HF = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
INPUTS = {W / 'ready63rel/out/DRAWS.jsonl': 'e4c66547ecc6ac1aacc9a6921b5611f3e9e183eec7aab6b90e55cf49edaa01b3',
          EX / 'X3/READY63-reviewed-MATH-20261020/MEMBERS-WITH-PROOFS.json': '1b27513c326e7c084c95f5921123d0c957764865804bc3e926b61e483954756d',
          EX / 'X3/fresh81_pure.py': '6b9c0e124f4d690c6bd1412aeccfdc8d12b8b20fb2ebe3d0576656c0b59f1e4d',
          W / 'fresh6h/out/PER-ORIGINAL.jsonl': '0e6a6657b948e78a088bd83d6fc5174ee4f4c239b3e6e110dd54358cd52ed49e',
          W / 'fresh6h/out/DRAWS.jsonl': '3c7bafdb25199f6fe44dbeb0c22c47954a386c01c7a147164aecf7dc8fdeaaf9'}
sys.path.insert(0, str(EX / 'X3')); import fresh81_pure as f
FAMS = ('base', 'surface_gs', 'surface_dlm'); B, SEED = 2000, 20261025

# ---- section 1: the tag under the binomial model ----
def q(pb, pg, pd, n=4):
    """P(NR | binary) for independent Bin(n, p) correct counts per family."""
    b = np.arange(1, n + 1); pmf = BN.pmf(b, n, pb); sg = BN.sf(b - 1, n, pg); sd = BN.sf(b - 1, n, pd)
    den = 1 - (1 - pb) ** n
    return float((pmf * (1 - sg * sd)).sum() / den) if den > 0 else float('nan')
def N0(p, n=4): return q(p, p, p, n)
def corrected(fn, ps, ms, rng, R=2000):
    """bias-corrected fn(p_hat...) by parametric bootstrap: 2*fn(p_hat) - mean fn(p*); also returns var of fn(p*)."""
    plug = fn(*ps); sims = np.array([fn(*[rng.binomial(m, p) / m for p, m in zip(ps, ms)]) for _ in range(R)])
    sims = sims[~np.isnan(sims)]
    return dict(plug=plug, corrected=2 * plug - float(sims.mean()), var=float(sims.var()))

def spear(y, x):
    if np.std(x) == 0 or np.std(y) == 0: return None
    return float(np.corrcoef(rankdata(y), rankdata(x))[0, 1])
def ci(vals):
    v = [x for x in vals if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return dict(ci95=np.quantile(v, [.025, .975]).tolist() if v else None, valid=len(v))
def boot(fn, n, rng, groups=None):
    out = []
    ug = None if groups is None else sorted(set(groups))
    for _ in range(B):
        if groups is None: ix = rng.integers(0, n, n)
        else: ix = np.concatenate([np.where(groups == g)[0] for g in rng.choice(ug, len(ug), replace=True)])
        out.append(fn(ix))
    return ci(out)
def fleiss(counts):
    """counts: list of (nNR, nR) per subject with >= 2 ratings."""
    c = np.array([x for x in counts if sum(x) >= 2], float); n = c.sum(1)
    Pi = ((c * (c - 1)).sum(1)) / (n * (n - 1)); pj = c.sum(0) / n.sum(); Pe = (pj ** 2).sum()
    return float((Pi.mean() - Pe) / (1 - Pe)) if Pe < 1 else None
def kappa_implied(qs, vs, ns):
    """expected Fleiss kappa if tag_i ~ Bernoulli(q_i) iid over waves; vs = estimation variance of q_i (subtracted)."""
    qs, vs, ns = map(np.asarray, (qs, vs, ns)); pbar = (ns * qs).sum() / ns.sum()
    Pi = qs ** 2 + (1 - qs) ** 2 - 2 * vs; Pe = pbar ** 2 + (1 - pbar) ** 2
    return float((Pi.mean() - Pe) / (1 - Pe))

# ---- data ----
def ready63_cells(draws):
    by = collections.defaultdict(lambda: collections.defaultdict(list))
    for d in draws: by[d['pid']][((d['replicate'] - 1000) // 4, d['family'])].append(d)
    return by
def acc(ds, numeric_only):
    if numeric_only: ds = [d for d in ds if d['status'] == 'numeric']
    return (sum(d['status'] == 'numeric' and d['correct'] == 1 for d in ds), len(ds))

def analyse(draws, members, rng):
    by = ready63_cells(draws); tmpl = {m['problem_id']: m['template_family'] for m in members}
    rows = []
    for pid in sorted(by):
        cells = by[pid]; waves = sorted({w for w, _ in cells})
        tags = {w: f.tag({fm: [dict(status=d['status'], correct=d['correct'] or 0) for d in sorted(cells[(w, fm)], key=lambda d: d['replicate'])] for fm in FAMS}, 4) for w in waves}
        ev = [tags[w] for w in waves if w % 2 == 0 and tags[w] in ('NR', 'R')]
        fam = lambda fm, par, num: acc([d for w in waves if par is None or w % 2 == par for d in cells[(w, fm)]], num)
        odd = {fm: fam(fm, 1, True) for fm in FAMS}; allnum = {fm: fam(fm, None, True) for fm in FAMS}; allsolve = {fm: fam(fm, None, False) for fm in FAMS}
        rows.append(dict(pid=pid, template=tmpl[pid], n_even_binary=len(ev), nNR_even=ev.count('NR'), Y=(ev.count('NR') / len(ev)) if ev else None,
                         odd=odd, allnum=allnum, allsolve=allsolve))
    use = [r for r in rows if r['n_even_binary'] >= 5]; n = len(use)
    for r in use:
        (cb, mb), (cg, mg), (cd, md) = (r['odd'][fm] for fm in FAMS)
        pb, pg, pd = cb / mb, cg / mg, cd / md; pp = (cb + cg + cd) / (mb + mg + md)
        r['p_b'], r['p_g'], r['p_d'], r['p_pool'] = pb, pg, pd, pp
        r['N0_base'] = corrected(lambda a: N0(a), [pb], [mb], rng); r['N0_pool'] = corrected(lambda a: N0(a), [pp], [mb + mg + md], rng)
        r['Q1'] = corrected(lambda a, b, c: q(a, b, c), [pb, pg, pd], [mb, mg, md], rng)
    Y = np.array([r['Y'] for r in use]); G = np.array([r['template'] for r in use])
    get = lambda k, s='corrected': np.array([r[k][s] for r in use])
    Nb, Np, Q1 = get('N0_base'), get('N0_pool'), get('Q1'); Nbp, Npp, Q1p = get('N0_base', 'plug'), get('N0_pool', 'plug'), get('Q1', 'plug')
    res = dict(n_used=n, n_originals=len(rows), excluded=[r['pid'] for r in rows if r['n_even_binary'] < 5])
    mean_ci = lambda x: dict(est=float(x.mean()), ci_original=boot(lambda ix: float(x[ix].mean()), n, rng), ci_template=boot(lambda ix: float(x[ix].mean()), n, rng, G))
    res['B1'] = dict(E_base=mean_ci(Y - Nb), E_pool=mean_ci(Y - Np), E_base_minus_E_pool=mean_ci(Np - Nb),
                     plug_in=dict(E_base=float((Y - Nbp).mean()), E_pool=float((Y - Npp).mean())),
                     mean_p_b=float(np.mean([r['p_b'] for r in use])), mean_p_pool=float(np.mean([r['p_pool'] for r in use])))
    res['B2'] = dict(rho_base=spear(Y, Nb), rho_base_ci=boot(lambda ix: spear(Y[ix], Nb[ix]), n, rng),
                     rho_pool=spear(Y, Np), rho_pool_ci=boot(lambda ix: spear(Y[ix], Np[ix]), n, rng),
                     rho_Q1=spear(Y, Q1), rho_Q1_ci=boot(lambda ix: spear(Y[ix], Q1[ix]), n, rng),
                     diff_base_minus_pool_ci=boot(lambda ix: (lambda a, b: None if a is None or b is None else a - b)(spear(Y[ix], Nb[ix]), spear(Y[ix], Np[ix])), n, rng))
    X = np.c_[np.ones(n), Nb]; co = np.linalg.lstsq(X, Y, rcond=None)[0]; pr = X @ co
    res['B3'] = dict(intercept=float(co[0]), slope=float(co[1]), R2=float(1 - ((Y - pr) ** 2).sum() / ((Y - Y.mean()) ** 2).sum()))
    parts = dict(null_at_base=Nb, edit_component=Q1 - Nb, residual=Y - Q1)
    res['B4'] = dict(mean_Y=mean_ci(Y), **{k: dict(**mean_ci(v), share=float(v.mean() / Y.mean())) for k, v in parts.items()})
    ns = np.array([r['n_even_binary'] for r in use])
    res['B5'] = dict(kappa_observed_even=fleiss([(r['nNR_even'], r['n_even_binary'] - r['nNR_even']) for r in use]),
                     kappa_observed_ci=boot(lambda ix: fleiss([(use[i]['nNR_even'], use[i]['n_even_binary'] - use[i]['nNR_even']) for i in ix]), n, rng),
                     kappa_implied_N0_base=kappa_implied(Nb, get('N0_base', 'var'), ns), kappa_implied_Q1=kappa_implied(Q1, get('Q1', 'var'), ns),
                     kappa_implied_Y_even_naive=kappa_implied(Y, Y * (1 - Y) / ns, ns))
    # ---- D: edit-induced change in solve probability, all originals, all waves ----
    D = {}
    for label, key in (('solve', 'allsolve'), ('numeric_only', 'allnum')):
        d_hat, se2, per = [], [], []
        for r in rows:
            (cb, mb), (cg, mg), (cd, md) = (r[key][fm] for fm in FAMS); pb, pg, pd = cb / mb, cg / mg, cd / md
            dg, dd = pb - pg, pb - pd; sg = pb * (1 - pb) / mb + pg * (1 - pg) / mg; sd = pb * (1 - pb) / mb + pd * (1 - pd) / md
            de = (dg + dd) / 2; se = (pb * (1 - pb) / mb) + (pg * (1 - pg) / mg + pd * (1 - pd) / md) / 4
            d_hat.append(de); se2.append(se)
            per.append(dict(pid=r['pid'], p_b=pb, p_g=pg, p_d=pd, delta_gs=dg, z_gs=dg / math.sqrt(sg) if sg > 0 else None,
                            delta_dlm=dd, z_dlm=dd / math.sqrt(sd) if sd > 0 else None, delta_edit=de, se_edit=math.sqrt(se)))
        dh, s2 = np.array(d_hat), np.array(se2); m = len(dh); Gt = np.array([tmpl[r['pid']] for r in rows])
        tau2 = lambda ix: max(0.0, float(np.var(dh[ix], ddof=1) - s2[ix].mean()))
        zs = [abs(x[k]) > 1.96 for x in per for k in ('z_gs', 'z_dlm') if x[k] is not None]
        D[label] = dict(n=m, mean_delta=float(dh.mean()), ci_original=boot(lambda ix: float(dh[ix].mean()), m, rng), ci_template=boot(lambda ix: float(dh[ix].mean()), m, rng, Gt),
                        tau=math.sqrt(tau2(np.arange(m))), tau_ci=boot(lambda ix: math.sqrt(tau2(ix)), m, rng),
                        var_delta_hat=float(np.var(dh, ddof=1)), mean_se2=float(s2.mean()),
                        n_tests=len(zs), n_abs_z_gt_1_96=int(sum(zs)), expected_under_null=0.05 * len(zs), per_original=per)
    D1 = D['solve']; tau = D1['tau']
    # D2: share of the single-tag NR probability that is edit vs null (all waves, numeric-only accuracy as the tag uses)
    qi, n0i = [], []
    for r in rows:
        (cb, mb), (cg, mg), (cd, md) = (r['allnum'][fm] for fm in FAMS); pb, pg, pd = cb / mb, cg / mg, cd / md
        qi.append(q(pb, pg, pd)); n0i.append(N0(pb))
    qi, n0i = np.array(qi), np.array(n0i); ok = ~np.isnan(qi) & ~np.isnan(n0i); qi, n0i = qi[ok], n0i[ok]
    D2 = dict(n=int(ok.sum()), mean_q=float(qi.mean()), mean_N0=float(n0i.mean()), edit_share_of_NR=float((qi - n0i).sum() / qi.sum()),
              var_q=float(qi.var()), var_edit_component=float((qi - n0i).var()), var_share_edit=float((qi - n0i).var() / qi.var()),
              tag_reliability_for_edit=float((qi - n0i).var() / (qi.mean() * (1 - qi.mean()))),
              tag_reliability_total=float(qi.var() / (qi.mean() * (1 - qi.mean()))))
    # D3: design guidance [C]
    P = [0.5, 0.8, 0.9, 0.95, 0.99]; DL = [0.02, 0.05, 0.1, 0.2]; NS = [1, 2, 4, 8, 16, 32, 64]
    pbar = float(np.mean([x['p_b'] for x in D1['per_original']]))
    rel = lambda nn: tau ** 2 / (tau ** 2 + 2 * pbar * (1 - pbar) / nn) if tau > 0 else 0.0
    Kr = lambda r, rr: None if r * math.sqrt(rr) <= 0 else math.ceil((2.8 / math.atanh(r * math.sqrt(rr))) ** 2 + 3)
    D3 = dict(LR_single_NR={f'{p}': {f'{d}': q(p, p - d, p - d) / N0(p) for d in DL if p - d > 0} for p in P},
              N0_by_n={f'{p}': {str(k): N0(p, k) for k in NS} for p in P},
              power_by_n_delta_0_05={f'{p}': {str(k): q(p, p - 0.05, p - 0.05, k) for k in NS} for p in P},
              draws_per_arm={f'{p}': {f'{d}': math.ceil(2.8 ** 2 * 2 * p * (1 - p) / d ** 2) for d in DL} for p in P},
              pbar=pbar, tau=tau,
              problems_for_mean_delta={f'{d}': {str(k): math.ceil(2.8 ** 2 * (tau ** 2 + 2 * pbar * (1 - pbar) / k) / d ** 2) for k in (4, 16, 64, 256)} for d in DL},
              reliability_delta_hat={str(k): rel(k) for k in (4, 16, 64, 256)},
              problems_for_predictor_r={f'{r}': dict(**{f'delta_hat_n{k}': Kr(r, rel(k)) for k in (4, 16, 64, 256)},
                                                     strict_tag_n4_edit_component=Kr(r, D2['tag_reliability_for_edit'])) for r in (0.2, 0.3, 0.5)})
    res['D'] = dict(D1=D, D2=D2, D3=D3)
    res['per_original'] = [{k: v for k, v in r.items() if k not in ('odd', 'allnum', 'allsolve')} | dict(odd=r['odd']) for r in use]
    return res

def fresh6h_S1(po, draws, rng):
    w2 = collections.defaultdict(lambda: collections.defaultdict(list))
    for d in draws:
        if d['src'] == 'continuation' and d['replicate'] >= 4: w2[d['pid']][d['family']].append(d)
    ys, nb, npool = [], [], []
    for p, x in po.items():
        if not (x.get('D1') and x['D1'].get('reached') and x['D1']['strict'] in ('NR', 'R') and x.get('W2')): continue
        if not all(len(w2[p][fm]) == 4 for fm in FAMS): continue
        cn = {fm: [d['correct'] == 1 for d in w2[p][fm] if d['status'] == 'numeric'] for fm in FAMS}
        if not cn['base']: continue
        pb = float(np.mean(cn['base'])); pp = sum(map(sum, cn.values())) / sum(map(len, cn.values()))
        ys.append(int(x['D1']['strict'] == 'NR')); nb.append(N0(pb)); npool.append(N0(pp))
    y, a, b = np.array(ys), np.array(nb), np.array(npool); n = len(y)
    a = np.nan_to_num(a, nan=1.0)  # base 0/4 correct -> N0 undefined; treat as maximal (FLOOR-like) risk
    return dict(n=n, NR=int(y.sum()), auc_base=f.auc(y, a), auc_base_ci=boot(lambda ix: f.auc(y[ix], a[ix]), n, rng),
                auc_pool=f.auc(y, b), auc_pool_ci=boot(lambda ix: f.auc(y[ix], b[ix]), n, rng),
                diff_ci=boot(lambda ix: (lambda u, v: None if u is None or v is None else u - v)(f.auc(y[ix], a[ix]), f.auc(y[ix], b[ix])), n, rng),
                base_zero_of_4=int(sum(np.isnan(np.array(nb)))))

def selftest():
    assert abs(N0(.99) - 0.0742) < 1e-3 and abs(N0(1.0)) < 1e-12
    assert abs(N0(0.7, 400) - 2 / 3) < 0.03, N0(0.7, 400)
    rng = np.random.default_rng(1); draws, members = [], []
    truth = {}
    for i in range(34):
        p = rng.uniform(0.5, 0.99); dlt = 0.05 if i % 2 else 0.0; pid = f'syn-{i}'; truth[pid] = dlt
        members.append(dict(problem_id=pid, template_family=f't{i % 25}'))
        for fm in FAMS:
            pf = p if fm == 'base' else max(0, p - dlt)
            for r in range(1000, 1400):
                num = rng.random() > 0.02
                draws.append(dict(pid=pid, family=fm, replicate=r, status='numeric' if num else 'abstain', correct=int(num and rng.random() < pf)))
    global B; B = 200
    res = analyse(draws, members, np.random.default_rng(2))
    m = res['D']['D1']['solve']['mean_delta']; assert abs(m - 0.025) < 0.012, m
    assert res['B4']['residual']['ci_original']['ci95'][0] < 0 < res['B4']['residual']['ci_original']['ci95'][1], res['B4']['residual']
    print('selftest ok: mean delta', round(m, 4), 'tau', round(res['D']['D1']['solve']['tau'], 4), '(true 0.025)',
          'E_base', round(res['B1']['E_base']['est'], 4), 'E_pool', round(res['B1']['E_pool']['est'], 4), 'residual', round(res['B4']['residual']['est'], 4),
          'kappa obs', round(res['B5']['kappa_observed_even'], 3), 'implied Q1', round(res['B5']['kappa_implied_Q1'], 3))

def run():
    fr = OUT / 'DECOMP-FREEZE.sha256'
    for line in fr.read_text().splitlines():
        h, p = line.split(None, 1); assert HF(OUT / p.strip().lstrip('*')) == h, ('freeze', p)
    for p, h in INPUTS.items(): assert HF(p) == h, ('input hash', p)
    out = OUT / 'RESULT.json'; assert not out.exists(), 'single execution: RESULT.json exists'
    (OUT / 'RUN-STARTED.json').write_text(json.dumps(dict(freeze=HF(fr), script=HF(__file__))))
    rng = np.random.default_rng(SEED)
    draws = [json.loads(l) for l in open(W / 'ready63rel/out/DRAWS.jsonl', encoding='utf-8')]
    members = json.loads((EX / 'X3/READY63-reviewed-MATH-20261020/MEMBERS-WITH-PROOFS.json').read_text(encoding='utf-8'))
    res = analyse(draws, members, rng)
    po = {x['pid']: x for x in map(json.loads, open(W / 'fresh6h/out/PER-ORIGINAL.jsonl', encoding='utf-8'))}
    fd = [json.loads(l) for l in open(W / 'fresh6h/out/DRAWS.jsonl', encoding='utf-8')]
    res['S1'] = fresh6h_S1(po, fd, rng)
    res = dict(freeze_sha256=HF(fr), script_sha256=HF(__file__), inputs={str(p): h for p, h in INPUTS.items()}, **res)
    out.write_text(json.dumps(res, indent=1, default=float)); print(HF(out))

if __name__ == '__main__':
    selftest() if sys.argv[1] == 'selftest' else run()
