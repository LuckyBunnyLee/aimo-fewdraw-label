"""Figure 1 for report v1.1d (AR1, 27 Oct; v4 with "tag" renamed "label" after the blind referee): (a) unchanged from v3e, the strict tag's no-edit null N0(p) for 1, 4, 16 and 64
draws per version (constructed, from explore/W9b/decomp/decomp.py's q); (b) SHAM Phase 1, prospective: per-original fragile
rate under the real rewrites against the identical-text copies, on the T1 jointly eligible originals (>= 3 waves binary for
both tags). Rates are k/n fractions, so identical points are merged and marker area is proportional to the square root of the number of
originals (the point at (0, 0) is labelled with its count). Data sha-pinned through numbers/ar1-t104.json. BLIND REPLAY PENDING for panel (b).
CPU only. Writes fig1_tag_null_sham_v4b.png and .sha256 next to this script (exclusive create).
usage: python -B pair/aimo/report/fig1_tag_null_sham_v4.py   (not -I: matplotlib is in user site-packages here)
"""
import hashlib, json, sys
from collections import Counter
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
RES = ROOT / 'from-box/research/W9d/sham1-score/tree/explore/W9b/sham1/v1.1/out/RESULT.json'
DC = ROOT / 'explore/W9b/decomp/decomp.py'
num = json.loads((HERE / 'numbers/ar1-t104.json').read_text(encoding='utf-8-sig')); vals = num['values']
assert hashlib.sha256(RES.read_bytes()).hexdigest() == num['_manifest'][str(RES).replace('/', '\\')], 'sham1 result changed since ar1-t104'
assert hashlib.sha256(DC.read_bytes()).hexdigest() == 'a37aebe72f582fd24ff9353ea273ed05abe70cf2ab6f5b1efff0a9bf85bb6929', 'decomp.py changed'
sys.path.insert(0, str(DC.parent)); from decomp import N0
res = json.loads(RES.read_text(encoding='utf-8-sig'))
rows = [r for r in res['per_original'] if r['n_joint'] >= 3]
assert len(rows) == vals['p1s_t1_n']

INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
SEQ = ['#a9c9f0', '#6ea6e6', '#2a78d6', '#164f96']
BLUE, ORANGE = '#2a78d6', '#eb6834'
plt.rcParams.update({'font.size': 10.5, 'axes.edgecolor': INK2, 'axes.labelcolor': INK, 'xtick.color': INK2, 'ytick.color': INK2,
                     'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': SURF, 'axes.facecolor': SURF})
fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.4), constrained_layout=True)

p = np.linspace(0.30, 0.999, 300)
for n, c in zip((1, 4, 16, 64), SEQ):
    a.plot(p, [N0(x, n) for x in p], color=c, lw=2, solid_capstyle='round', label=f'{n} draw' + ('s' if n > 1 else '') + ' per version')
a.axhline(2 / 3, color=INK2, lw=1, ls=(0, (3, 3)))
a.text(0.31, 2 / 3 + 0.02, 'limit 2/3 as draws grow', fontsize=9.5, color=INK2)
a.legend(loc='lower left', fontsize=9, frameon=False)
a.set_xlim(0.3, 1.0); a.set_ylim(0, 0.8); a.set_xticks([0.4, 0.6, 0.8, 1.0])
a.set_xlabel('Accuracy p among numeric answers\n(same for the original and both rewrites)'); a.set_ylabel('P(fragile | original ≥ 1 right,\nall 3n answers numeric)')
a.set_title('(a) The strict label with no edit effect', loc='left', fontsize=10.5, color=INK)
a.grid(True, color=GRID, lw=0.6); a.set_axisbelow(True)

xs = np.array([r['nr_sham_joint'] for r in rows]); ys = np.array([r['nr_real_joint'] for r in rows])
cnt = Counter(zip(np.round(xs, 6), np.round(ys, 6)))
px, py, pn = zip(*[(x, y, n) for (x, y), n in cnt.items()])
b.plot([0, 1], [0, 1], color=INK2, lw=1, ls=(0, (3, 3)))
b.text(0.70, 0.63, 'equal label rates', fontsize=9.5, color=INK2, rotation=38)
b.scatter(px, py, s=[16 * n ** 0.5 for n in pn], color=BLUE, alpha=0.55, edgecolor=SURF, linewidth=0.8, zorder=3)
b.scatter([xs.mean()], [ys.mean()], s=60, marker='D', color=ORANGE, edgecolor=SURF, linewidth=1.5, zorder=4)
n00 = cnt.get((0.0, 0.0), 0)
b.annotate(f'{n00} problems', (0, 0), xytext=(10, 6), textcoords='offset points', fontsize=9, color=INK2)
b.annotate('mean', (xs.mean(), ys.mean()), xytext=(7, -11), textcoords='offset points', fontsize=9.5, color=INK2)
b.set_xlim(-0.04, 1.02); b.set_ylim(-0.04, 1.02)
b.set_xlabel('Fragile rate, identical-text copies'); b.set_ylabel('Fragile rate, real rewrites')
b.set_title(f'(b) Prospective control, {len(rows)} problems', loc='left', fontsize=10.5, color=INK)
b.grid(True, color=GRID, lw=0.6); b.set_axisbelow(True)

out = HERE / 'fig1_tag_null_sham_v4b.png'
assert not out.exists(), 'exists; choose a new name'
fig.savefig(out, dpi=200)
(HERE / 'fig1_tag_null_sham_v4b.sha256').write_text(hashlib.sha256(out.read_bytes()).hexdigest() + '  fig1_tag_null_sham_v4b.png\n')
print(out, hashlib.sha256(out.read_bytes()).hexdigest(), 'mean sham', xs.mean(), 'mean real', ys.mean(), 'max marker n', max(pn))
