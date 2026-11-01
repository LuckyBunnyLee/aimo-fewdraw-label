"""CPU test of wave_core.py pause/resume rules with a fake engine and a simulated clock (no GPU, no vLLM).
usage: python -I explore/W9b/sham1/test_wave_core.py     (works in a temp folder; prints PASS per case)"""
import json, random, shutil, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); import wave_core as wc


class Clock:
    def __init__(self): self.t = 1_000_000.0
    def __call__(self): return self.t


class Fake:
    """Finishes 1-6 active requests per step, 900-1100 tokens each; can create PAUSE/STOP_NOW or raise at a set step."""
    def __init__(self, R, clock, seed=0, hook=None):
        self.R, self.clock, self.rng, self.active, self.steps, self.hook = R, clock, random.Random(seed), [], 0, hook
    def add(self, key, q): self.active.append(key)
    def step(self):
        self.steps += 1; self.clock.t += 5.0
        if self.hook: self.hook(self)
        out = []
        for _ in range(min(len(self.active), self.rng.randint(1, 6))):
            k = self.active.pop(self.rng.randrange(len(self.active))); n = self.rng.randint(900, 1100)
            out.append(dict(key=k, token_ids=[1] * n, text='work\nANSWER: 1', finish_reason='stop'))
        return out, sum(len(y['token_ids']) for y in out)
    def close(self): pass


def setup(waves_built=15, planned=12, per=3, cap=10**12, hours=10**6):
    R = Path(tempfile.mkdtemp(prefix='sham1-test-'))
    reqs = [dict(wave=w, identity_sha256=wc.sha(f'{w}|{p}|{f}|{r}'.encode()), seed=1, identity=dict(w=w, p=p, f=f, r=r))
            for w in range(waves_built) for p in range(per) for f in range(5) for r in range(4)]
    man = dict(waves_built=waves_built, waves_planned=planned, requests_per_wave=per * 20, global_token_cap=cap, gpu_hour_cap=hours, max_active=8)
    adm = dict(absolute_deadline=10**12)
    return R, reqs, man, adm


def records(R):
    keys = [p.stem for p in R.glob('block-*/records/*.json')]
    assert len(keys) == len(set(keys)), 'an identity was issued twice'
    return keys


def case(name, fn):
    fn(); print('PASS', name)


def clean():
    R, reqs, man, adm = setup(); c = Clock()
    assert wc.run_block(R, Fake(R, c), reqs, man, adm, clock=c) == 'complete'
    st = wc.scan(R, man); assert st['complete'] == list(range(12)) and st['abandoned'] == []; records(R); shutil.rmtree(R)


def pause_resume():
    R, reqs, man, adm = setup(); c = Clock()
    def hook(e):
        if e.steps == 30: (R / 'PAUSE').write_text('cvpr')
    assert wc.run_block(R, Fake(R, c, hook=hook), reqs, man, adm, clock=c) == 'paused_at_wave_boundary'
    st = wc.scan(R, man); assert st['abandoned'] == [] and len(st['complete']) >= 1 and st['complete'] == list(range(len(st['complete'])))
    k = len(st['complete'])
    (R / 'PAUSE').unlink()
    assert wc.run_block(R, Fake(R, c, seed=1), reqs, man, adm, clock=c) == 'complete'
    st = wc.scan(R, man); assert st['complete'] == list(range(12)) and st['abandoned'] == [] and len(st['blocks']) == 2, st
    assert k < 12; records(R); shutil.rmtree(R)


def stop_now_makeup():
    R, reqs, man, adm = setup(); c = Clock()
    def hook(e):
        if e.steps == 70: (R / 'STOP_NOW').write_text('urgent')
    assert wc.run_block(R, Fake(R, c, hook=hook), reqs, man, adm, clock=c) == 'operator_stop_now'
    st = wc.scan(R, man); assert len(st['abandoned']) == 1; a = st['abandoned'][0]
    (R / 'STOP_NOW').unlink()
    assert wc.run_block(R, Fake(R, c, seed=2), reqs, man, adm, clock=c) == 'complete'
    st = wc.scan(R, man); assert len(st['complete']) == 12 and st['abandoned'] == [a] and a not in st['complete']
    assert st['complete'] == [w for w in range(13) if w != a], st; records(R); shutil.rmtree(R)


def engine_error():
    R, reqs, man, adm = setup(); c = Clock()
    def hook(e):
        if e.steps == 50: raise RuntimeError('CUDA error (simulated)')
    try: wc.run_block(R, Fake(R, c, hook=hook), reqs, man, adm, clock=c); raise AssertionError('no raise')
    except RuntimeError: pass
    st = wc.scan(R, man); assert len(st['abandoned']) == 1
    ex = wc.read(next(R.glob('block-*')) / 'EXIT.json'); assert ex['reason'] == 'engine_error' and ex['abandoned_wave'] == st['abandoned'][0]
    shutil.rmtree(R)


def killed_then_sealed():
    R, reqs, man, adm = setup(); c = Clock()
    assert wc.run_block(R, Fake(R, c), reqs, man, adm, clock=c) == 'complete'  # then fake a dead block after it
    R2, reqs2, man2, adm2 = setup(); c2 = Clock()
    def hook(e):
        if e.steps == 40: raise KeyboardInterrupt  # not caught by run_block's except: EXIT still written by finally
    try: wc.run_block(R2, Fake(R2, c2, hook=hook), reqs2, man2, adm2, clock=c2)
    except KeyboardInterrupt: pass
    b = next(R2.glob('block-*')); (b / 'EXIT.json').unlink()  # simulate a hard kill: no EXIT.json
    try: wc.run_block(R2, Fake(R2, c2), reqs2, man2, adm2, clock=c2); raise AssertionError('resumed over an unsealed block')
    except AssertionError as e: assert 'unsealed' in str(e), e
    wc.seal(b)
    assert wc.run_block(R2, Fake(R2, c2, seed=3), reqs2, man2, adm2, clock=c2) == 'complete'
    st = wc.scan(R2, man2); assert len(st['abandoned']) == 1 and len(st['complete']) == 12; records(R2)
    shutil.rmtree(R); shutil.rmtree(R2)


def token_cap():
    R, reqs, man, adm = setup(cap=60 * 1000 * 5)  # about five waves of tokens
    c = Clock(); reason = wc.run_block(R, Fake(R, c), reqs, man, adm, clock=c)
    st = wc.scan(R, man); assert reason == 'token_cap_at_boundary' and st['abandoned'] == [] and 1 <= len(st['complete']) < 5, (reason, st)
    shutil.rmtree(R)


def pool_exhausted():
    R, reqs, man, adm = setup(); c = Clock(); n = 0
    for k in range(4):  # abandon four waves in a row
        def hook(e):
            if e.steps == 3: (R / 'STOP_NOW').write_text('x')
        wc.run_block(R, Fake(R, c, seed=k, hook=hook), reqs, man, adm, clock=c); (R / 'STOP_NOW').unlink()
    assert wc.run_block(R, Fake(R, c, seed=9), reqs, man, adm, clock=c) == 'wave_pool_exhausted'
    st = wc.scan(R, man); assert len(st['abandoned']) == 4 and len(st['complete']) == 11; shutil.rmtree(R)


for name, fn in [('clean 12 waves', clean), ('pause at boundary, resume', pause_resume), ('STOP_NOW abandons, make-up wave', stop_now_makeup),
                 ('engine error abandons and raises', engine_error), ('killed block refuses resume until sealed', killed_then_sealed),
                 ('token cap stops at a boundary', token_cap), ('make-up pool exhausted', pool_exhausted)]:
    case(name, fn)
print('ALL PASS')
