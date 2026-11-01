"""D14 numbers (t004) for report draft v0.4: the causal-length experiment E (P1 only), its stopped
compression arm, the AN-63 split and the AN-08 RF arm.
Values are read from sha-pinned raw result files: the frozen scorer's RESULT, the E eval freeze
(dose and power), the comp/para audit sample and union flags, the replay comparison, the AN-63 split
RESULT and the AN-08 RF RESULT. Two values are constructed from them ([C]): the length ratio exp(dose)
and the NR change a fully causal observational gradient predicts at this dose (gradient x dose).
Writes numbers/d14-t004.json (exclusive create). No models, GPU, network or sealed data.
usage: python -I pair/aimo/report/numbers/make_d14_t004.py
"""
import hashlib, json, math
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
CL = 'explore/W9b/causal_length/'
RES, FRZ, SMP, AUD = CL + 'score/RESULT.json', CL + 'final/EVAL-FREEZE.json', CL + 'final/AUDIT-SAMPLE.json', CL + 'final/audit/AUDIT-RESULTS.json'
R1, R2, CMP, A63, A08 = CL + 'final/audit/READER1.json', CL + 'final/audit/READER2.json', CL + 'replay/COMPARE.json', CL + 'an63/RESULT.json', 'explore/RA/an08-rf-20261024/RESULT-AN-08-RF.json'
PIN = {RES: 'dc5b00b5a96e4854fe4a4823426334015ff2c0b53fdbfb8557cbdc422794441b',
       FRZ: '123f4d74c055dc2fd9834fa36e748e9b0207df1ed228391474d273273a7610e2',
       SMP: 'e9c0c1cb30c3a386e4557146f8b198e4a22451efcea7b55f1473aa4f9e1374b3',
       AUD: '9ed32797068cf95714a4e9b215f8354103d3260f1cc1641a280d1b2a7a5072ea',
       R1: 'b91be30b', R2: 'abfda8bb',  # prefixes as listed in the P1 amendment's file table
       CMP: 'e2d4d2821b64eadfa2f8592df8ea7937fdeff601d6d60fa49c55a2af1f76b3b2',
       A63: '01b5d73103e1f0b002bd200b071ff3e50d87e939e584ffc6c5e9398836e7f411',
       A08: 'ad1a2f7efe899bccfb47960109cf9bb2d666dc159d34d60fd40459caa970ccef'}
manifest = {}


def js(rel):
    p = ROOT / rel; b = p.read_bytes(); h = hashlib.sha256(b).hexdigest()
    assert h.startswith(PIN[rel]), rel + ' changed'
    manifest[str(p)] = h
    return json.loads(b.decode('utf-8-sig'))


r, frz, smp, aud, rd1, rd2, cmp, a63, a08 = (js(x) for x in (RES, FRZ, SMP, AUD, R1, R2, CMP, A63, A08))
assert r['eval_freeze_sha256'] == PIN[FRZ] and rd1['audit_sample_sha256'] == rd2['audit_sample_sha256'] == PIN[SMP]
v, ptr = {}, {}


def put(k, val, pointer, src):
    assert k not in v, k
    v[k] = val; ptr[k] = src + ' :: ' + pointer


def r3(x): return round(x, 3)
def ci(x, nd=3): return [round(a, nd) for a in x]


# ---- design: cohort, waves, records, dose, power ----
put('cl_cohort', frz['cohort'], '/cohort', FRZ)
put('cl_cohort_nr', frz['cohort_counts']['NR'], '/cohort_counts/NR', FRZ)
put('cl_cohort_r', frz['cohort_counts']['R'], '/cohort_counts/R', FRZ)
put('cl_waves', frz['waves'], '/waves', FRZ)
put('cl_records', r['records'], '/records', RES)
assert r['records'] == r['requests'] == frz['requests']
put('cl_orig_waves', r['original_waves'], '/original_waves', RES)
put('cl_not_reached', r['original_waves_not_reached'], '/original_waves_not_reached', RES)
put('cl_dose', r3(frz['mean_dlog_pad_vs_control']), '/mean_dlog_pad_vs_control; 3 dp', FRZ)
pw = frz['power_by_base_rate']['0.290']
put('cl_power_005', round(pw['power_at_0p05'], 2), '/power_by_base_rate/0.290/power_at_0p05; 2 dp', FRZ)
put('cl_null_inside', round(pw['p_ci95_inside_0p05_under_null'], 2), '/power_by_base_rate/0.290/p_ci95_inside_0p05_under_null; 2 dp', FRZ)

