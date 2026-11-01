"""W9b numbers (t084) for report draft v0.6: the strict-tag decomposition (DECOMP), the identical-text sham
(SHAM Phase 0), the Phase 1 sham design and cost (spec text), and the X1-173 frozen transfer.
Values are read from sha-pinned raw outputs:
- explore/W9b/decomp/RESULT.json (spec DECOMP-SPEC-20261025.md, script decomp.py; run once, E-post on READY63)
- explore/W9b/decomp/SHAM-PHASE0-RESULT.json (spec SHAM-SPEC-20261025.md, script sham_phase0.py; run once, E-post)
- explore/W9b/decomp/SHAM-SPEC-20261025.md (Phase 1 design numbers, read from the frozen text; constructed, not measured)
- explore/X1/continuous0910/173/APPLY-RA-20261024/METRICS.json (RA, applied and scored once; blind replay agreed)
Writes numbers/w9b-t084.json (exclusive create). No models, GPU, network or sealed data.
usage: python -I pair/aimo/report/numbers/make_w9b_t084.py
"""
import hashlib, json, re
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
DC, SH, SPEC, X173 = ('explore/W9b/decomp/RESULT.json', 'explore/W9b/decomp/SHAM-PHASE0-RESULT.json',
                      'explore/W9b/decomp/SHAM-SPEC-20261025.md', 'explore/X1/continuous0910/173/APPLY-RA-20261024/METRICS.json')
PIN = {DC: 'f70423eb7b03d70ac5252fdaee8464705b802cd0a3dc8b3d66127d3bb12ace0f',
       SH: '7cbdc2f0c899ea72ad40e5726c6f8dde1d627f00e4e027572feeece3b92d7b91',
       SPEC: '019827a0670718a78a5eaee262c8212100d917ecc77f7a38eb5bf41f61a670f4',
       X173: 'aebcca9bc5ade61739b26f54906b0fdbec1f1d45626a5682448b10f39eea8617'}
manifest = {}


def raw(rel):
    p = ROOT / rel; b = p.read_bytes(); h = hashlib.sha256(b).hexdigest()
    assert h == PIN[rel], rel + ' changed'
    manifest[str(p)] = h
    return b.decode('utf-8-sig')


dc, sh, spec, x = json.loads(raw(DC)), json.loads(raw(SH)), raw(SPEC), json.loads(raw(X173))
assert dc['script_sha256'] == 'a37aebe72f582fd24ff9353ea273ed05abe70cf2ab6f5b1efff0a9bf85bb6929'
assert sh['script_sha256'] == 'ae83857b69961a8cf15ffe85024e281c2f5783f3223c55d819fe0f2b0e138bd9'
v, ptr = {}, {}


def put(k, val, pointer, src=DC):
    assert k not in v, k
    v[k] = val; ptr[k] = src + ' :: ' + pointer


r3 = lambda a: round(a, 3)
def c3(d): return [round(a, 3) for a in d['ci95']]
def c2(d): return [round(a, 2) for a in d['ci95']]

# ---- DECOMP (b) ----
put('dc_n_used', dc['n_used'], '/n_used (>= 5 binary even waves)')
put('dc_n_originals', dc['n_originals'], '/n_originals')
B1 = dc['B1']
for k, src in (('E_base', 'E_base'), ('E_pool', 'E_pool'), ('E_diff', 'E_base_minus_E_pool')):
    put('dc_' + k, r3(B1[src]['est']), f'/B1/{src}/est; 3 dp')
    put('dc_' + k + '_ci', c3(B1[src]['ci_original']), f'/B1/{src}/ci_original/ci95; 3 dp')
put('dc_mean_pb', r3(B1['mean_p_b']), '/B1/mean_p_b; 3 dp'); put('dc_mean_ppool', r3(B1['mean_p_pool']), '/B1/mean_p_pool; 3 dp')
B2 = dc['B2']
for k in ('base', 'pool'):
    put(f'dc_rho_{k}', r3(B2[f'rho_{k}']), f'/B2/rho_{k}; 3 dp'); put(f'dc_rho_{k}_ci', c2(B2[f'rho_{k}_ci']), f'/B2/rho_{k}_ci/ci95; 2 dp')
B4 = dc['B4']
put('dc_meanY', r3(B4['mean_Y']['est']), '/B4/mean_Y/est; 3 dp'); put('dc_meanY_ci', c3(B4['mean_Y']['ci_original']), '/B4/mean_Y/ci_original/ci95; 3 dp')
for k, src in (('null', 'null_at_base'), ('edit', 'edit_component'), ('resid', 'residual')):
    put(f'dc_{k}', r3(B4[src]['est']), f'/B4/{src}/est; 3 dp'); put(f'dc_{k}_ci', c3(B4[src]['ci_original']), f'/B4/{src}/ci_original/ci95; 3 dp')
    put(f'dc_{k}_share', round(B4[src]['share'], 2), f'/B4/{src}/share; 2 dp')
