"""CPU test of wave_core.py v1.1 pause/resume and cap rules with a fake engine and a simulated clock (no GPU, no vLLM).
usage: python -I explore/W9b/sham1/v1.1/test_wave_core.py
Works in fresh temp folders and deletes nothing: the folders are kept (paths printed), and operator files are cleared
by renaming them. The kill case runs a child process that dies with os._exit mid-wave, so no EXIT.json is written."""
import json, os, random, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); import wave_core as wc
KEPT = []


class Clock:
    def __init__(self, t=1_000_000.0): self.t = t
    def __call__(self): return self.t


class Fake:
    """Finishes 1-6 active requests per step, tokens from tok(wave) each (default 900-1100); can create PAUSE/STOP_NOW,
    raise, or die at a set step. Each step moves the clock by dt(wave) seconds."""
    def __init__(self, R, clock, seed=0, hook=None, tok=None, dt=None):
        self.R, self.clock, self.rng, self.active, self.steps, self.hook = R, clock, random.Random(seed), [], 0, hook
        self.tok, self.dt, self.wave, self.generated = tok, dt, {}, 0
    def add(self, key, q): self.active.append(key); self.wave[key] = q['wave']
    def step(self):
        self.steps += 1; w = self.wave[self.active[0]] if self.active else 0
        self.clock.t += self.dt(w) if self.dt else 5.0
        if self.hook: self.hook(self)
        out = []
        for _ in range(min(len(self.active), self.rng.randint(1, 6))):
            k = self.active.pop(self.rng.randrange(len(self.active))); n = self.tok(self.wave[k], self.rng) if self.tok else self.rng.randint(900, 1100)
            out.append(dict(key=k, token_ids=[1] * n, text='work\nANSWER: 1', finish_reason='stop'))
        n = sum(len(y['token_ids']) for y in out); self.generated += n
        return out, n
    def close(self): pass


def setup(R=None, waves_built=15, planned=12, per=3, cap=10**12, hours=10**6, per_wave=None):
    R = Path(R) if R else Path(tempfile.mkdtemp(prefix='sham1-v11-test-')); KEPT.append(R)
    reqs = [dict(wave=w, identity_sha256=wc.sha(f'{w}|{p}|{f}|{r}'.encode()), seed=1, identity=dict(w=w, p=p, f=f, r=r))
            for w in range(waves_built) for p in range(per) for f in range(5) for r in range(4)]
    man = dict(waves_built=waves_built, waves_planned=planned, requests_per_wave=per_wave or per * 20, global_token_cap=cap, gpu_hour_cap=hours,
               max_active=8, max_new_tokens=1100)
    if (R / 'MANIFEST.json').exists(): man = wc.read(R / 'MANIFEST.json')  # a child process re-reads the parent's caps
    else: (R / 'MANIFEST.json').write_bytes(wc.canon(man))
    return R, reqs, man, dict(absolute_deadline=10**12)


def clear(R, name):
    n = len(list(R.glob(name + '.cleared-*'))); (R / name).rename(R / f'{name}.cleared-{n}')


def records(R):
    keys = [p.stem for p in R.glob('block-*/records/*.json')]
    assert len(keys) == len(set(keys)), 'an identity was issued twice'
    return keys


def exits(R):
    out = []
    for b in sorted(R.glob('block-*')):
        p = b / 'EXIT.json' if (b / 'EXIT.json').exists() else b / 'EXIT-SEALED-BY-OPERATOR.json'; out.append(wc.read(p))
    return out


def clean():
    R, reqs, man, adm = setup(); c = Clock()
    assert wc.run_block(R, Fake(R, c), reqs, man, adm, clock=c) == 'complete'
    st = wc.scan(R, man); assert st['complete'] == list(range(12)) and st['abandoned'] == []; records(R)
    e = exits(R)[0]; assert e['charged_tokens'] == e['new_tokens'] <= e['token_bound']


def pause_resume():
    R, reqs, man, adm = setup(); c = Clock()
    def hook(e):
        if e.steps == 30: (R / 'PAUSE').write_text('cvpr')
    assert wc.run_block(R, Fake(R, c, hook=hook), reqs, man, adm, clock=c) == 'paused_at_wave_boundary'
    st = wc.scan(R, man); assert st['abandoned'] == [] and len(st['complete']) >= 1 and st['complete'] == list(range(len(st['complete'])))
    k = len(st['complete']); clear(R, 'PAUSE')
    assert wc.run_block(R, Fake(R, c, seed=1), reqs, man, adm, clock=c) == 'complete'
    st = wc.scan(R, man); assert st['complete'] == list(range(12)) and st['abandoned'] == [] and len(st['blocks']) == 2, st
    assert k < 12; records(R)


