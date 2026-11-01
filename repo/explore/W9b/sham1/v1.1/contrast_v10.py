"""Contrast replay: the v1.1 GPU-hour and token cases run against the frozen v1.0 wave_core.py (../wave_core.py),
to show the fixes change behaviour. CPU, fake engine, temp folders kept. usage: python -I contrast_v10.py"""
import importlib.util, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('wc10', HERE.parent / 'wave_core.py'); wc10 = importlib.util.module_from_spec(spec); spec.loader.exec_module(wc10)
sys.path.insert(0, str(HERE)); import test_wave_core as t


class Slow(t.Fake):
    def step(self):
        w = self.wave[self.active[0]] if self.active else 0
        if w >= 4 and self.rng.random() < 0.95: self.clock.t += 55.0; return [], 0
        self.clock.t += (55.0 if w >= 4 else 10.0) - 5.0
        return t.Fake.step(self)


R, reqs, man, adm = t.setup(hours=4.0); c = t.Clock()
r = wc10.run_block(R, Slow(R, c), reqs, man, adm, clock=c)
h = sum(wc10.read(b / 'EXIT.json')['elapsed'] for b in R.glob('block-*')) / 3600
print('v1.0 GPU-hour case (no load time charged), cap 4.0 h:', r, round(h, 3), 'h recorded')
R, reqs, man, adm = t.setup(cap=30_000, per_wave=6); c = t.Clock()
r = wc10.run_block(R, t.Fake(R, c, tok=lambda w, g: 100 if w == 0 else 1100), reqs, man, adm, clock=c)
n = sum(wc10.read(b / 'EXIT.json')['new_tokens'] for b in R.glob('block-*'))
print('v1.0 token case, cap 30000:', r, n, 'tokens')