B5 = dc['B5']
put('dc_kappa_even', r3(B5['kappa_observed_even']), '/B5/kappa_observed_even; 3 dp'); put('dc_kappa_even_ci', c2(B5['kappa_observed_ci']), '/B5/kappa_observed_ci/ci95; 2 dp')
put('dc_kappa_impl', r3(B5['kappa_implied_Q1']), '/B5/kappa_implied_Q1; 3 dp')
# ---- DECOMP (d) ----
D1 = dc['D']['D1']
for lab, k in (('solve', 'solve'), ('numeric_only', 'num')):
    d = D1[lab]
    put(f'dc_delta_{k}', r3(d['mean_delta']), f'/D/D1/{lab}/mean_delta; 3 dp'); put(f'dc_delta_{k}_ci', c3(d['ci_original']), f'/D/D1/{lab}/ci_original/ci95; 3 dp')
    put(f'dc_tau_{k}', r3(d['tau']), f'/D/D1/{lab}/tau; 3 dp'); put(f'dc_tau_{k}_ci', c3(d['tau_ci']), f'/D/D1/{lab}/tau_ci/ci95; 3 dp')
put('dc_z_sig', D1['solve']['n_abs_z_gt_1_96'], '/D/D1/solve/n_abs_z_gt_1_96'); put('dc_z_tests', D1['solve']['n_tests'], '/D/D1/solve/n_tests')
put('dc_z_expected', round(D1['solve']['expected_under_null'], 1), '/D/D1/solve/expected_under_null; 1 dp')
put('dc_draws_per_arm_all', 400, '/D/D1/solve/per_original: 100 waves x 4 draws per family (spec section 3); checked below')
per = D1['solve']['per_original']
top = sorted(per, key=lambda r: -r['delta_edit'])[:3]
excl = set(dc['excluded'])
put('dc_top3_excluded', sum(r['pid'] in excl for r in top), '/D/D1/solve/per_original: top 3 by delta_edit, count in /excluded')
put('dc_top_drop', round(max(max(r['delta_gs'], r['delta_dlm']) for r in per), 2), '/D/D1/solve/per_original: max of delta_gs, delta_dlm; 2 dp')
D2 = dc['D']['D2']
put('dc_edit_share_nr', round(D2['edit_share_of_NR'], 2), '/D/D2/edit_share_of_NR; 2 dp')
put('dc_tag_rel_edit', r3(D2['tag_reliability_for_edit']), '/D/D2/tag_reliability_for_edit; 3 dp')
D3 = dc['D']['D3']
for p in ('0.5', '0.8', '0.9', '0.95', '0.99'):
    for d in ('0.05', '0.1', '0.2'):
        put(f'dc_lr_p{p[2:]}_d{d[2:]}', round(D3['LR_single_NR'][p][d], 2), f'/D/D3/LR_single_NR/{p}/{d}; 2 dp')
for p in ('0.5', '0.9', '0.95', '0.99'):
    put(f'dc_n0_p{p[2:]}', round(D3['N0_by_n'][p]['4'], 2), f'/D/D3/N0_by_n/{p}/4; 2 dp')
for n in ('1', '4', '16', '64'):
    put(f'dc_n0_p9_n{n}', round(D3['N0_by_n']['0.9'][n], 2), f'/D/D3/N0_by_n/0.9/{n}; 2 dp')
for p in ('0.9', '0.5'):
    for d in ('0.05', '0.1'):
        put(f'dc_draws_p{p[2:]}_d{d[2:]}', D3['draws_per_arm'][p][d], f'/D/D3/draws_per_arm/{p}/{d}')
for d in ('0.05', '0.1'):
    for n in ('4', '64'):
        put(f'dc_K_mean_d{d[2:]}_n{n}', D3['problems_for_mean_delta'][d][n], f'/D/D3/problems_for_mean_delta/{d}/{n}')
for r in ('0.3', '0.5'):
    put(f'dc_K_r{r[2:]}_tag', D3['problems_for_predictor_r'][r]['strict_tag_n4_edit_component'], f'/D/D3/problems_for_predictor_r/{r}/strict_tag_n4_edit_component')
    for n in ('16', '64'):
        put(f'dc_K_r{r[2:]}_n{n}', D3['problems_for_predictor_r'][r][f'delta_hat_n{n}'], f'/D/D3/problems_for_predictor_r/{r}/delta_hat_n{n}')
