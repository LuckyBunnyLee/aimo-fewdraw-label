"""One-shot scorer for explore/W9b/THINKREP-SPEC-20261024-r2.md (W9b; r1 frozen 24 Oct 2026, r2 re-frozen the same day
after the V14 design review, both before any output existed).
  python -B score_thinkrep.py RUN_DIR                         real run: writes only explore/W9b/thinkrep/out (once)
  python -B score_thinkrep.py RUN_DIR --dry-run STATE_DIR     synthetic records only; writes STATE_DIR/out
Every bound hash is checked before any record is opened; the SCORE-ONCE guard is written first.
r2: refuses unless the attempt's gate said CONTINUE or STOP (never ABORT_ENGINE) and the final engine check matches the
run's current record fingerprint and allows scoring; reads only the waves before an engine cut (waves 0-1 after a STOP)."""
import collections, json, sys, time
from pathlib import Path
import numpy as np
from scipy import optimize, special, stats
import thinkrep_core as C

f = C.f; E = C.E; TR = C.TR
RUN = Path(sys.argv[1]); STATE, DRY = C.state_dir(sys.argv); OUT = STATE / 'out'
assert not OUT.exists(), 'one-shot guard: output folder exists'

# ---- bound inputs (spec section 3); FREEZE-r2 lists spec r2, scorer, gate, engine check, core, parser, requests, truths, cohort
FREEZE = C.FREEZE; C.check_freeze(__file__)
COMP = {E / 'W9b/ready63rel/out/RESULT.json': '98ebc88e7d7ce4d5aca91916fe4dfa8fa28d12c6f7a54fb21ae0403c1d31ac25',
        E / 'M1b/NOISE-CEILING-RESULT-20261021.json': '2b773b9c8316e77826b9c531c7f6f761a2323bdef293e86ed05b9a5c57bb8777',
        E.parent / 'pair/aimo/report/numbers/m1h-t002.json': 'c92d2b1ab7e4da0cb47cd9e5b42289a125742029fea32d5683034ab8f6c30335',
        E / 'X3/afternoon-20261020/64/PREDICTIONS-V2-BEFORE-FRESH-OUTCOMES.json': '833f74c8d34a2450831f1f1f30c07c29180e9f691d41087997566cc8ad4d90bb',
        E / 'X3/fresh81_pure.py': '6b9c0e124f4d690c6bd1412aeccfdc8d12b8b20fb2ebe3d0576656c0b59f1e4d'}
for p, h in COMP.items():
    assert C.H(p) == h, f'ABORT hash mismatch {p}'
ATTEMPT, MAN_SHA = C.run_manifest(RUN)  # the run folder's own manifest names the attempt and our request and truth files
GATE = C.J(STATE / 'gate' / f'GATE-RESULT-a{ATTEMPT}.json'); ENG = C.J(STATE / 'engine' / f'ENGINE-CHECK-a{ATTEMPT}.json')
assert GATE['decision'] in ('CONTINUE', 'STOP'), 'ABORT no scoring after ABORT_ENGINE'
assert GATE['run_manifest_sha256'] == MAN_SHA == ENG['run_manifest_sha256'], 'ABORT gate / engine check from another run folder'
assert ENG['record_fingerprint'] == C.fingerprint(RUN)[0], 'ABORT records changed since the engine check; rerun engine_check.py'
assert ENG['scorer_may_run'] and ENG['gate_decision'] == GATE['decision'], 'ABORT engine check does not allow scoring'
MAX_WAVE = 2 if GATE['decision'] == 'STOP' else (ENG['cut_at_wave'] if ENG['cut_at_wave'] is not None else C.WAVES)
reqs, truths, cohort = C.frozen(ATTEMPT)
run_files = {str(p.relative_to(RUN)): C.H(p) for p in sorted(RUN.glob('*.json')) + sorted(RUN.glob('block-*/*.json'))}
OUT.mkdir(parents=True)
(OUT / 'SCORE-ONCE-STARTED.json').write_text(json.dumps(dict(started=time.time(), dry_run=DRY, run=str(RUN), attempt=ATTEMPT, max_wave=MAX_WAVE,
                                                             run_level_json_sha256=run_files, freeze_sha256=C.H(FREEZE),
                                                             gate_sha256=C.H(STATE / 'gate' / f'GATE-RESULT-a{ATTEMPT}.json'),
                                                             engine_check_sha256=C.H(STATE / 'engine' / f'ENGINE-CHECK-a{ATTEMPT}.json'))), encoding='utf-8')

