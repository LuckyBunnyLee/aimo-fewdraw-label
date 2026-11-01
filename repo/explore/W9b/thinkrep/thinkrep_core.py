"""Shared loading, binding and tagging for the thinking-on reliability repeat (W9b, 24 Oct 2026).
Used by gate_thinkrep.py, engine_check.py and score_thinkrep.py. Read-only on the run folder; never opens prefixes/.
r2 (24 Oct, before any output; V14 verdict): FREEZE-r2 check shared by every script, two pre-frozen attempts
(attempt 2 = fresh replicates, used only after ABORT_ENGINE), run-manifest checks, an outcome-blind engine check
(statuses read without truths) and a stat-only record fingerprint."""
import collections, hashlib, json, sys
from pathlib import Path

E = Path('E:/work/research-cycle/explore'); TR = E / 'W9b/thinkrep'
sys.path.insert(0, str(E / 'X3')); sys.path.insert(0, str(TR))
import fresh81_pure as f  # noqa: E402
import parse_think as P  # noqa: E402

FAMS = ['base', 'surface_gs', 'surface_dlm']; WAVES = 20; PER_WAVE = 408; RULES = ['O', 'S', 'L']; CAP = 32768
FREEZE = TR / 'THINKREP-FREEZE-r2.sha256'
ATTEMPTS = {1: dict(req='REQUESTS.json', truth='TRUTHS.json', rep0=2000), 2: dict(req='REQUESTS-a2.json', truth='TRUTHS-a2.json', rep0=3000)}
H = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
J = lambda p: json.loads(Path(p).read_bytes())


def check_freeze(caller):
    """Every hash in FREEZE-r2 must match and the calling script must be listed. Run before any record is opened."""
    lines = [l.split() for l in FREEZE.read_text(encoding='utf-8').splitlines() if l.strip() and not l.startswith('#')]
    for h, p in lines:
        assert H(E.parent / p) == h, f'ABORT hash mismatch {p}'
    assert H(caller) in {h for h, _ in lines}, f'ABORT {Path(caller).name} not in FREEZE'
    return H(FREEZE)


def state_dir(argv):
    """Real runs keep gate/engine/out state under thinkrep/; a dry run names its own folder after --dry-run."""
    if '--dry-run' in argv:
        d = Path(argv[argv.index('--dry-run') + 1]); assert d.resolve() != TR.resolve(); return d, True
    return TR, False


def run_manifest(run):
    """The run folder's MANIFEST.json names the attempt, our request/truth files, the bound chat template and a passed
    smoke check (a non-cohort prompt whose raw output contains </think> and finished with stop). Returns (attempt, sha)."""
    man = J(Path(run) / 'MANIFEST.json'); a = man.get('thinkrep_attempt'); assert a in ATTEMPTS, 'ABORT manifest thinkrep_attempt'
    assert man['request_sha256'] == H(TR / ATTEMPTS[a]['req']) and man['truth_sha256'] == H(TR / ATTEMPTS[a]['truth']), 'ABORT run manifest'
    t = man.get('chat_template_sha256', ''); assert len(t) == 64 and all(c in '0123456789abcdef' for c in t), 'ABORT chat template not bound'
    s = man.get('smoke') or {}; assert s.get('think_closed') is True and s.get('finish_reason') == 'stop', 'ABORT smoke check missing or failed'
    return a, H(Path(run) / 'MANIFEST.json')


def frozen(attempt=1):
    A = ATTEMPTS[attempt]; reqs = J(TR / A['req']); truths = J(TR / A['truth']); cohort = J(TR / 'COHORT.json')
    assert len(reqs) == WAVES * PER_WAVE and [q['order_index'] for q in reqs] == list(range(len(reqs)))
    assert set(truths) == {q['identity_sha256'] for q in reqs}
    return reqs, truths, cohort


def wave_of(q):
    return (q['identity']['replicate'] - ATTEMPTS[1 if q['identity']['replicate'] < 3000 else 2]['rep0']) // 4


