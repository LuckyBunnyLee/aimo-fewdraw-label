"""SHAM Phase 1 scorer (W9b), v1.1. Implements SHAM-PHASE1-AMENDMENT-20261025.md section 3 with the v1.1 addendum
(V23 fix 4: every undefined secondary gets a named reading and null, never NaN); frozen before any record exists.
usage:
  python -I score_phase1.py selftest            planted-effect and edge-case checks on synthetic draws (CPU)
  python -I score_phase1.py dryrun              end-to-end on a 10-original subset run by wave_core with a fake engine (CPU, temp folder kept)
  python -I score_phase1.py run <RUN-FOLDER>    score once: refuses if out/SCORE-ONCE-STARTED.json exists or the freeze does not verify
"""
import collections, hashlib, json, math, pathlib, random, sys, tempfile, time
import numpy as np
HERE = pathlib.Path(__file__).resolve().parent; DATA = HERE.parent; EX = HERE.parents[2]  # data files are the v1.0 build, unchanged
sys.path.insert(0, str(EX / 'X3')); import fresh81_pure as f
sys.path.insert(0, str(EX / 'W9b/decomp')); from decomp import N0
sys.path.insert(0, str(HERE)); import wave_core as wc
B, SEED, MIN_JOINT, MIN_OWN, MIN_WAVES = 2000, 20261025, 3, 3, 8
FAM = ['base', 'surface_gs', 'surface_dlm', 'sham_a', 'sham_b']
HF = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def boot(x, rng, stat=np.mean):
    x = np.asarray(x, float); n = len(x)
    if n == 0: return dict(est=None, ci95=None, n=0)
    bt = [float(stat(x[rng.integers(0, n, n)])) for _ in range(B)]
    return dict(est=float(stat(x)), ci95=np.quantile(bt, [.025, .975]).tolist(), n=n)


def bind(R, requests, truths):
    """Draws from the first 12 complete waves (index order). Every record is verified against its frozen request."""
    m = json.loads((DATA / 'MANIFEST.json').read_bytes())
    st = wc.scan(R, m); assert not st['unsealed'], 'unsealed blocks'
    waves = st['complete'][:12]; where = {}
    for b in sorted(pathlib.Path(R).glob('block-*')):
        for c in b.glob('WAVE-COMPLETE-*.json'): where[int(c.stem.rsplit('-', 1)[1])] = (b, wc.read(c)['records'])
    byw = wc.by_wave(requests); draws = []
    for w in waves:
        b, recs = where[w]; assert set(recs) == {q['identity_sha256'] for q in byw[w]}, f'wave {w} record set'
        for q in byw[w]:
            k = q['identity_sha256']; r = f.envelope(wc.read(b / 'records' / (k + '.json')))
            assert r['identity_sha256'] == k and r['identity'] == q['identity'] and r['seed'] == q['seed'] and r['request_sha256'] == wc.sha(wc.canon(q)), k
            assert wc.sha(wc.canon(r)) == recs[k] and r['wave'] == w
            v = f.parse(r['raw'], r['finish_reason'], r['error'], truths[k])
            draws.append(dict(key=k, pid=q['identity']['problem_id'], family=q['identity']['family'], wave=w, replicate=q['identity']['replicate'],
                              status=v['status'], correct=v['correct'] or 0, tokens=r['output_tokens']))
    return dict(complete=st['complete'], abandoned=st['abandoned'], scored_waves=waves), draws