def stop_now_makeup():
    R, reqs, man, adm = setup(); c = Clock()
    def hook(e):
        if e.steps == 70: (R / 'STOP_NOW').write_text('urgent')
    assert wc.run_block(R, Fake(R, c, hook=hook), reqs, man, adm, clock=c) == 'operator_stop_now'
    st = wc.scan(R, man); assert len(st['abandoned']) == 1; a = st['abandoned'][0]; clear(R, 'STOP_NOW')
    assert wc.run_block(R, Fake(R, c, seed=2), reqs, man, adm, clock=c) == 'complete'
    st = wc.scan(R, man); assert len(st['complete']) == 12 and st['abandoned'] == [a] and a not in st['complete']
    assert st['complete'] == [w for w in range(13) if w != a], st; records(R)


def engine_error():
    R, reqs, man, adm = setup(); c = Clock()
    def hook(e):
        if e.steps == 50: raise RuntimeError('CUDA error (simulated)')
    try: wc.run_block(R, Fake(R, c, hook=hook), reqs, man, adm, clock=c); raise AssertionError('no raise')
    except RuntimeError: pass
    st = wc.scan(R, man); assert len(st['abandoned']) == 1
    ex = exits(R)[0]; assert ex['reason'] == 'engine_error' and ex['abandoned_wave'] == st['abandoned'][0]
    assert ex['charged_tokens'] == ex['token_bound'] >= ex['new_tokens'] and ex['admitted'] > ex['terminal']


def child(R, die_at, seed):
    """Child process for the kill cases: runs one block on a simulated clock and dies with os._exit at step die_at."""
    R, reqs, man, adm = setup(R); KEPT.clear(); t0 = float((R / 'CLOCK').read_text()) if (R / 'CLOCK').exists() else 1_000_000.0; c = Clock(t0)
    def hook(e):
        (R / 'CLOCK').write_text(repr(c.t))
        if e.steps == die_at: os._exit(9)
    wc.run_block(R, Fake(R, c, seed=seed, hook=hook), reqs, man, adm, clock=c)
    (R / 'CLOCK').write_text(repr(c.t))


def spawn(R, die_at, seed):
    return subprocess.run([sys.executable, '-I', str(Path(__file__).resolve()), 'child', str(R), str(die_at), str(seed)]).returncode


def killed_then_sealed():
    R, reqs, man, adm = setup(); assert spawn(R, 40, 0) == 9
    b = next(R.glob('block-*')); assert not (b / 'EXIT.json').exists()
    try: wc.run_block(R, Fake(R, Clock()), reqs, man, adm); raise AssertionError('resumed over an unsealed block')
    except AssertionError as e: assert 'unsealed' in str(e), e
    t_seal = float((R / 'CLOCK').read_text()) + 600
    wc.seal(b, now=t_seal, lock_check=False)
    s = wc.read(b / 'EXIT-SEALED-BY-OPERATOR.json'); terminal_tokens = sum(wc.read(p)['record']['output_tokens'] for p in (b / 'records').glob('*.json'))
    assert s['admitted'] > s['records'] and s['charged_tokens'] == terminal_tokens + 1100 * (s['admitted'] - s['records']), s
    assert s['charged_seconds'] == t_seal - wc.read(b / 'START.json')['started']
    c = Clock(t_seal); assert wc.run_block(R, Fake(R, c, seed=3), reqs, man, adm, clock=c) == 'complete'
    st = wc.scan(R, man); assert len(st['abandoned']) == 1 and len(st['complete']) == 12; records(R)


def ledger_required():
    R, reqs, man, adm = setup(); c = Clock()
    def hook(e):
        if e.steps == 20: (R / 'PAUSE').write_text('x')
    wc.run_block(R, Fake(R, c, hook=hook), reqs, man, adm, clock=c); b = next(R.glob('block-*'))
    (b / wc.LEDGER).rename(b / (wc.LEDGER + '.moved-for-test'))
    try: wc.scan(R, man); raise AssertionError('scanned a block without a ledger')
    except AssertionError as e: assert 'cost cannot be bounded' in str(e), e


def repeated_kills_within_token_cap():
    """Kills at random steps, each sealed promptly, then resumes, under a token cap of about four waves:
    the total charged (bounds included) must never exceed the cap."""
    R, reqs, man, adm = setup(cap=4 * 60 * 1000); rng = random.Random(4); t = 1_000_000.0
    for k in range(3):
        assert spawn(R, rng.randint(5, 20), k) == 9
        b = [x for x in sorted(R.glob('block-*')) if not (x / 'EXIT.json').exists() and not (x / 'EXIT-SEALED-BY-OPERATOR.json').exists()][0]
        t = float((R / 'CLOCK').read_text()) + 30; wc.seal(b, now=t, lock_check=False); (R / 'CLOCK').write_text(repr(t))
    c = Clock(t); reason = wc.run_block(R, Fake(R, c, seed=7), reqs, man, adm, clock=c)
    total = sum(e['charged_tokens'] for e in exits(R))
    assert reason in ('token_cap_at_boundary', 'token_cap_in_wave', 'complete') and total <= man['global_token_cap'], (reason, total)
    assert len([e for e in exits(R) if e['reason'] == 'process_died_sealed_by_operator']) == 3; records(R)