def record_files(run):
    byname = {}
    for blk in sorted(Path(run).glob('block-*')):
        rd = blk / 'records'
        if not rd.is_dir():
            continue
        for p in rd.iterdir():
            if p.suffix == '.json' and len(p.name) == 69:
                assert p.stem not in byname, f'ABORT duplicate record across blocks {p.stem}'
                byname[p.stem] = p
    return byname


def fingerprint(run):
    """sha256 over sorted 'relative path|size' of every record file: from stat only, no record is read."""
    run = Path(run); rows = sorted(f'{p.relative_to(run).as_posix()}|{p.stat().st_size}' for p in record_files(run).values())
    return hashlib.sha256('\n'.join(rows).encode()).hexdigest(), len(rows)


def present_per_wave(run, reqs):
    byname = record_files(run)
    return [sum(q['identity_sha256'] in byname for q in reqs[w * PER_WAVE:(w + 1) * PER_WAVE]) for w in range(WAVES)]


def load(run, reqs, truths, max_wave=WAVES):
    """Bind records under run/block-*/records/. Returns (draws by key, wave_status list, binding failures, layout).
    truths=None reads statuses only (no correctness, no legacy parse): used by the engine check before any grading."""
    run = Path(run); byname = record_files(run)
    keys = {q['identity_sha256'] for q in reqs}
    assert not set(byname) - keys, 'ABORT record names outside REQUESTS'
    present = [sum(q['identity_sha256'] in byname for q in reqs[w * PER_WAVE:(w + 1) * PER_WAVE]) for w in range(WAVES)]
    last = max([w for w in range(WAVES) if present[w]], default=-1)
    status = []
    for w in range(WAVES):
        if w >= max_wave:
            status.append('NOT_USED')
        elif present[w] == PER_WAVE or (present[w] and w < last):
            status.append('INCLUDED')
        elif present[w]:
            status.append('PARTIAL')
        else:
            status.append('NOT_REACHED')
    draws = {}; fails = []
    for q in reqs:
        w = wave_of(q); assert q['order_index'] // PER_WAVE == w
        if status[w] != 'INCLUDED':
            continue
        key = q['identity_sha256']; i = q['identity']
        d = dict(key=key, pid=i['problem_id'], family=i['family'], rep=i['replicate'] - ATTEMPTS[1 if i['replicate'] < 3000 else 2]['rep0'],
                 wave=w, finish=None, tokens=None)
        if key not in byname:
            pt = pl = dict(status='missing', answer=None, correct=None, path=None); d['disagree'] = False
        else:
            try:
                r = f.envelope(json.loads(byname[key].read_bytes()))
                assert r['identity_sha256'] == key and r['identity'] == i, 'identity'
                assert str(r['seed']) == str(q['seed']) and r['request_sha256'] == f.sha(f.canon(q)), 'seed/request'
                pt = P.parse(r['raw'], r['finish_reason'], r['error'], None if truths is None else truths[key])
                pl = (dict(status=None, answer=None, correct=None, path=None) if truths is None
                      else dict(f.parse(r['raw'], r['finish_reason'], r['error'], truths[key]), path=None))
                d.update(finish=r['finish_reason'], tokens=r['output_tokens'], disagree=P.boxed_disagrees(r['raw'], pt))
            except Exception as exc:  # noqa: BLE001 - every failure is listed and stays in the denominator
                fails.append(dict(key=key, wave=w, error=repr(exc)[:200]))
                pt = pl = dict(status='binding_fail', answer=None, correct=None, path=None); d['disagree'] = False
        d['parse'] = pt; d['legacy'] = pl; draws[key] = d
    return draws, status, fails, dict(blocks=sorted(b.name for b in run.glob('block-*')), records=len(byname), present_per_wave=present)


