"""CAUSAL-LENGTH P1-only scorer (W9b, 23 Oct 2026). EXPLORATORY. CPU only. Frozen and dry-run before any evaluation record exists.
Implements design R2 section 5 restricted to P1 (CAUSAL-LENGTH-AMENDMENT-P1-20261023.md section 3) and the AN-49 P1 readout
(AN49-MECHANISM-PREDICTION-20261023.md sections 2-4).
  real    E_RECORDS FINAL OUT   E_RECORDS: CL job folder (block-*/records/*.json envelopes) or one JSON {identity_sha256: envelope};
                                 SCORE-ONCE: refuses if OUT/SCORE-ONCE-STARTED.json exists; writes OUT/RESULT.json
  dryrun  FINAL SCRATCH          synthetic records under three worlds (H-inert, H-acc, H-rob) and one partial run; asserts the readouts"""
import json, hashlib, pathlib, sys, math, collections, datetime
import numpy as np
HERE = pathlib.Path(__file__).resolve().parent
X3 = HERE.parents[1] / 'X3'; sys.path.insert(0, str(X3))
FRESH81_SHA = hashlib.sha256((X3 / 'fresh81_pure.py').read_bytes()).hexdigest()
import fresh81_pure as fp
F6 = pathlib.Path('D:/research-cycle/cl-fresh6h-20261021-0935'); W = HERE.parent
FAMS = ('base', 'surface_gs', 'surface_dlm'); CONDS = ('control', 'pad'); PER_WAVE, WAVES = 4, 12
NBOOT, SEED = 2000, 20261023
H = lambda b: hashlib.sha256(b).hexdigest(); HF = lambda p: H(pathlib.Path(p).read_bytes())
get = lambda p: json.loads(pathlib.Path(p).read_text(encoding='utf-8'))

def binom(k, p, n=4): return math.comb(n, k) * p ** k * (1 - p) ** (n - k)
def nr_prob(pb, pg, pd):
    """AN-50's N0 (why_fragility_varies.py, unchanged): P(NR | all 12 numeric, base >= 1), independent Binomial(4, p) per family."""
    num = sum(binom(b, pb) * binom(s1, pg) * binom(s2, pd) for b in range(1, 5) for s1 in range(5) for s2 in range(5) if min(s1, s2) < b)
    den = 1 - binom(0, pb)
    return num / den if den > 0 else float('nan')

def obs_gradient():
    """Design section 1, recomputed: logistic fit of fresh6h primary strict NR on log base words, average marginal effect (1,255 rows)."""
    ros = {r['problem_id']: r for r in json.loads((F6 / 'ROSTER.json').read_bytes())['selected']}; y, x = [], []
    for l in open(W / 'fresh6h/out/PER-ORIGINAL.jsonl', encoding='utf-8'):
        r = json.loads(l); p = r['primary'] or {}
        if p.get('reached') and p.get('strict') in ('NR', 'R'):
            b = [m['problem'] for m in ros[r['pid']]['members'] if m['family'] == 'base'][0]; y.append(p['strict'] == 'NR'); x.append(math.log(len(b.split())))
    y, X = np.array(y, float), np.c_[np.ones(len(x)), x]; w = np.zeros(2)
    for _ in range(50):
        pr = 1 / (1 + np.exp(-X @ w)); w += np.linalg.solve((X * (pr * (1 - pr))[:, None]).T @ X, X.T @ (y - pr))
    pr = 1 / (1 + np.exp(-X @ w)); return dict(n=len(y), ame=float(np.mean(w[1] * pr * (1 - pr))))

def load_records(path):
    """{identity_sha256: record}; every envelope checked with fresh81_pure.envelope (record hash, raw hash, token count)."""
    path = pathlib.Path(path); out = {}
    envs = list(get(path).values()) if path.is_file() else [json.loads(f.read_bytes()) for f in sorted(path.glob('block-*/records/*.json'))]
    for e in envs:
        r = fp.envelope(e); assert r['identity_sha256'] not in out, 'duplicate record'; out[r['identity_sha256']] = r
    return out