# ---- bind, parse, tag (spec sections 4-5)
draws, status, fails, layout = C.load(RUN, reqs, truths, max_wave=MAX_WAVE)
PIDS = cohort['pids']; W_IN = [w for w, s in enumerate(status) if s == 'INCLUDED']; NW = len(W_IN)
T = C.tags(draws, status, PIDS)
pred = {r['pid']: r for r in C.J(E / 'X3/afternoon-20261020/64/PREDICTIONS-V2-BEFORE-FRESH-OUTCOMES.json')['rows']}
A4 = np.array([pred[p]['NR_scores']['interaction-A4'] for p in PIDS]); PK = np.array([pred[p]['NR_scores']['point-K'] for p in PIDS])
TPL = np.array([cohort['template_family'][p] for p in PIDS]); UT = sorted(set(TPL))
SEED_B = 8101945; NB = 2000; Z80 = stats.norm.ppf(.975) + stats.norm.ppf(.80)


def counts(rule):
    nb = np.array([sum(T[rule][w][p] in ('NR', 'R') for w in W_IN) for p in PIDS])
    nr = np.array([sum(T[rule][w][p] == 'NR' for w in W_IN) for p in PIDS])
    return nb, nr


def fleiss(nb, nr):
    ok = nb >= 2
    if not ok.any():
        return None, 0, None
    a, n = nr[ok], nb[ok]; b = n - a
    Pi = (a * (a - 1) + b * (b - 1)) / (n * (n - 1)); pnr = a.sum() / n.sum(); Pe = pnr ** 2 + (1 - pnr) ** 2
    return (float((Pi.mean() - Pe) / (1 - Pe)) if Pe < 1 else None), int(ok.sum()), float(pnr)


def boot(fn, unit='original', seed=SEED_B):
    rng = np.random.default_rng(seed); vals = []; bad = 0
    for _ in range(NB):
        ix = rng.integers(0, len(PIDS), len(PIDS)) if unit == 'original' else np.concatenate([np.flatnonzero(TPL == g) for g in rng.choice(UT, len(UT))])
        v = fn(ix)
        if v is None or np.isnan(v):
            bad += 1
        else:
            vals.append(v)
    return dict(ci95=np.quantile(vals, [.025, .975]).tolist() if vals else None, sd=float(np.std(vals, ddof=1)) if len(vals) > 1 else None,
                valid=len(vals), invalid=bad)


def kappa_block(rule):
    nb, nr = counts(rule); k, n, p = fleiss(nb, nr)
    return dict(kappa=k, subjects=n, pooled_NR=p, NR_tags=int(nr.sum()), binary_original_waves=int(nb.sum()),
                bootstrap=boot(lambda ix: fleiss(nb[ix], nr[ix])[0]))


def wave_gain(rule, ix, w):
    t = np.array([T[rule][w][PIDS[i]] for i in ix]); b = np.isin(t, ['NR', 'R']); y = (t[b] == 'NR').astype(int)
    a, k = f.auc(y, A4[ix][b]), f.auc(y, PK[ix][b])
    return None if a is None else a - k


def mean_gain(rule, ix):
    g = [x for x in (wave_gain(rule, ix, w) for w in W_IN) if x is not None]
    return float(np.mean(g)) if g else None