for n in ('4', '64'):
    put(f'dc_rel_n{n}', round(D3['reliability_delta_hat'][n], 2), f'/D/D3/reliability_delta_hat/{n}; 2 dp')
put('dc_pbar', round(D3['pbar'], 2), '/D/D3/pbar; 2 dp')
S1 = dc['S1']
put('dc_s1_n', S1['n'], '/S1/n'); put('dc_s1_nr', S1['NR'], '/S1/NR')
for k in ('base', 'pool'):
    put(f'dc_s1_auc_{k}', r3(S1[f'auc_{k}']), f'/S1/auc_{k}; 3 dp'); put(f'dc_s1_auc_{k}_ci', c2(S1[f'auc_{k}_ci']), f'/S1/auc_{k}_ci/ci95; 2 dp')
put('dc_s1_diff_ci', c3(S1['diff_ci']), '/S1/diff_ci/ci95 (base minus pool); 3 dp')

# ---- SHAM Phase 0 (c) ----
put('sh_n_used', sh['n_used'], '/n_used', SH)
put('sh_triples', 33, 'spec Phase 0: 33 wave triples per original; checked against per_original counts', SH)
assert all(sum(r['sham_counts'].values()) == 33 for r in sh['per_original'])
for k, src in (('false', 'P0_1_false_fragility'), ('real', 'mean_real_NR'), ('delta', 'P0_2_delta'), ('cal', 'P0_3_sham_minus_N0')):
    put(f'sh_{k}', r3(sh[src]['est']), f'/{src}/est; 3 dp', SH); put(f'sh_{k}_ci', c3(sh[src]), f'/{src}/ci95; 3 dp', SH)
put('sh_share', round(sh['P0_2_sham_share_of_real']['est'], 2), '/P0_2_sham_share_of_real/est; 2 dp', SH)
put('sh_share_ci', c2(sh['P0_2_sham_share_of_real']), '/P0_2_sham_share_of_real/ci95; 2 dp', SH)

# ---- SHAM Phase 1 design (frozen spec text; constructed) ----
m = re.search(r'\*\*([\d,]+) requests\*\*', spec); put('sh1_requests', m[1], 'spec text "**N requests**"', SPEC)
m = re.search(r'about \*\*([\d.]+) GPU-h\*\* on the 5070', spec); put('sh1_gpu_h', float(m[1]), 'spec text "about N GPU-h on the 5070"', SPEC)
m = re.search(r'(\d+) originals drawn at random from the ([\d,]+) reached', spec); put('sh1_originals', int(m[1]), 'spec text cohort size', SPEC); put('sh1_pool', m[2], 'spec text reached pool', SPEC)
m = re.search(r'Planned W = (\d+)', spec); put('sh1_waves', int(m[1]), 'spec text "Planned W = N"', SPEC)
m = re.search(r'\*\*Caps: (\d+) GPU-h and (\d+)M tokens\.\*\*', spec); put('sh1_cap_h', int(m[1]), 'spec text caps', SPEC); put('sh1_cap_mtok', int(m[2]), 'spec text caps', SPEC)

# ---- X1-173 frozen transfer ----
pr = [r for r in x['results'] if r['scope'] == 'PRIMARY_raw_binary52'][0]
put('x173_all', x['all_originals'], '/all_originals', X173); put('x173_unusable', x['state_counts']['UNUSABLE'], '/state_counts/UNUSABLE', X173)
put('x173_n', pr['originals'], '/results[PRIMARY]/originals', X173); put('x173_nr', pr['NR'], '/results[PRIMARY]/NR', X173)
put('x173_auc', r3(pr['candidate_AUC']), '/results[PRIMARY]/candidate_AUC; 3 dp', X173); put('x173_len', r3(pr['frozen_length_AUC']), '/results[PRIMARY]/frozen_length_AUC; 3 dp', X173)
put('x173_gain', r3(pr['gain']), '/results[PRIMARY]/gain; 3 dp', X173); put('x173_gain_ci', [round(a, 3) for a in pr['gain_ci95']], '/results[PRIMARY]/gain_ci95; 3 dp', X173)
put('x173_rule', pr['exploratory_transfer_rule'], '/results[PRIMARY]/exploratory_transfer_rule', X173)

out = HERE / 'w9b-t084.json'
with open(out, 'x', encoding='utf-8') as fh:
    json.dump(dict(tier='Exploratory, post hoc on READY63/fresh6h draws already analysed (DECOMP, SHAM Phase 0 run once each); '
                        'formula tables constructed; X1-173 applied and scored once by RA; W9b t084 producer for report v0.6.',
                   values=v, raw_pointers=ptr, _manifest=manifest), fh, indent=1, ensure_ascii=False)
print(len(v), 'keys ->', out, hashlib.sha256(out.read_bytes()).hexdigest())