def cells(final, recs):
    """-> per (pid, cond, wave): None if any of its 12 requests is missing, else dict(tag, base/surface correct counts, accuracy, mediators)."""
    reqs = get(final / 'EVAL-REQUESTS.json'); truths = get(final / 'TRUTHS.json'); idx = {q['identity_sha256']: q for q in reqs}
    assert set(recs) <= set(idx), 'records outside EVAL-REQUESTS'
    g = collections.defaultdict(lambda: collections.defaultdict(list)); words = {}
    for ih, q in idx.items():
        i = q['identity']; key = (i['problem_id'], i['condition'], i['replicate'] // PER_WAVE)
        if i['family'] == 'base': words[(i['problem_id'], i['condition'])] = len(q['problem'].split())
        r = recs.get(ih)
        if r is None: g[key]['_missing'].append(ih); continue
        assert r['identity'] == i, ('identity mismatch', ih)
        d = fp.parse(r['raw'], r['finish_reason'], r.get('error'), truths[ih]); d['tokens'] = r['output_tokens']; g[key][i['family']].append(d)
    out = {}
    for key, v in g.items():
        if v.get('_missing'): out[key] = None; continue
        assert all(len(v[f]) == PER_WAVE for f in FAMS)
        c = {f: [x for x in v[f]] for f in FAMS}; tag = fp.tag(c, PER_WAVE)
        corr = {f: sum(x['correct'] == 1 for x in c[f]) for f in FAMS}
        lt = lambda xs: float(np.mean([math.log(max(x['tokens'], 1)) for x in xs]))
        out[key] = dict(tag=tag, corr=corr, pooled=sum(corr.values()) / 12, med=lt([x for f in FAMS for x in c[f]]), med_base=lt(c['base']))
    return out, words

def per_original(cl, words, pids, wave_set=range(WAVES), unusable_as=None):
    """Per-original condition summaries over original-waves where both conditions' 24 requests are bound (else NOT_REACHED)."""
    res = {}; not_reached = 0
    for p in pids:
        acc = {c: collections.defaultdict(list) for c in CONDS}
        for w in wave_set:
            a, b = cl.get((p, 'control', w)), cl.get((p, 'pad', w))
            if a is None or b is None: not_reached += 1; continue
            for c, x in (('control', a), ('pad', b)):
                t = x['tag'] if not (unusable_as and x['tag'] == 'UNUSABLE') else unusable_as
                d = acc[c]; d['unusable'].append(x['tag'] == 'UNUSABLE'); d['acc_base'].append(x['corr']['base'] / 4)
                d['gap'].append(x['corr']['base'] / 4 - (x['corr']['surface_gs'] + x['corr']['surface_dlm']) / 8); d['med'].append(x['med']); d['med_base'].append(x['med_base'])
                if t in ('NR', 'R'):
                    d['nr'].append(t == 'NR')
                    if x['tag'] in ('NR', 'R'): n0 = nr_prob(x['pooled'], x['pooled'], x['pooled']); d['n0'].append(n0); d['s4'].append((t == 'NR') - n0)
        m = lambda c, k: float(np.mean(acc[c][k])) if acc[c][k] else np.nan
        res[p] = {k: m('pad', k) - m('control', k) for k in ('nr', 'n0', 's4', 'acc_base', 'gap', 'med', 'med_base', 'unusable')}
        res[p]['dlog_words'] = math.log(words[(p, 'pad')] / words[(p, 'control')])
        res[p]['unusable_control'], res[p]['unusable_pad'] = m('control', 'unusable'), m('pad', 'unusable')
    return res, not_reached

def boot_mean(v, ix):
    """v: per-original values (nan = no contribution); ix: NBOOT x n resample index matrix."""
    v = np.asarray(v, float); est = float(np.nanmean(v)) if np.isfinite(v).any() else np.nan
    bs = np.array([np.nanmean(v[i]) if np.isfinite(v[i]).any() else np.nan for i in ix]); bs = bs[np.isfinite(bs)]
    return dict(est=est, n=int(np.isfinite(v).sum()), ci95=np.quantile(bs, [.025, .975]).tolist(), ci975=np.quantile(bs, [.0125, .9875]).tolist())
def boot_fn(fn, n, ix):
    """fn(index array) -> scalar or vector; resamples where any component is not finite are dropped."""
    est = np.atleast_1d(fn(np.arange(n))); bs = np.array([np.atleast_1d(fn(i)) for i in ix], float); bs = bs[np.isfinite(bs).all(1)]
    return dict(est=est.tolist(), ci95=np.quantile(bs, [.025, .975], axis=0).T.tolist(), completed=len(bs))
def ols(y, X):
    ok = np.all(np.isfinite(np.c_[y, X]), 1)
    if ok.sum() <= X.shape[1]: return np.full(X.shape[1], np.nan)
    return np.linalg.lstsq(X[ok], y[ok], rcond=None)[0]

contains = lambda ci, v: ci[0] <= v <= ci[1]
inside = lambda ci, a: -a <= ci[0] and ci[1] <= a
def reading(s):
    if not contains(s['ci975'], 0): return 'a neutral preamble moves NR (' + ('up' if s['est'] > 0 else 'down') + ')'
    if inside(s['ci95'], 0.05): return 'no effect as large as 0.05'
    return 'inconclusive'

def score(final, recs):
    st = get(final / 'P1-COHORT.json'); pids = st['cohort']; tags = {p: st['stimuli'][p]['tag'] for p in pids}
    cl, words = cells(final, recs); n = len(pids)
    ix = np.random.default_rng(SEED).integers(0, n, (NBOOT, n))
    po, nreach = per_original(cl, words, pids); col = lambda k, d=po: np.array([d[p][k] for p in pids], float)
    out = dict(records=len(recs), requests=len(get(final / 'EVAL-REQUESTS.json')), original_waves=n * WAVES, original_waves_not_reached=nreach)
    P1 = boot_mean(col('nr'), ix); out['P1'] = dict(P1, reading=reading(P1))
    sec = out['secondaries'] = {}
    sec['S2_base_accuracy'] = boot_mean(col('acc_base'), ix)
    dl, nr = col('dlog_words'), col('nr'); og = obs_gradient()
    beta = lambda i: (np.nanmean(nr[i]) / np.mean(dl[i][np.isfinite(nr[i])])) if np.isfinite(nr[i]).any() else np.nan
    s3 = boot_fn(beta, n, ix); s3['obs_gradient'] = og; ub = s3['ci95'][0][1]
    s3['reading'] = ('compatible with a fully causal gradient' if contains(s3['ci95'][0], og['ame']) else
                     'less than half of the gradient is causal through input length' if ub < og['ame'] / 2 else 'neither bound reached')
    sec['S3_causal_vs_observational'] = s3
    sec['S4_excess'] = boot_mean(col('s4'), ix); sec['dN0'] = boot_mean(col('n0'), ix)
    sec['S5_family_gap'] = boot_mean(col('gap'), ix)
    sec['S6_unusable'] = dict(control=float(np.nanmean(col('unusable_control'))), pad=float(np.nanmean(col('unusable_pad'))), diff=boot_mean(col('unusable'), ix))
    for k, a in (('as_NR', 'NR'), ('as_R', 'R')):
        pk, _ = per_original(cl, words, pids, unusable_as=a); sec['S6_unusable'][f'P1_unusable_{k}'] = boot_mean(np.array([pk[p]['nr'] for p in pids]), ix)
    sec['S7_strata'] = {t: boot_mean(np.where([tags[p] == t for p in pids], nr, np.nan), ix) for t in ('NR', 'R')}
    med = out['mediation'] = {}
    med['M1_mediator_all12'] = boot_mean(col('med'), ix); med['M1_mediator_base_only'] = boot_mean(col('med_base'), ix)
    ev, _ = per_original(cl, words, pids, range(0, WAVES, 2)); od, _ = per_original(cl, words, pids, range(1, WAVES, 2))
    E = {k: col(k, ev) for k in ('nr', 'n0', 's4', 'med')}; O = {k: col(k, od) for k in ('nr', 'n0', 's4', 'med')}; mmed = col('med')
    one = np.ones(n)
    def xfit(ycol, xcols):
        """cross-fitted: y from even waves with x from odd, then the reverse; coefficients averaged."""
        def f(i):
            c1 = ols(E[ycol][i], np.c_[one[i], *[O[x][i] for x in xcols]]); c2 = ols(O[ycol][i], np.c_[one[i], *[E[x][i] for x in xcols]]); return (c1 + c2) / 2
        return f
    def m2(ycol):
        f = xfit(ycol, ['med'])
        def g(i): a, b = f(i); return np.array([a, b, b * np.nanmean(mmed[i])])
        r = boot_fn(g, n, ix); return dict(direct_a=dict(est=r['est'][0], ci95=r['ci95'][0]), b=dict(est=r['est'][1], ci95=r['ci95'][1]), indirect=dict(est=r['est'][2], ci95=r['ci95'][2]))
    med['M2'] = m2('nr'); M1 = med['M1_mediator_all12']
    if not contains(P1['ci975'], 0):
        if inside(M1['ci95'], 0.05): m3 = 'the neutral preamble acts through the input, not through response length'
        elif not contains(M1['ci95'], 0) and np.sign(M1['est']) == np.sign(med['M2']['indirect']['est']) and not contains(med['M2']['indirect']['ci95'], 0):
            m3 = 'consistent with response-length mediation of the preamble effect'
        else: m3 = 'mixed; reported as observed'
    elif inside(P1['ci95'], 0.05): m3 = 'at this dose, a neutral preamble does not move NR; the observational length association is a marker (difficulty, verbosity or design)'
    else: m3 = 'mixed; reported as observed'
    med['M3_readout'] = m3
    # AN-49 (P1 only); every interval here is 95%
    a = out['AN49'] = {}; S2, S4, S5 = sec['S2_base_accuracy'], sec['S4_excess'], sec['S5_family_gap']
    a['pred1_dS4_contains_0'] = contains(S4['ci95'], 0)
    a['pred2'] = ('not applicable: S2 contains 0' if contains(S2['ci95'], 0) else
                  'refuted: same sign as S2, both exclude 0' if (not contains(P1['ci95'], 0) and np.sign(P1['est']) == np.sign(S2['est'])) else 'holds')
    a['pred4_S5_contains_0'] = contains(S5['ci95'], 0)
    tr = boot_fn(xfit('nr', ['n0']), n, ix); a['pred5_tracking'] = dict(intercept=dict(est=tr['est'][0], ci95=tr['ci95'][0]), slope=dict(est=tr['est'][1], ci95=tr['ci95'][1]),
                                                                       holds=contains(tr['ci95'][0], 0) and contains(tr['ci95'][1], 1))
    a['M2_S4'] = m2('s4'); a['M2_S4']['holds'] = contains(a['M2_S4']['direct_a']['ci95'], 0) and contains(a['M2_S4']['indirect']['ci95'], 0)
    mn = boot_fn(xfit('nr', ['med', 'n0']), n, ix)
    a['M2_plus_N0'] = dict(a=dict(est=mn['est'][0], ci95=mn['ci95'][0]), b=dict(est=mn['est'][1], ci95=mn['ci95'][1]), c_N0=dict(est=mn['est'][2], ci95=mn['ci95'][2]),
                           holds=contains(mn['ci95'][1], 0) and contains(mn['ci95'][2], 1))
    if not contains(S2['ci95'], 0) and contains(S4['ci95'], 0): r = 'H-acc supported: the preamble altered difficulty, and NR moved mechanically'
    elif not contains(S4['ci95'], 0) and np.sign(S4['est']) == np.sign(P1['est']): r = 'H-acc refuted for P1: robustness moved beyond accuracy (H-rob)'
    elif contains(S2['ci95'], 0) and inside(S2['ci95'], 0.02) and contains(S4['ci95'], 0) and inside(P1['ci95'], 0.05): r = 'H-inert: H-acc is not tested by P1'
    else: r = 'mixed; reported as observed'
    a['readout'] = r
    return out

def scorer_meta(final):
    fz = get(final / 'EVAL-FREEZE.json')
    for k, h in fz['files'].items(): assert HF(final / k) == h, ('frozen file changed', k)
    return dict(scorer_sha256=HF(__file__), fresh81_pure_sha256=FRESH81_SHA, eval_freeze_sha256=HF(final / 'EVAL-FREEZE.json'))

# ---------- dry run ----------
def synth(final, world, seed, drop_last_waves=0):
    """Synthetic envelopes. Per-original accuracy p ~ Beta; world sets how pad changes each family's accuracy."""
    rng = np.random.default_rng(seed); reqs = get(final / 'EVAL-REQUESTS.json'); truths = get(final / 'TRUTHS.json')
    pids = sorted({q['identity']['problem_id'] for q in reqs}); p = dict(zip(pids, np.clip(rng.beta(6, 1.2, len(pids)), 0, 0.995)))
    shift = dict(inert=dict(base=0, surf=0), acc=dict(base=-0.06, surf=-0.06), rob=dict(base=0, surf=-0.10))[world]
    out = {}
    for q in reqs:
        i = q['identity']
        if i['replicate'] // PER_WAVE >= WAVES - drop_last_waves: continue
        pp = p[i['problem_id']] + (0 if i['condition'] == 'control' else shift['base' if i['family'] == 'base' else 'surf'])
        ok = rng.random() < pp; ans = truths[q['identity_sha256']] if ok else str(int(rng.integers(10 ** 6, 10 ** 7)))
        if rng.random() < 0.004: raw, fin = 'no answer line', 'stop'
        else: raw, fin = f'Work.\nANSWER: {ans}', 'stop'
        ntok = int(rng.integers(20, 60) * (1.15 if i['condition'] == 'pad' else 1))
        r = dict(identity=i, identity_sha256=q['identity_sha256'], raw=raw, raw_sha256=H(raw.encode()), finish_reason=fin, error=None, output_tokens=ntok, token_ids=[0] * ntok)
        out[q['identity_sha256']] = dict(record=r, record_sha256=H(fp.canon(r)))
    return out

def dryrun(final, scratch):
    scratch.mkdir(parents=True, exist_ok=True); meta = scorer_meta(final); summ = {}
    og = obs_gradient(); assert og['n'] == 1255 and abs(og['ame'] - 0.116) < 0.001, og
    assert abs(nr_prob(.99, .99, .99) - 0.0742) < 1e-3 and abs(nr_prob(1, 1, 1)) < 1e-12
    # folder form with envelopes: same loader result as the file form
    env = synth(final, 'inert', 1, drop_last_waves=11); fold = scratch / 'JOB' / 'block-1' / 'records'; fold.mkdir(parents=True, exist_ok=True)
    for k, v in list(env.items())[:50]: (fold / f'{k}.json').write_text(json.dumps(v), encoding='utf-8')
    assert set(load_records(scratch / 'JOB')) == set(list(env)[:50])
    bad = dict(list(env.items())[:1]); k = next(iter(bad)); bad[k] = dict(bad[k], record_sha256='0' * 64); (scratch / 'BAD.json').write_text(json.dumps(bad), encoding='utf-8')
    try: load_records(scratch / 'BAD.json'); accepted = True
    except AssertionError: accepted = False
    assert not accepted, 'bad envelope accepted'
    for world, seed in (('inert', 11), ('acc', 12), ('rob', 13)):
        p = scratch / f'SYNTH-{world}.json'; p.write_text(json.dumps(synth(final, world, seed)), encoding='utf-8')
        r = score(final, load_records(p)); summ[world] = r
        print(world, r['P1']['est'], r['P1']['reading'], '| S2', round(r['secondaries']['S2_base_accuracy']['est'], 4), '| S4', round(r['secondaries']['S4_excess']['est'], 4),
              r['secondaries']['S4_excess']['ci95'], '| S5', round(r['secondaries']['S5_family_gap']['est'], 4), '|', r['AN49']['readout'], '| M3', r['mediation']['M3_readout'])
    i, a, b = summ['inert'], summ['acc'], summ['rob']
    assert i['P1']['reading'] == 'no effect as large as 0.05' and i['AN49']['readout'].startswith('H-inert'), i['AN49']
    assert a['P1']['est'] > 0 and a['AN49']['readout'].startswith('H-acc supported') and a['AN49']['pred4_S5_contains_0'], a['AN49']
    assert b['AN49']['readout'].startswith('H-acc refuted') and not b['AN49']['pred4_S5_contains_0'], b['AN49']
    assert i['original_waves_not_reached'] == 0 and i['records'] == i['requests']
    for r in summ.values(): assert abs(r['P1']['est'] - (r['secondaries']['dN0']['est'] + r['secondaries']['S4_excess']['est'])) < 1e-9, 'P1 = dN0 + dS4 by construction'
    # partial run: the last 2 waves missing -> NOT_REACHED counted, still scores
    p = scratch / 'SYNTH-partial.json'; p.write_text(json.dumps(synth(final, 'acc', 14, drop_last_waves=2)), encoding='utf-8')
    r = score(final, load_records(p)); assert r['original_waves_not_reached'] == 160 * 2, r['original_waves_not_reached']
    res = dict(meta, worlds={k: dict(P1=v['P1'], AN49_readout=v['AN49']['readout'], S4=v['secondaries']['S4_excess'], S5=v['secondaries']['S5_family_gap'],
                                    M3=v['mediation']['M3_readout']) for k, v in summ.items()}, partial_not_reached=r['original_waves_not_reached'], obs_gradient=og)
    (scratch / 'DRYRUN-RESULT.json').write_text(json.dumps(res, indent=1, default=float), encoding='utf-8'); print('dry run ok')

def real(e_records, final, out):
    out.mkdir(parents=True, exist_ok=True); meta = scorer_meta(final)
    with (out / 'SCORE-ONCE-STARTED.json').open('x', encoding='utf-8') as fh:
        json.dump(dict(meta, started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), e_records=str(e_records)), fh, indent=1)
    recs = load_records(e_records); res = dict(meta, **score(final, recs))
    with (out / 'RESULT.json').open('x', encoding='utf-8') as fh: json.dump(res, fh, indent=1, default=float)
    print(json.dumps(dict(P1=res['P1'], AN49=res['AN49']['readout'], M3=res['mediation']['M3_readout']), indent=1, default=float))

if __name__ == '__main__':
    if sys.argv[1] == 'dryrun': dryrun(pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]))
    elif sys.argv[1] == 'real': real(pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), pathlib.Path(sys.argv[4]))