def gain_block(rule):
    ALL = np.arange(len(PIDS)); per = [wave_gain(rule, ALL, w) for w in W_IN]; dfn = [g for g in per if g is not None]
    ob = boot(lambda ix: mean_gain(rule, ix)); tb = boot(lambda ix: mean_gain(rule, ix), unit='template')
    return dict(estimand='mean over defined included waves of AUC_w(interaction-A4) - AUC_w(point-K)', observed=mean_gain(rule, ALL),
                defined_waves=len(dfn), per_wave=per, wave_min=min(dfn) if dfn else None, wave_max=max(dfn) if dfn else None,
                waves_with_loss=sum(g < 0 for g in dfn), original_bootstrap=ob, template_bootstrap=tb,
                mde80=float(Z80 * ob['sd']) if ob['sd'] else None)


# ---- P2 noise ceiling (spec 7.2; methods of explore/M1b/noise_ceiling_20261021.py, waves = included waves)
def summ(x):
    x = np.asarray([v for v in x if v is not None and not np.isnan(v)], float)
    if not len(x):
        return None
    pc = np.percentile(x, [2.5, 25, 50, 75, 97.5])
    return dict(n=int(len(x)), mean=float(x.mean()), min=float(x.min()), p2_5=float(pc[0]), median=float(pc[2]), p97_5=float(pc[4]), max=float(x.max()))


def noise_ceiling(rule):
    nb, nr = counts(rule); use = nb > 0
    if nb.sum() == 0 or nr.sum() == 0 or nr.sum() == nb.sum():
        return dict(defined=False, reason='no binary rows or one class pooled')
    pooled = nr.sum() / nb.sum(); q = np.where(use, nr / np.maximum(nb, 1), np.nan)
    loo = []
    for w in W_IN:
        rows = [i for i, p in enumerate(PIDS) if T[rule][w][p] in ('NR', 'R')]
        y = np.array([T[rule][w][PIDS[i]] == 'NR' for i in rows], int)
        k = nr[rows] - y; n = nb[rows] - 1
        loo.append(f.auc(y, np.where(n > 0, k / np.maximum(n, 1), pooled)))

    def nll(t):
        a, b = np.exp(t); return -np.sum(special.betaln(nr[use] + a, nb[use] - nr[use] + b) - special.betaln(a, b))
    fit = optimize.minimize(nll, np.log([1.0, 1.0]), method='Nelder-Mead', options=dict(xatol=1e-10, fatol=1e-12, maxiter=20000))
    al, be = np.exp(fit.x); ui = np.flatnonzero(use); bh = nb / NW; rng = np.random.default_rng(20261021)
    sim = []
    for _ in range(20000):
        qt = rng.beta(al + nr[ui], be + nb[ui] - nr[ui]); bin_ = rng.random(len(ui)) < bh[ui]; y = rng.random(len(ui)) < qt
        sim.append(f.auc(y[bin_].astype(int), qt[bin_]))
    kw = {}
    for K in (1, 3, 11):
        a = []
        for _ in range(3000):
            qt = rng.beta(al + nr[ui], be + nb[ui] - nr[ui]); nbin = rng.binomial(K, bh[ui]); knr = rng.binomial(nbin, qt); ok = nbin > 0
            y = knr[ok] * 2 > nbin[ok]; tie = knr[ok] * 2 == nbin[ok]; y = np.where(tie, rng.random(ok.sum()) < .5, y)
            a.append(f.auc(y.astype(int), qt[ok]))
        kw[K] = summ(a)
    return dict(defined=True, pooled_NR=float(pooled), q_hat={p: (None if np.isnan(v) else float(v)) for p, v in zip(PIDS, q)}, q_summary=summ(q),
                oracle_leave_wave_out=summ(loo), oracle_leave_wave_out_per_wave=loo, eb_prior=dict(alpha=float(al), beta=float(be)),
                oracle_parametric_eb=summ(sim), oracle_vs_k_wave_majority=kw)