def analyse(draws, fresh_tag, rng):
    cells = collections.defaultdict(list); pids = sorted({d['pid'] for d in draws}); waves = sorted({d['wave'] for d in draws})
    for d in draws: cells[(d['pid'], d['wave'], d['family'])].append(d)
    rows = []
    for p in pids:
        allf = {fm: [d for w in waves for d in cells[(p, w, fm)]] for fm in FAM}
        assert all(len(v) == 4 * len(waves) for v in allf.values()), p
        ps = {fm: float(np.mean([d['correct'] for d in v])) for fm, v in allf.items()}   # all-answer solve rate
        num_b = [d for d in allf['base'] if d['status'] == 'numeric']
        real, sham = [], []
        for w in waves:
            c = {fm: [dict(status=d['status'], correct=d['correct']) for d in sorted(cells[(p, w, fm)], key=lambda d: d['replicate'])] for fm in FAM}
            real.append(f.tag(dict(base=c['base'], surface_gs=c['surface_gs'], surface_dlm=c['surface_dlm']), 4))
            sham.append(f.tag(dict(base=c['base'], surface_gs=c['sham_a'], surface_dlm=c['sham_b']), 4))
        joint = [(a, b) for a, b in zip(real, sham) if a in ('NR', 'R') and b in ('NR', 'R')]
        rb = [a for a in real if a in ('NR', 'R')]; sb = [b for b in sham if b in ('NR', 'R')]
        pb_num = float(np.mean([d['correct'] for d in num_b])) if num_b else None
        rows.append(dict(pid=p, fresh6h=fresh_tag[p], **{'p_' + fm: ps[fm] for fm in FAM},
                         delta_vs_sham=(ps['sham_a'] + ps['sham_b']) / 2 - (ps['surface_gs'] + ps['surface_dlm']) / 2,
                         delta_vs_base=ps['base'] - (ps['surface_gs'] + ps['surface_dlm']) / 2, cal_base_minus_sham=ps['base'] - (ps['sham_a'] + ps['sham_b']) / 2,
                         n_joint=len(joint), nr_real_joint=sum(a == 'NR' for a, _ in joint) / len(joint) if joint else None,
                         nr_sham_joint=sum(b == 'NR' for _, b in joint) / len(joint) if joint else None,
                         n_real_bin=len(rb), n_sham_bin=len(sb), nr_real_own=rb.count('NR') / len(rb) if rb else None, nr_sham_own=sb.count('NR') / len(sb) if sb else None,
                         p_b_numeric=pb_num, N0=N0(pb_num) if pb_num else None, real_counts=dict(collections.Counter(real)), sham_counts=dict(collections.Counter(sham))))
    n = 4 * len(waves); res = dict(originals=len(rows), waves=len(waves), draws_per_version=n)
    # primary: all-answer solve change against the identical-text copies drawn in the same waves
    res['PRIMARY_solve_vs_sham'] = boot([r['delta_vs_sham'] for r in rows], rng)
    # calibration: base against its byte-identical copies; and the sham contrasts as an empirical null of a per-original z
    res['CAL1_base_minus_sham'] = boot([r['cal_base_minus_sham'] for r in rows], rng)
    zs = []
    for r in rows:
        for a, b in (('base', 'sham_a'), ('base', 'sham_b'), ('sham_a', 'sham_b')):
            pa, pb = r['p_' + a], r['p_' + b]; se = (pa * (1 - pa) / n + pb * (1 - pb) / n) ** .5
            if se > 0: zs.append((pa - pb) / se)
    share = float(np.mean(np.abs(zs) > 1.96)) if zs else None
    res['CAL2_sham_z'] = dict(tests=len(zs), share_abs_z_gt_1_96=share, rule='independent draws give about 0.05; above 0.10 fails',
                              reading='not estimable: every sham contrast has zero variance' if not zs else 'pass' if share <= 0.10 else 'fail')
    c1 = res['CAL1_base_minus_sham']['ci95']; lo, hi = res['PRIMARY_solve_vs_sham']['ci95']
    res['PRIMARY_reading'] = ('calibration not estimable: not read as an edit effect' if not zs else
                              'calibration failed: not read as an edit effect' if not (c1[0] <= 0 <= c1[1] and share <= 0.10) else
                              'edit loss in solve probability' if lo > 0 else 'edit gain in solve probability' if hi < 0 else 'not resolved')
    # secondary: the report's metric (against the original) and the spread of true effects (method of moments, as DECOMP D1)
    d = np.array([r['delta_vs_base'] for r in rows])
    se2 = np.array([r['p_base'] * (1 - r['p_base']) / n + (r['p_surface_gs'] * (1 - r['p_surface_gs']) / n + r['p_surface_dlm'] * (1 - r['p_surface_dlm']) / n) / 4 for r in rows])
    res['S_solve_vs_base'] = boot(d, rng); res['S_tau'] = float(max(0.0, d.var(ddof=1) - se2.mean()) ** .5) if len(d) > 1 else None
    # tag secondaries
    J = [r for r in rows if r['n_joint'] >= MIN_JOINT]; O = [r for r in rows if r['n_real_bin'] >= MIN_OWN and r['n_sham_bin'] >= MIN_OWN]
    O1 = [r for r in rows if r['n_real_bin'] >= 1 and r['n_sham_bin'] >= 1]
    def tagset(rs, kr, ks):
        if not rs: return dict(n=0, reading='not estimable: no eligible originals')
        R_, S_ = np.array([r[kr] for r in rs]), np.array([r[ks] for r in rs]); out = dict(n=len(rs), real=boot(R_, rng), sham=boot(S_, rng), delta=boot(R_ - S_, rng))
        if R_.mean() == 0:
            out['ratio_sham_over_real'] = dict(est=None, ci95=None, undefined_resamples=None, reading='undefined: no real-rewrite NR in this set (zero denominator)')
            return out
        bt, und = [], 0; m_ = len(rs)
        for _ in range(B):
            ix = rng.integers(0, m_, m_)
            if R_[ix].mean() > 0: bt.append(S_[ix].mean() / R_[ix].mean())
            else: und += 1
        out['ratio_sham_over_real'] = dict(est=float(S_.mean() / R_.mean()), ci95=np.quantile(bt, [.025, .975]).tolist(), undefined_resamples=und,
                                           reading='descriptive' if und == 0 else f'descriptive; {und} of {B} resamples had a zero denominator and are left out')
        return out
    res['T1_joint'] = tagset(J, 'nr_real_joint', 'nr_sham_joint'); res['T1_joint']['rule'] = f'originals with >= {MIN_JOINT} waves binary for both tags'
    res['T2_own'] = tagset(O, 'nr_real_own', 'nr_sham_own'); res['T2_own']['rule'] = f'>= {MIN_OWN} binary waves for each tag'
    res['T3_own_spec_rule'] = tagset(O1, 'nr_real_own', 'nr_sham_own'); res['T3_own_spec_rule']['rule'] = '>= 1 binary wave for each tag (SHAM-SPEC P1 as frozen)'
    Z = [r for r in O if r['N0'] is not None]
    res['T4_sham_minus_N0'] = boot([r['nr_sham_own'] - r['N0'] for r in Z], rng)
    t4 = res['T4_sham_minus_N0']['ci95']
    res['T4_calibrated_within_0_03'] = None if t4 is None else bool(-0.03 < t4[0] and t4[1] < 0.03)
    res['T4_reading'] = ('not estimable: no T2-eligible original with a numeric base rate (not evidence against calibration)' if t4 is None else
                         'sham NR rate within 0.03 of N0' if res['T4_calibrated_within_0_03'] else 'not shown within 0.03 of N0')
    # selection displays (descriptive)
    res['E_eligible_T1'] = dict(n=len(J), share=len(J) / len(rows), reading='descriptive; conditional on an outcome-dependent eligibility rule')
    res['E_solve_by_T1'] = dict(eligible=boot([r['delta_vs_sham'] for r in J], rng), ineligible=boot([r['delta_vs_sham'] for r in rows if r not in J], rng))
    res['S1_solve_by_fresh6h'] = {k: boot([r['delta_vs_sham'] for r in rows if (r['fresh6h'] == 'UNUSABLE') == (k == 'UNUSABLE')], rng) for k in ('UNUSABLE', 'binary_or_floor')}
    res['status_counts'] = {fm: dict(collections.Counter(d['status'] for d in draws if d['family'] == fm)) for fm in FAM}
    return res, rows