# ---- compression arm audit (the stop) ----
arms = [row['arm'] for row in smp['rows']]
put('cl_audit_comp_n', arms.count('comp'), '/rows arm == comp count', SMP)
put('cl_audit_para_n', arms.count('para'), '/rows arm == para count', SMP)
put('cl_comp_flagged', aud['comp_flagged'], '/comp_flagged (union of two readers)', AUD)
put('cl_para_flagged', aud['para_flagged'], '/para_flagged (union of two readers)', AUD)
put('cl_comp_flagged_pct', round(100 * aud['comp_flagged'] / arms.count('comp')), '/comp_flagged over comp rows; integer %', AUD)
put('cl_comp_flagged_r1', sum(f['arm'] == 'comp' for f in rd1['flagged']), '/flagged arm == comp count', R1)
put('cl_comp_flagged_r2', sum(f['arm'] == 'comp' for f in rd2['flagged']), '/flagged arm == comp count', R2)

# ---- primary ----
P1 = r['P1']
put('cl_p1', r3(P1['est']), '/P1/est; 3 dp', RES)
put('cl_p1_n', P1['n'], '/P1/n (originals with a binary wave in both conditions)', RES)
put('cl_p1_ci95', ci(P1['ci95']), '/P1/ci95; 3 dp', RES)
put('cl_p1_ci975', ci(P1['ci975']), '/P1/ci975; 3 dp', RES)
put('cl_p1_hi975', r3(P1['ci975'][1]), '/P1/ci975[1] (upper limit); 3 dp', RES)
put('cl_p1_reading', P1['reading'], '/P1/reading', RES)

# ---- secondaries and mediation (95%) ----
S = r['secondaries']; M = r['mediation']
for key, node, ptr_ in (('cl_s2', S['S2_base_accuracy'], '/secondaries/S2_base_accuracy'), ('cl_dn0', S['dN0'], '/secondaries/dN0'),
                        ('cl_s4', S['S4_excess'], '/secondaries/S4_excess'), ('cl_s5', S['S5_family_gap'], '/secondaries/S5_family_gap'),
                        ('cl_s6_diff', S['S6_unusable']['diff'], '/secondaries/S6_unusable/diff'),
                        ('cl_s7_nr', S['S7_strata']['NR'], '/secondaries/S7_strata/NR'), ('cl_s7_r', S['S7_strata']['R'], '/secondaries/S7_strata/R'),
                        ('cl_m1', M['M1_mediator_all12'], '/mediation/M1_mediator_all12'),
                        ('cl_m2_direct', M['M2']['direct_a'], '/mediation/M2/direct_a'), ('cl_m2_indirect', M['M2']['indirect'], '/mediation/M2/indirect')):
    put(key, r3(node['est']), ptr_ + '/est; 3 dp', RES)
    put(key + '_ci', ci(node['ci95']), ptr_ + '/ci95; 3 dp', RES)
for key in ('cl_s7_nr', 'cl_s7_r'):
    put(key + '_n', S['S7_strata'][key[-2:].lstrip('_').upper()]['n'], '/secondaries/S7_strata/*/n', RES)
put('cl_s6_control', r3(S['S6_unusable']['control']), '/secondaries/S6_unusable/control; 3 dp', RES)
put('cl_s6_pad', r3(S['S6_unusable']['pad']), '/secondaries/S6_unusable/pad; 3 dp', RES)
S3 = S['S3_causal_vs_observational']
put('cl_s3', r3(S3['est'][0]), '/secondaries/S3_causal_vs_observational/est[0]; 3 dp', RES)
put('cl_s3_ci', ci(S3['ci95'][0]), '/secondaries/S3_causal_vs_observational/ci95[0]; 3 dp', RES)
put('cl_obs_grad', r3(S3['obs_gradient']['ame']), '/secondaries/S3_causal_vs_observational/obs_gradient/ame; 3 dp', RES)
put('cl_obs_grad_n', S3['obs_gradient']['n'], '/secondaries/S3_causal_vs_observational/obs_gradient/n', RES)
put('cl_m3_readout', M['M3_readout'], '/mediation/M3_readout', RES)
A = r['AN49']
put('cl_an49_readout', A['readout'], '/AN49/readout', RES)
put('cl_an49_slope', round(A['pred5_tracking']['slope']['est'], 2), '/AN49/pred5_tracking/slope/est; 2 dp', RES)
put('cl_an49_slope_ci', ci(A['pred5_tracking']['slope']['ci95'], 2), '/AN49/pred5_tracking/slope/ci95; 2 dp', RES)

