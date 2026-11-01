"""[C] Power of the Phase 1 primary (all-answer solve change against the identical-text copies), by simulation.
True per-original rates: the 34 READY63 originals' all-answer solve rates over 400 draws per version
(DECOMP RESULT.json /D/D1/solve/per_original: p_b, p_g, p_d), sham true rate = p_b. 320 originals resampled with replacement,
4 draws per version per wave, normal-approximation 95% CI of the mean per-original difference (the scorer bootstraps;
at n = 320 the two agree closely). Also the null (rewrites set to p_b) for the false-positive rate. CPU, seconds.
usage: python -I explore/W9b/sham1/power_phase1.py
"""
import hashlib, json, pathlib
import numpy as np
SRC = pathlib.Path(r'E:/work/research-cycle/explore/W9b/decomp/RESULT.json')
per = json.loads(SRC.read_bytes())['D']['D1']['solve']['per_original']
P = np.array([[r['p_b'], r['p_g'], r['p_d']] for r in per])
true_mean = float(np.mean(P[:, 0] - (P[:, 1] + P[:, 2]) / 2))
rng = np.random.default_rng(20261025); SIMS = 2000; out = dict(source=str(SRC), source_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest(),
                                                               true_mean_edit_effect=true_mean, sims=SIMS)
for waves in (12, 8):
    n = 4 * waves
    for label, null in (('effect', False), ('null', True)):
        hits = lo_pos = 0; widths = []
        for _ in range(SIMS):
            ix = rng.integers(0, len(P), 320); pb, pg, pd = P[ix, 0], (P[ix, 0] if null else P[ix, 1]), (P[ix, 0] if null else P[ix, 2])
            sa, sb, g, d = (rng.binomial(n, x) / n for x in (pb, pb, pg, pd))
            delta = (sa + sb) / 2 - (g + d) / 2; m = delta.mean(); se = delta.std(ddof=1) / np.sqrt(len(delta))
            lo, hi = m - 1.96 * se, m + 1.96 * se; widths.append(hi - lo); lo_pos += lo > 0; hits += (lo > 0) or (hi < 0)
        out[f'W{waves}_{label}'] = dict(P_lower_bound_above_0=lo_pos / SIMS, P_any_resolved=hits / SIMS, mean_ci_halfwidth=float(np.mean(widths) / 2))
print(json.dumps(out, indent=1))
with open(pathlib.Path(__file__).with_name('POWER-PHASE1.json'), 'x') as g: json.dump(out, g, indent=1)
