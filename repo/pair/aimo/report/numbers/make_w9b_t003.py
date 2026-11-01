"""W9b numbers (t003) for report draft v0.3: why per-original fragile rates vary (AN-50).
Values are read from explore/W9b/whyfrag/RESULT.json (sha-pinned; the run under spec
WHY-FRAGILITY-VARIES-SPEC-20261023.md, script why_fragility_varies.py). The curve points are
constructed: P(NR | base >= 1) when all three families share accuracy p, four draws each, from the
same formula as the script (checked against the script's text, whose sha the RESULT records).
The analysis was frozen before it ran, so the READY63 and fresh6h values are [E-pre]-able; the
curve values are [C]. Writes numbers/w9b-t003.json (exclusive create). No models, GPU, network or sealed data.
usage: python -I pair/aimo/report/numbers/make_w9b_t003.py
"""
import hashlib, json, math
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
RES, SCRIPT = 'explore/W9b/whyfrag/RESULT.json', 'explore/W9b/whyfrag/why_fragility_varies.py'
PIN = {RES: '01e52b412554ab20615faed8fbd9487dc8ef4dda94fa23763b9977aa7b3ec9ef',
       SCRIPT: '502a5c067a3935a35757692d22e3cf6f7bdac69c8cd49637f0037b9c3d793389'}
manifest = {}


def raw(rel):
    p = ROOT / rel; b = p.read_bytes(); h = hashlib.sha256(b).hexdigest()
    assert h == PIN[rel], rel + ' changed'
    manifest[str(p)] = h
    return b.decode('utf-8-sig')


r = json.loads(raw(RES)); src = raw(SCRIPT)
assert r['script_sha256'] == PIN[SCRIPT]
v, ptr = {}, {}


def put(k, val, pointer, src_rel=RES):
    assert k not in v, k
    v[k] = val; ptr[k] = src_rel + ' :: ' + pointer


def ci(x, nd=2): return [round(a, nd) for a in x['ci95']]


R6, A1, A2 = r['ready63'], r['ready63']['A1'], r['ready63']['A2']
put('wf_n_originals', R6['n_originals'], '/ready63/n_originals')
put('wf_n_used', R6['n_used'], '/ready63/n_used (>= 5 binary even waves)')
put('wf_n_excluded', len(R6['excluded']), '/ready63/excluded length')
put('wf_rho_n0', round(A1['N0']['rho'], 3), '/ready63/A1/N0/rho; 3 dp')
put('wf_rho_n0_ci', ci(A1['N0']['ci']), '/ready63/A1/N0/ci/ci95; 2 dp')
put('wf_rho_n1', round(A1['N1']['rho'], 3), '/ready63/A1/N1/rho; 3 dp')
put('wf_rho_n1_ci', ci(A1['N1']['ci']), '/ready63/A1/N1/ci/ci95; 2 dp')
put('wf_split_half', round(R6['split_half']['rho'], 3), '/ready63/split_half/rho; 3 dp')
put('wf_split_half_sb', round(R6['split_half']['spearman_brown'], 3), '/ready63/split_half/spearman_brown; 3 dp')
put('wf_ols_intercept', round(A1['ols_Y_on_N0']['intercept'], 3), '/ready63/A1/ols_Y_on_N0/intercept; 3 dp')
put('wf_ols_slope', round(A1['ols_Y_on_N0']['slope'], 2), '/ready63/A1/ols_Y_on_N0/slope; 2 dp')
put('wf_ols_r2', round(A1['ols_Y_on_N0']['R2'], 2), '/ready63/A1/ols_Y_on_N0/R2; 2 dp')
put('wf_excess', round(A1['mean_Y_minus_N0']['est'], 3), '/ready63/A1/mean_Y_minus_N0/est; 3 dp')
put('wf_excess_ci', ci(A1['mean_Y_minus_N0']['ci'], 3), '/ready63/A1/mean_Y_minus_N0/ci/ci95; 3 dp')
put('wf_y_range', [round(a, 2) for a in A1['Y_range']], '/ready63/A1/Y_range; 2 dp')
put('wf_overdisp_med', round(R6['overdispersion_median'], 2), '/ready63/overdispersion_median; 2 dp')
put('wf_rho_len', round(A2['L']['rho'], 2), '/ready63/A2/L/rho; 2 dp')
put('wf_rho_len_ci', ci(A2['L']['rho_ci']), '/ready63/A2/L/rho_ci/ci95; 2 dp')
for t, name in (('T7', 'acc'), ('T8', 'var'), ('T4', 'effort'), ('T9', 'gap_gs'), ('T10', 'gap_dlm')):
    put(f'wf_rho_{name}', round(A2[t]['rho'], 2), f'/ready63/A2/{t}/rho; 2 dp')
    put(f'wf_rho_{name}_ci', ci(A2[t]['rho_ci']), f'/ready63/A2/{t}/rho_ci/ci95; 2 dp')
    put(f'wf_pc_{name}', round(A2[t]['partial_L_N0'], 2), f'/ready63/A2/{t}/partial_L_N0; 2 dp')
    put(f'wf_pc_{name}_ci', ci(A2[t]['partial_L_N0_ci']), f'/ready63/A2/{t}/partial_L_N0_ci/ci95; 2 dp')