# ---- S3 cross-endpoint: per-original NR fraction, thinking (O) vs the published no-think READY63 fractions
def cross_endpoint():
    ref = C.J(E / 'W9b/ready63rel/out/RESULT.json')['S4']['per_original']; nb, nr = counts('O')
    ok = [i for i, p in enumerate(PIDS) if nb[i] >= 5 and ref[p]['binary_waves'] >= 5]
    x = np.array([nr[i] / nb[i] for i in ok]); y = np.array([ref[PIDS[i]]['NR_fraction'] for i in ok])
    rho = lambda ix: (float(stats.spearmanr(x[ix], y[ix])[0]) if len(set(x[ix])) > 1 and len(set(y[ix])) > 1 else None)
    rng = np.random.default_rng(SEED_B); bs = [rho(rng.integers(0, len(ok), len(ok))) for _ in range(NB)] if len(ok) > 2 else []
    bs = [v for v in bs if v is not None and not np.isnan(v)]
    return dict(n=len(ok), spearman=rho(np.arange(len(ok))) if len(ok) > 2 else None, ci95=np.quantile(bs, [.025, .975]).tolist() if bs else None,
                valid=len(bs), mean_NR_fraction_thinking=float(x.mean()) if len(ok) else None, mean_NR_fraction_nothink=float(y.mean()) if len(ok) else None)


# ---- S4 N0 mechanism check (rule O): fragile rate from even included waves, pooled accuracy from odd included waves
def n0(p):
    pb = stats.binom.pmf(np.arange(5), 4, p); cdf = stats.binom.cdf(np.arange(5) - 1, 4, p)
    nr_ = sum(pb[k] * (1 - (1 - cdf[k]) ** 2) for k in range(1, 5)); r_ = sum(pb[k] * (1 - cdf[k]) ** 2 for k in range(1, 5))
    return nr_ / (nr_ + r_) if nr_ + r_ > 0 else np.nan


def mechanism():
    ev = [w for w in W_IN if w % 2 == 0]; od = [w for w in W_IN if w % 2 == 1]; xs, ys = [], []
    for p in PIDS:
        t = [T['O'][w][p] for w in ev]; b = [v for v in t if v in ('NR', 'R')]
        cs = [P_cell for d in draws.values() if d['pid'] == p and d['wave'] in od for P_cell in [C.P.cell(d['parse'], 'O')] if P_cell['status'] == 'numeric']
        if len(b) >= 5 and cs:
            ys.append(b.count('NR') / len(b)); xs.append(n0(np.mean([c['correct'] for c in cs])))
    x, y = np.array(xs), np.array(ys)
    rho = lambda ix: (float(stats.spearmanr(x[ix], y[ix])[0]) if len(set(x[ix])) > 1 and len(set(y[ix])) > 1 else None)
    rng = np.random.default_rng(SEED_B); bs = [rho(rng.integers(0, len(x), len(x))) for _ in range(NB)] if len(x) > 2 else []
    bs = [v for v in bs if v is not None and not np.isnan(v)]
    return dict(n=len(x), spearman_fragile_vs_N0=rho(np.arange(len(x))) if len(x) > 2 else None,
                ci95=np.quantile(bs, [.025, .975]).tolist() if bs else None, valid=len(bs),
                mean_excess_over_N0=float(np.mean(y - x)) if len(x) else None)


# ---- operational and diagnostics (spec section 9)
inc = list(draws.values())
st_fam = collections.Counter(f"{d['family']}|{d['parse']['status']}" for d in inc)
path = collections.Counter(str(d['parse']['path']) for d in inc if d['parse']['status'] in ('numeric', 'abstain', 'nonnumeric'))
tok = {fam: np.percentile([d['tokens'] for d in inc if d['family'] == fam and d['tokens'] is not None], [25, 50, 75]).tolist()
       if any(d['family'] == fam and d['tokens'] is not None for d in inc) else None for fam in C.FAMS}