def synth(rng, n_orig=320, waves=12, edit=0.0, sham_shift=0.0, unusable=0.0, lo=0.3, hi=0.99, nonnum=0.3):
    draws = []; tags = {}; nn = nonnum
    for i in range(n_orig):
        p = rng.uniform(lo, hi); bad = rng.random() < unusable; tags[f's{i}'] = 'UNUSABLE' if bad else 'R'
        for w in range(waves):
            for fm in FAM:
                pf = p - edit if fm.startswith('surface') else p - sham_shift if fm.startswith('sham') else p
                for r in range(4):
                    nonnum = bad and rng.random() < nn
                    draws.append(dict(pid=f's{i}', family=fm, wave=w, replicate=4 * w + r, status='invalid' if nonnum else 'numeric',
                                      correct=0 if nonnum else int(rng.random() < max(0, pf))))
    return draws, tags


def selftest():
    global B; B = 300
    rng = np.random.default_rng(1)
    r0, _ = analyse(*synth(rng), np.random.default_rng(2))
    assert r0['PRIMARY_reading'] == 'not resolved' and r0['CAL2_sham_z']['share_abs_z_gt_1_96'] < 0.08, r0['PRIMARY_solve_vs_sham']
    r1, _ = analyse(*synth(rng, edit=0.06, unusable=0.4), np.random.default_rng(2))
    assert r1['PRIMARY_reading'] == 'edit loss in solve probability' and r1['T1_joint']['delta']['est'] > 0, r1['PRIMARY_solve_vs_sham']
    r2, _ = analyse(*synth(rng, sham_shift=0.08), np.random.default_rng(2))
    assert r2['PRIMARY_reading'].startswith('calibration failed'), r2['CAL1_base_minus_sham']
    # v1.1 edge cases: all perfect (zero variance everywhere, no NR), no tag-eligible originals, zero real NR with some sham NR
    r3, _ = analyse(*synth(rng, n_orig=40, lo=1.0, hi=1.0), np.random.default_rng(2))
    assert r3['PRIMARY_reading'].startswith('calibration not estimable') and r3['CAL2_sham_z']['tests'] == 0
    assert r3['T1_joint']['ratio_sham_over_real']['est'] is None and r3['T1_joint']['ratio_sham_over_real']['reading'].startswith('undefined')
    r4, _ = analyse(*synth(rng, n_orig=40, unusable=1.0, nonnum=1.0), np.random.default_rng(2))
    assert r4['T1_joint'] == dict(n=0, reading='not estimable: no eligible originals', rule=r4['T1_joint']['rule']) and r4['T2_own']['n'] == 0
    assert r4['T4_calibrated_within_0_03'] is None and r4['T4_reading'].startswith('not estimable')
    r5, rows5 = analyse(*synth(rng, n_orig=40, lo=1.0, hi=1.0, sham_shift=0.3), np.random.default_rng(2))
    assert r5['T1_joint']['ratio_sham_over_real']['reading'].startswith('undefined') and r5['T1_joint']['sham']['est'] > 0
    for r in (r0, r1, r2, r3, r4, r5): json.dumps(r, allow_nan=False)  # no NaN anywhere
    print('selftest ok', dict(null=r0['PRIMARY_solve_vs_sham']['ci95'], planted_006=r1['PRIMARY_solve_vs_sham']['est'], shifted_sham=r2['PRIMARY_reading'],
                              T4_null=r0['T4_sham_minus_N0']['est'], all_perfect=r3['PRIMARY_reading'], no_eligible=r4['T1_joint']['reading'],
                              zero_real_nr=r5['T1_joint']['ratio_sham_over_real']['reading']))