tested = [t for t, x in A2.items() if t != 'L' and x.get('perm_p_L_N0') is not None]
put('wf_n_props_tested', len(tested), '/ready63/A2/* count with perm_p_L_N0')
put('wf_min_perm_p', round(min(A2[t]['perm_p_L_N0'] for t in tested), 2), '/ready63/A2/*/perm_p_L_N0 minimum; 2 dp')
put('wf_min_holm_p', min(A2[t]['holm_p_L_N0'] for t in tested), '/ready63/A2/*/holm_p_L_N0 minimum')

W = r['fresh6h']['W2_600']
put('wf_f6_n', W['n'], '/fresh6h/W2_600/n'); put('wf_f6_nr', W['NR'], '/fresh6h/W2_600/NR')
put('wf_f6_auc_n0', round(W['N0']['auc'], 3), '/fresh6h/W2_600/N0/auc; 3 dp')
put('wf_f6_auc_n0_ci', ci(W['N0']['auc_ci']), '/fresh6h/W2_600/N0/auc_ci/ci95; 2 dp')
put('wf_f6_auc_len', round(W['L']['auc'], 3), '/fresh6h/W2_600/L/auc; 3 dp')
put('wf_f6_auc_len_ci', ci(W['L']['auc_ci']), '/fresh6h/W2_600/L/auc_ci/ci95; 2 dp')
put('wf_f6_n0_coef', round(W['N0']['logit_coef_given_L'], 2), '/fresh6h/W2_600/N0/logit_coef_given_L (per SD); 2 dp')
put('wf_f6_n0_coef_ci', ci(W['N0']['logit_coef_ci']), '/fresh6h/W2_600/N0/logit_coef_ci/ci95; 2 dp')

# ---- constructed: the exchangeable-family curve (same formula as the script) ----
LINE = "num = sum(binom(b, pb) * binom(s1, pg) * binom(s2, pd) for b in range(1, 5) for s1 in range(5) for s2 in range(5) if min(s1, s2) < b)"
assert LINE in src, 'curve formula differs from the script'


def binom(k, p, n=4): return math.comb(n, k) * p ** k * (1 - p) ** (n - k)


def n0(p):
    num = sum(binom(b, p) * binom(s1, p) * binom(s2, p) for b in range(1, 5) for s1 in range(5) for s2 in range(5) if min(s1, s2) < b)
    return num / (1 - binom(0, p))


for p in (0.99, 0.95, 0.9, 0.8, 0.5):
    put(f'wf_curve_{round(100 * p)}', round(n0(p), 2), f'constructed: N0(p={p}), 2 dp', SCRIPT)
peak = max((n0(i / 1000), i / 1000) for i in range(5, 1000))
put('wf_curve_max', round(peak[0], 2), 'constructed: max over p of N0(p), grid 0.001; 2 dp', SCRIPT)
put('wf_curve_argmax', round(peak[1], 2), 'constructed: argmax over p of N0(p), grid 0.001; 2 dp', SCRIPT)
# accuracy drop that alone raises N0 by 0.05, from a starting accuracy (for the AN-49 prediction)
for p0 in (0.95, 0.9):
    target = n0(p0) + 0.05; p = p0
    while n0(p) < target: p -= 0.0005
    put(f'wf_drop_for_005_from_{round(100 * p0)}', round(p0 - p, 3), f'constructed: smallest accuracy drop from {p0} that raises N0 by 0.05, step 0.0005; 3 dp', SCRIPT)

assert set(manifest) == {str(ROOT / k) for k in PIN}
out = {'tier': 'Exploratory; W9b t003 producer for report draft v0.3 (AN-50 why-fragility values, frozen-spec run; curve values constructed).',
       'values': v, 'raw_pointers': ptr,
       'checks': ['RESULT and script shas pinned', 'RESULT.script_sha256 equals the pinned script', 'curve formula line found verbatim in the script'],
       '_manifest': manifest, 'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (HERE / 'w9b-t003.json').open('x', encoding='utf-8') as f:
    json.dump(out, f, indent=1)
print(json.dumps(v))