per_wave = {r: {w: dict(collections.Counter(T[r][w].values())) for w in W_IN} for r in C.RULES}
half = {}
for name, ws in (('first_half', W_IN[:NW // 2]), ('second_half', W_IN[NW // 2:])):
    nb = np.array([sum(T['O'][w][p] in ('NR', 'R') for w in ws) for p in PIDS]); nr = np.array([sum(T['O'][w][p] == 'NR' for w in ws) for p in PIDS])
    half[name] = dict(waves=ws, kappa=fleiss(nb, nr)[0], pooled_NR=fleiss(nb, nr)[2])
nc = C.J(E / 'M1b/NOISE-CEILING-RESULT-20261021.json'); r63 = C.J(E / 'W9b/ready63rel/out/RESULT.json')
comparators = dict(note='READY63 no-think repeat (Qwen3.5-4B, thinking off, cap 4096, 100 waves); descriptive only, no test of the difference',
                   kappa=r63['S4']['fleiss_kappa_NR_R'], kappa_ci95=C.J(E.parent / 'pair/aimo/report/numbers/m1h-t002.json')['values']['rel_kappa_ci'],
                   oracle_leave_wave_out_mean=nc['oracle_single_wave']['leave_wave_out']['mean'], repeat_gain=r63['primary'])

res = dict(scope='EXPLORATORY reliability repeat on the READY63 cohort on this thinking-on endpoint (Qwen3.5-4B thinking ON, T 1, cap 32768, '
                 'truncation = wrong, boxed-aware parser, rule O); NOT organiser parity',
           dry_run=DRY, scorer_sha256=C.H(__file__), freeze_sha256=C.H(FREEZE), attempt=ATTEMPT, gate_decision=GATE['decision'],
           gate_stop_reading=GATE.get('reading'), engine_cut_at_wave=ENG['cut_at_wave'],
           operational=dict(wave_status=status, included_waves=W_IN, layout=layout, draws_in_included_waves=len(inc), binding_failures=len(fails),
                            binding_failure_list=fails[:50], status_by_family=dict(sorted(st_fam.items())), answer_path=dict(path),
                            answer_line_vs_boxed_disagree=sum(d['disagree'] for d in inc),
                            truncated_by_family={fam: sum(d['family'] == fam and d['parse']['status'] == 'truncated' for d in inc) for fam in C.FAMS},
                            output_token_quartiles=tok, per_wave_tags=per_wave),
           P1_kappa_O=kappa_block('O'), P2_noise_ceiling_O=noise_ceiling('O'), P3_repeat_gain_O=gain_block('O'),
           S1_strict=dict(kappa=kappa_block('S'), gain=gain_block('S')), S2_legacy_parser_kappa=kappa_block('L'),
           S3_cross_endpoint=cross_endpoint(), S4_mechanism=mechanism(), diagnostics=dict(kappa_by_half_O=half), comparators=comparators)
(OUT / 'RESULT.json').write_text(json.dumps(res, indent=1, default=float), encoding='utf-8')
with open(OUT / 'DRAWS.jsonl', 'w', encoding='utf-8') as fh:
    for d in inc:
        fh.write(json.dumps(dict(key=d['key'], pid=d['pid'], family=d['family'], wave=d['wave'], rep=d['rep'], finish=d['finish'], tokens=d['tokens'],
                                 status=d['parse']['status'], answer=d['parse']['answer'], correct=d['parse']['correct'], path=d['parse']['path'],
                                 legacy_status=d['legacy']['status'])) + '\n')
print(json.dumps(dict(included_waves=NW, P1=res['P1_kappa_O'], P3=dict((k, res['P3_repeat_gain_O'][k]) for k in ('observed', 'defined_waves', 'original_bootstrap', 'mde80')),
                      oracle=(res['P2_noise_ceiling_O'].get('oracle_leave_wave_out') or {}).get('mean')), indent=1, default=float))