def gpu_hour_cap_with_load():
    """V23 overrun replay: load time charged before the first wave, then a wave far slower than the boundary projection
    (stalled steps, each under the 60 s margin). v1.0 ran past a 20 h cap; v1.1 must stop inside the wave, at or under the cap."""
    R, reqs, man, adm = setup(hours=4.0); c = Clock()
    blk = wc.open_block(R, man, adm, started=c.t, clock=c); c.t += 0.5 * 3600  # model load, charged

    class Slow(Fake):
        def step(self):
            w = self.wave[self.active[0]] if self.active else 0
            if w >= 4 and self.rng.random() < 0.95: self.clock.t += 55.0; return [], 0  # stalled step
            self.clock.t += 55.0 if w >= 4 else 10.0; self.clock.t -= 5.0
            return Fake.step(self)
    reason = wc.run_block(R, Slow(R, c), reqs, man, adm, clock=c, block=blk)
    e = exits(R)[0]
    assert reason == 'gpu_hour_cap_in_wave' and 3.9 * 3600 <= e['charged_seconds'] <= 4.0 * 3600, (reason, e['charged_seconds'] / 3600)
    st = wc.scan(R, man); assert len(st['abandoned']) == 1 and 4 <= len(st['complete']) and st['hours'] <= 4.0


def load_failure_charged():
    R, reqs, man, adm = setup(hours=3.0); c = Clock()
    blk = wc.open_block(R, man, adm, started=c.t, clock=c); c.t += 1800
    wc.close_block(blk, 'load_error', "OSError('weights')", None, 0, man, c)
    st = wc.scan(R, man); assert abs(st['hours'] - 0.5) < 1e-9 and st['tokens'] == 0 and st['started'] == []


def token_cap_in_wave():
    """A wave far larger in tokens than the projection: the hard cap stops it inside the wave, never above the cap."""
    R, reqs, man, adm = setup(cap=30_000, per_wave=6); c = Clock()
    tok = lambda w, r: 100 if w == 0 else 1100
    reason = wc.run_block(R, Fake(R, c, tok=tok), reqs, man, adm, clock=c)
    e = exits(R)[0]; assert reason == 'token_cap_in_wave' and e['charged_tokens'] <= 30_000, (reason, e)


def token_cap():
    R, reqs, man, adm = setup(cap=60 * 1000 * 5)  # about five waves of tokens
    c = Clock(); reason = wc.run_block(R, Fake(R, c), reqs, man, adm, clock=c)
    st = wc.scan(R, man); assert reason == 'token_cap_at_boundary' and st['abandoned'] == [] and 1 <= len(st['complete']) < 5, (reason, st)


def pool_exhausted():
    R, reqs, man, adm = setup(); c = Clock()
    for k in range(4):  # abandon four waves in a row
        def hook(e):
            if e.steps == 3: (R / 'STOP_NOW').write_text('x')
        wc.run_block(R, Fake(R, c, seed=k, hook=hook), reqs, man, adm, clock=c); clear(R, 'STOP_NOW')
    assert wc.run_block(R, Fake(R, c, seed=9), reqs, man, adm, clock=c) == 'wave_pool_exhausted'
    st = wc.scan(R, man); assert len(st['abandoned']) == 4 and len(st['complete']) == 11


if __name__ == '__main__':
    if sys.argv[1:2] == ['child']: child(sys.argv[2], int(sys.argv[3]), int(sys.argv[4])); sys.exit(0)
    for name, fn in [('clean 12 waves', clean), ('pause at boundary, resume', pause_resume), ('STOP_NOW abandons, make-up wave', stop_now_makeup),
                     ('engine error abandons, raises, charges the bound', engine_error), ('killed child refuses resume until sealed; seal charges the bound', killed_then_sealed),
                     ('block without a ledger refuses resume', ledger_required), ('three kills then resume stay within the token cap', repeated_kills_within_token_cap),
                     ('GPU-hour cap with load time and a slow wave (V23 replay)', gpu_hour_cap_with_load), ('load failure is charged', load_failure_charged),
                     ('token cap stops inside an oversized wave', token_cap_in_wave), ('token cap stops at a boundary', token_cap), ('make-up pool exhausted', pool_exhausted)]:
        fn(); print('PASS', name)
    print('ALL PASS'); print('kept temp folders:', len(KEPT), str(KEPT[0].parent))