class FakeAnswers:
    """Fake engine for the dry run: answers ANSWER: <truth> with probability p_pid (lower for rewrites), else a wrong number or NaN."""
    def __init__(self, truths, reqs, clock):
        self.t, self.q, self.a, self.rng, self.clock = truths, {q['identity_sha256']: q for q in reqs}, [], random.Random(5), clock
    def add(self, key, q): self.a.append(key)
    def step(self):
        self.clock.t += 3.0; out = []
        for _ in range(min(len(self.a), self.rng.randint(1, 8))):
            k = self.a.pop(self.rng.randrange(len(self.a))); q = self.q[k]; fam = q['identity']['family']
            p = 0.8 - (0.1 if fam.startswith('surface') else 0.0); u = self.rng.random()
            txt = f'ok\nANSWER: {self.t[k]}' if u < p else 'ok\nANSWER: NaN' if u > 0.97 else 'ok\nANSWER: 123456789'
            out.append(dict(key=k, token_ids=[7] * 500, text=txt, finish_reason='stop'))
        return out, 500 * len(out)
    def close(self): pass


def dryrun():
    global B; B = 200
    reqs = json.loads((DATA / 'REQUESTS.json').read_bytes()); truths = json.loads((DATA / 'TRUTHS.json').read_bytes())
    cohort = json.loads((DATA / 'COHORT.json').read_bytes())['selected'][:10]; keep = {r['problem_id'] for r in cohort}
    sub = [q for q in reqs if q['identity']['problem_id'] in keep]
    m = json.loads((DATA / 'MANIFEST.json').read_bytes()); m = dict(m, requests=len(sub), requests_per_wave=10 * 20)
    R = pathlib.Path(tempfile.mkdtemp(prefix='sham1-v11-dry-')); clock = type('C', (), {'t': 1e6, '__call__': lambda s: s.t})()  # kept, not deleted
    (R / 'MANIFEST.json').write_bytes(wc.canon(m))
    hook_engine = FakeAnswers(truths, sub, clock)
    step0 = hook_engine.step
    def step_with_stop():  # STOP_NOW in wave 2: it must be abandoned and replaced by wave 12
        if clock.t > 1e6 + 3.0 * 160 and not (R / 'STOP_SEEN').exists(): (R / 'STOP_NOW').write_text('x'); (R / 'STOP_SEEN').write_text('1')
        return step0()
    hook_engine.step = step_with_stop
    r1 = wc.run_block(R, hook_engine, sub, m, dict(absolute_deadline=1e12), clock=clock); (R / 'STOP_NOW').rename(R / 'STOP_NOW.cleared-0')
    r2 = wc.run_block(R, FakeAnswers(truths, sub, clock), sub, m, dict(absolute_deadline=1e12), clock=clock)
    meta, draws = bind(R, sub, truths)
    res, rows = analyse(draws, {r['problem_id']: r['fresh6h_primary_tag'] for r in cohort}, np.random.default_rng(SEED))
    assert r1 == 'operator_stop_now' and r2 == 'complete' and len(meta['abandoned']) == 1 and len(meta['scored_waves']) == 12 and meta['abandoned'][0] not in meta['scored_waves']
    assert res['draws_per_version'] == 48 and res['originals'] == 10
    dumps(dict(res, per_original=rows))
    print('dryrun ok', dict(reasons=[r1, r2], abandoned=meta['abandoned'], scored=meta['scored_waves'], primary=res['PRIMARY_solve_vs_sham']['est'],
                            reading=res['PRIMARY_reading'], cal2=res['CAL2_sham_z']['share_abs_z_gt_1_96'], kept=str(R)))