# ---- r2 engine-validity check (spec r2 section 6). Statuses only; thresholds frozen before any output.
# On the 10,388 reliability20 thinking draws, read by this parser, the rates were: unclosed 0, no usable answer 0.38%,
# truncated at 32,768 0.03% (explore/W9b/thinkrep/R2-PARSER-REPLAY.md).
LIMITS = dict(unclosed_of_stop=0.02, no_usable_answer=0.05, truncated=0.20)
NO_USABLE = ('noanswer', 'nonnumeric', 'invalid', 'error')


BIND_RATE_AFTER_GATE = 0.01  # after the gate a binding failure stays in the denominator (r1 rule) unless the rate exceeds this


def engine_stats(ds, fails_n, mult=1.0, gate=True):
    st = collections.Counter(d['parse']['status'] for d in ds); n = len(ds)
    stop = sum(d['finish'] in ('stop', 'eos') for d in ds)
    short = sum(d['parse']['status'] == 'truncated' and (d['tokens'] or 0) < CAP for d in ds)
    rates = dict(unclosed_of_stop=st['unclosed'] / stop if stop else (1.0 if n else 0.0),
                 no_usable_answer=sum(st[s] for s in NO_USABLE) / n if n else 0.0, truncated=st['truncated'] / n if n else 0.0)
    fired = [k for k, v in rates.items() if v > LIMITS[k] * mult]
    if (fails_n if gate else (n and fails_n / n > BIND_RATE_AFTER_GATE * mult)):
        fired.append('binding_failure')
    if short:
        fired.append('truncated_below_cap')
    return dict(draws=n, stop_finished=stop, status=dict(st), rates=rates, limits={k: v * mult for k, v in LIMITS.items()},
                binding_failures=fails_n, truncated_below_cap=short, fired=fired, ok=not fired)


def engine_check(draws, fails, waves, per_wave_mult=None):
    """Gate (no per_wave_mult): pooled check over `waves`, any binding failure fires. After the gate (per_wave_mult set):
    pooled check plus each wave alone at the multiplied rate limits; binding failures fire only above 1% (2% per wave).
    Returns (ok, report, first failing wave or None)."""
    ws = set(waves); ds = [d for d in draws.values() if d['wave'] in ws]; gate = not per_wave_mult
    pooled = engine_stats(ds, sum(x['wave'] in ws for x in fails), gate=gate); rep = dict(waves=sorted(ws), pooled=pooled); first = None
    if per_wave_mult:
        rep['per_wave'] = {}
        for w in sorted(ws):
            s = engine_stats([d for d in ds if d['wave'] == w], sum(x['wave'] == w for x in fails), per_wave_mult, gate=False)
            rep['per_wave'][w] = s
            if not s['ok'] and first is None:
                first = w
    return pooled['ok'] and first is None, rep, first


def cp_upper(k, n, conf=0.95):
    """Two-sided 95% Clopper-Pearson upper bound for a binomial proportion."""
    from scipy import stats
    return 1.0 if k >= n else float(stats.beta.ppf(1 - (1 - conf) / 2, k + 1, n - k))


def tags(draws, status, pids):
    """tags[rule][w][pid] for every INCLUDED wave; rule O / S use parse_think, L uses the frozen fresh81 parser (strict)."""
    cells = collections.defaultdict(list)
    for d in draws.values():
        cells[(d['wave'], d['pid'], d['family'])].append(d)
    out = {r: {} for r in RULES}
    for w, s in enumerate(status):
        if s != 'INCLUDED':
            continue
        for r in RULES:
            out[r][w] = {}
            for pid in pids:
                c = {}
                for fam in FAMS:
                    ds = sorted(cells[(w, pid, fam)], key=lambda d: d['rep']); assert [d['rep'] for d in ds] == list(range(4 * w, 4 * w + 4))
                    if r == 'L':
                        c[fam] = [dict(status=d['legacy']['status'], correct=d['legacy']['correct']) for d in ds]
                    else:
                        c[fam] = [P.cell(d['parse'], r) for d in ds]
                out[r][w][pid] = f.tag(c, 4)
    return out