# ---- constructed from the above ----
dose, ame = frz['mean_dlog_pad_vs_control'], S3['obs_gradient']['ame']
put('cl_len_ratio', round(math.exp(dose), 1), 'constructed: exp(mean_dlog_pad_vs_control), mean word-count ratio implied by the mean log dose; 1 dp', FRZ)
put('cl_causal_pred', r3(ame * dose), 'constructed: obs_gradient/ame (RESULT) x mean_dlog_pad_vs_control (EVAL-FREEZE); 3 dp', RES)

# ---- independent replay ----
put('cl_replay_n', len(cmp['stats']), '/stats count', CMP)
assert cmp['ALL_MATCH'] is True
put('cl_replay_maxdiff', float(f"{max(s['diff'] for s in cmp['stats'].values()):.0e}"), '/stats/*/diff maximum; 1 sig fig', CMP)

# ---- AN-63 split (pad - control) ----
st = a63['stats']
assert abs(a63['gate_S5'] - S['S5_family_gap']['est']) < 1e-12
for key, name in (('an63_w', 'W'), ('an63_n', 'N')):
    put(key, round(st[name]['est'], 4), f'/stats/{name}/est; 4 dp', A63)
    put(key + '_ci', ci(st[name]['ci95']), f'/stats/{name}/ci95; 3 dp', A63)
put('an63_share_n', round(a63['shares']['N'], 2), '/shares/N; 2 dp', A63)
for key, name in (('an63_dacc_gs', 'dacc_surface_gs'), ('an63_dacc_dlm', 'dacc_surface_dlm')):
    put(key, r3(st[name]['est']), f'/stats/{name}/est; 3 dp', A63)
    put(key + '_ci', ci(st[name]['ci95']), f'/stats/{name}/ci95; 3 dp', A63)
put('an63_n_wider', a63['n_originals_G_positive'], '/n_originals_G_positive', A63)
put('an63_n_narrower', a63['n_originals_G_negative'], '/n_originals_G_negative', A63)
put('an63_reading', a63['reading'], '/reading', A63)

# ---- AN-08 RF arm ----
au = a08['mean_wave_AUC']
put('an08_n', a08['n_originals'], '/n_originals', A08)
put('an08_waves', a08['waves'], '/waves', A08)
put('an08_rf_zero', r3(au['RF_zero']), '/mean_wave_AUC/RF_zero; 3 dp', A08)
put('an08_rf_mean', r3(au['RF_mean']), '/mean_wave_AUC/RF_mean; 3 dp', A08)
put('an08_rf_diff', r3(a08['H_source']['diff']), '/H_source/diff; 3 dp', A08)
put('an08_lr', r3(au['LR_zero']), '/mean_wave_AUC/LR_zero; 3 dp', A08)
assert au['LR_zero'] == au['LR_mean'] and a08['H_source']['supported'] is True
put('an08_chars', r3(au['characters']), '/mean_wave_AUC/characters; 3 dp', A08)
put('an08_waves_up', a08['waves_rf_mean_gt_zero'], '/waves_rf_mean_gt_zero', A08)
put('an08_waves_down', a08['waves_rf_mean_lt_zero'], '/waves_rf_mean_lt_zero', A08)

assert set(manifest) == {str(ROOT / k) for k in PIN}
out = {'tier': 'Exploratory; D14 t004 producer for report draft v0.4 (causal-length E P1 scored once by the frozen scorer, '
               'comp audit stop, AN-63 split, AN-08 RF arm; two values constructed).',
       'values': v, 'raw_pointers': ptr,
       'checks': ['every raw file sha pinned (reader files by the prefixes in the P1 amendment)',
                  'RESULT.eval_freeze_sha256 equals the pinned EVAL-FREEZE', 'both readers read the pinned audit sample',
                  'records == requests == frozen requests', 'replay ALL_MATCH', 'AN-63 gate equals RESULT S5',
                  'AN-08 LR unchanged under imputation and H_source supported'],
       '_manifest': manifest, 'producer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with (HERE / 'd14-t004.json').open('x', encoding='utf-8') as f:
    json.dump(out, f, indent=1)
print(json.dumps(v))