def dumps(x):
    """Serialise before any output file is opened: NaN or infinity anywhere is an error, never a silent value."""
    return json.dumps(x, indent=1, allow_nan=False)


def run(R):
    for line in (HERE / 'SHAM1-FREEZE-v1.1.sha256').read_text().splitlines():
        h, p = line.split(None, 1); assert HF(HERE / p.strip()) == h, ('freeze', p)
    out = HERE / 'out'; out.mkdir(exist_ok=True)
    with open(out / 'SCORE-ONCE-STARTED.json', 'x') as g: g.write(json.dumps(dict(started=time.strftime('%Y-%m-%d %H:%M:%S %z'), run=str(R), scorer=HF(__file__))))
    reqs = json.loads((DATA / 'REQUESTS.json').read_bytes()); truths = json.loads((DATA / 'TRUTHS.json').read_bytes())
    cohort = {r['problem_id']: r['fresh6h_primary_tag'] for r in json.loads((DATA / 'COHORT.json').read_bytes())['selected']}
    meta, draws = bind(R, reqs, truths)
    if len(meta['scored_waves']) < MIN_WAVES:
        res = dict(reading=f'not measured: {len(meta["scored_waves"])} complete waves, fewer than {MIN_WAVES}'); rows = []
    else:
        res, rows = analyse(draws, cohort, np.random.default_rng(SEED))
    res.update(meta=meta, scorer_sha256=HF(__file__), freeze_sha256=HF(HERE / 'SHAM1-FREEZE-v1.1.sha256'))
    text = dumps(dict(res, per_original=rows))
    with open(out / 'RESULT.json', 'x') as g: g.write(text)
    with open(out / 'DRAWS.jsonl', 'x', encoding='utf-8', newline='\n') as g:
        for d in draws: g.write(json.dumps(d) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k.startswith(('PRIMARY', 'CAL', 'reading'))}, indent=1))


if __name__ == '__main__':
    {'selftest': selftest, 'dryrun': dryrun}.get(sys.argv[1], lambda: run(pathlib.Path(sys.argv[2])))()
