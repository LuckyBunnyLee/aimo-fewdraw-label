"""W9b numbers (t044) for draft v7.8: the fresh6h frozen test (explore/W9b/FRESH6H-SCORE-20261021.md) and M1b's
noise ceiling for READY63 (explore/M1b/NOISE-CEILING-20261021.md). Every value is read from a sha-pinned RESULT.json.
The fresh6h primary AUCs and P1/P2 point estimates are also recomputed here from the per-original tags and the frozen
predictions (own midrank Mann-Whitney AUC) and must match the scorer to 1e-12. Asserts check each value against the
figure in the two report files. Writes numbers/w9b-t044.json (exclusive create).
usage: python -I pair/aimo/paper/numbers/make_w9b_t044.py
"""
import hashlib, json
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
manifest = {}
PINS = {'explore/W9b/fresh6h/out/RESULT.json': 'e30d33c6ec7daccfdd0a12f6e67b249cefda692cbec9bb9ef5c6267a2309ed9c',
        'explore/W9b/fresh6h/out/PER-ORIGINAL.jsonl': '0e6a6657b948e78a088bd83d6fc5174ee4f4c239b3e6e110dd54358cd52ed49e',
        'explore/W9b/fresh6h/PREDICTIONS-BEFORE-RECORDS.json': 'd8c8549f45d1e8491594a0c0e658de60f862a53af073f7cdfa474ecc7b3e95d1',
        'explore/M1b/NOISE-CEILING-RESULT-20261021.json': '2b773b9c8316e77826b9c531c7f6f761a2323bdef293e86ed05b9a5c57bb8777'}


def load(rel, lines=False):
    p = ROOT / rel
    b = p.read_bytes()
    manifest[str(p)] = hashlib.sha256(b).hexdigest()
    assert manifest[str(p)] == PINS[rel], 'sha mismatch against the report: ' + rel
    t = b.decode('utf-8-sig')
    return [json.loads(x) for x in t.splitlines() if x.strip()] if lines else json.loads(t)


F6 = 'explore/W9b/fresh6h/out/RESULT.json'
PO = 'explore/W9b/fresh6h/out/PER-ORIGINAL.jsonl'
PR = 'explore/W9b/fresh6h/PREDICTIONS-BEFORE-RECORDS.json'
NC = 'explore/M1b/NOISE-CEILING-RESULT-20261021.json'
f6, po, pr, nc = load(F6), load(PO, lines=True), load(PR), load(NC)
v, raw = {}, {}


def put(k, val, src, ptr):
    assert k not in v, k
    v[k] = val; raw[k] = src + ' :: ' + ptr


def r(x, d):
    return round(x, d)


# fresh6h: operational counts and tags (primary block).
op, st = f6['primary']['operational'], f6['primary']['strict']
put('f6h_roster', len(po), PO, 'number of rows (one per roster original)')
put('f6h_attempts', op['attempts'], F6, '/primary/operational/attempts')
put('f6h_not_submitted', op['not_submitted'], F6, '/primary/operational/not_submitted')
put('f6h_trunc', op['truncated'], F6, '/primary/operational/truncated')
put('f6h_binding_fail', op['binding_fail'], F6, '/primary/operational/binding_fail')
put('f6h_not_reached', f6['primary']['not_reached'], F6, '/primary/not_reached')
put('f6h_reached', st['reached'], F6, '/primary/strict/reached')
put('f6h_binary', st['binary'], F6, '/primary/strict/binary')
put('f6h_nr', st['NR'], F6, '/primary/strict/NR')
put('f6h_r', st['R'], F6, '/primary/strict/R')
put('f6h_unusable', st['tag_counts']['UNUSABLE'], F6, '/primary/strict/tag_counts/UNUSABLE')
put('f6h_floor', st['tag_counts']['FLOOR'], F6, '/primary/strict/tag_counts/FLOOR')
put('f6h_boot', st['bootstrap_valid'], F6, '/primary/strict/bootstrap_valid')
put('f6h_nr_prev', r(st['panel_A4']['NR_prevalence'], 3), F6, '/primary/strict/panel_A4/NR_prevalence, 3 dp')
put('f6h_a4_acc', r(st['panel_A4']['acc05'], 3), F6, '/primary/strict/panel_A4/acc05, 3 dp')
put('f6h_allr_acc', r(st['panel_A4']['AllR_acc'], 3), F6, '/primary/strict/panel_A4/AllR_acc, 3 dp')
# Primary AUCs and the two frozen contrasts; the decision intervals are 97.5%.
for key, name in (('a4', 'AUC_A4'), ('len', 'AUC_length'), ('agree', 'AUC_baseagree')):
    put(f'f6h_auc_{key}', r(st[name]['est'], 3), F6, f'/primary/strict/{name}/est, 3 dp')
    put(f'f6h_auc_{key}_ci975', [r(x, 3) for x in st[name]['ci975']], F6, f'/primary/strict/{name}/ci975, 3 dp')
p1, p2 = st['P1_A4_minus_length'], st['P2_A4_minus_baseagree']
put('f6h_p1', r(p1['est'], 3), F6, '/primary/strict/P1_A4_minus_length/est, 3 dp')
# The upper decision bound is -0.00018; 3 dp would print -0.000, so it is kept at 4 dp.
put('f6h_p1_ci975', [r(p1['ci975'][0], 3), r(p1['ci975'][1], 4)], F6, '/primary/strict/P1_A4_minus_length/ci975, lower 3 dp, upper 4 dp')
put('f6h_p1_ci95', [r(x, 3) for x in p1['ci95']], F6, '/primary/strict/P1_A4_minus_length/ci95, 3 dp')
put('f6h_p2', r(p2['est'], 3), F6, '/primary/strict/P2_A4_minus_baseagree/est, 3 dp')
put('f6h_p2_ci975', [r(x, 3) for x in p2['ci975']], F6, '/primary/strict/P2_A4_minus_baseagree/ci975, 3 dp')
# Secondary S1: base agreement from the side-B draws, so it no longer shares draws with the side-A label.
s1 = f6['primary']['S1_sideA_label_sideB_agreement']
put('f6h_s1_binary', s1['binary'], F6, '/primary/S1_sideA_label_sideB_agreement/binary')
put('f6h_s1_auc_agree', r(s1['AUC_baseagree']['est'], 3), F6, '/primary/S1_sideA_label_sideB_agreement/AUC_baseagree/est, 3 dp')
put('f6h_s1_p2', r(s1['P2_A4_minus_baseagree']['est'], 3), F6, '/primary/S1_sideA_label_sideB_agreement/P2_A4_minus_baseagree/est, 3 dp')
put('f6h_s1_p2_ci975', [r(x, 3) for x in s1['P2_A4_minus_baseagree']['ci975']], F6, '/primary/S1_sideA_label_sideB_agreement/P2_A4_minus_baseagree/ci975, 3 dp')
# Reliability on this roster.
sh, bw = f6['primary']['wave_reliability']['split_half_n2B'], f6['D2_wave2']['between_wave_kappa']
put('f6h_kappa_split', r(sh['kappa'], 2), F6, '/primary/wave_reliability/split_half_n2B/kappa, 2 dp')
put('f6h_kappa_split_n', sh['n'], F6, '/primary/wave_reliability/split_half_n2B/n')
put('f6h_kappa_between', r(bw['kappa'], 3), F6, '/D2_wave2/between_wave_kappa/kappa, 3 dp')
put('f6h_kappa_between_n', bw['n'], F6, '/D2_wave2/between_wave_kappa/n')
put('f6h_d2_reached', f6['D2_wave2']['wave1_on_600']['reached'], F6, '/D2_wave2/wave1_on_600/reached')
# Deviation sensitivities.
d1 = f6['D1_completion']['strict']['P1_A4_minus_length']
put('f6h_d1_p1', r(d1['est'], 3), F6, '/D1_completion/strict/P1_A4_minus_length/est, 3 dp')
put('f6h_d1_p1_ci975', [r(x, 3) for x in d1['ci975']], F6, '/D1_completion/strict/P1_A4_minus_length/ci975, 3 dp')
put('f6h_d2w1_p1', r(f6['D2_wave2']['wave1_on_600']['P1_A4_minus_length']['est'], 4), F6, '/D2_wave2/wave1_on_600/P1_A4_minus_length/est, 4 dp')
put('f6h_d2w2_p1', r(f6['D2_wave2']['wave2_on_600']['P1_A4_minus_length']['est'], 4), F6, '/D2_wave2/wave2_on_600/P1_A4_minus_length/est, 4 dp')
assert pr['pointK_computable'] is False and f6['pointK'].startswith('not computable')

# Independent recompute of the primary point estimates from per-original tags and frozen predictions.
pred = {row['pid']: row for row in pr['rows']}


def auc(pos, neg):
    allv = sorted([(x, 1) for x in pos] + [(x, 0) for x in neg])
    ranks, i = [0.0] * len(allv), 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]:
            j += 1
        for k in range(i, j + 1):
            ranks[k] = (i + j) / 2 + 1
        i = j + 1
    rs = sum(rk for rk, (_, lab) in zip(ranks, allv) if lab)
    return (rs - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


tags = {row['pid']: row['primary']['strict'] for row in po if row['primary']['reached']}
agree = {row['pid']: row['primary']['agree4'] for row in po if row['primary']['reached']}
nr = [p for p, t in tags.items() if t == 'NR']; rr = [p for p, t in tags.items() if t == 'R']
assert (len(nr), len(rr)) == (st['NR'], st['R'])
own = {'AUC_A4': auc([pred[p]['interaction-A4'] for p in nr], [pred[p]['interaction-A4'] for p in rr]),
       'AUC_length': auc([pred[p]['words'] for p in nr], [pred[p]['words'] for p in rr]),
       'AUC_baseagree': auc([1 - agree[p] for p in nr], [1 - agree[p] for p in rr])}
for name, val in own.items():
    assert abs(val - st[name]['est']) < 1e-12, (name, val, st[name]['est'])
assert abs(own['AUC_A4'] - own['AUC_length'] - p1['est']) < 1e-12
assert abs(own['AUC_A4'] - own['AUC_baseagree'] - p2['est']) < 1e-12

# Noise ceiling (READY63, 100 strict-n4 waves on 34 originals).
o, orc, obs, pw = nc['originals'], nc['oracle_single_wave'], nc['observed_predictors'], nc['power']
assert nc['crosscheck']['primary_gain_matches_scorer'] and nc['crosscheck']['rf_length_auc_matches_scorer']
put('nc_originals', o['n'], NC, '/originals/n')
put('nc_q_min', r(o['q_hat_summary']['min'], 2), NC, '/originals/q_hat_summary/min, 2 dp')
put('nc_q_max', r(o['q_hat_summary']['max'], 2), NC, '/originals/q_hat_summary/max, 2 dp')
put('nc_q_mid_n', o['n_q_between_0_3_0_7'], NC, '/originals/n_q_between_0_3_0_7')
put('nc_q_n', o['q_hat_summary']['n'], NC, '/originals/q_hat_summary/n')
loo = orc['leave_wave_out']
put('nc_oracle_loo', r(loo['mean'], 3), NC, '/oracle_single_wave/leave_wave_out/mean, 3 dp')
put('nc_oracle_loo_range', [r(loo['p2_5'], 2), r(loo['p97_5'], 2)], NC, '/oracle_single_wave/leave_wave_out/p2_5, p97_5, 2 dp')
put('nc_oracle_param', r(orc['parametric_eb_truth']['mean'], 3), NC, '/oracle_single_wave/parametric_eb_truth/mean, 3 dp')
for k in ('3', '11'):
    put(f'nc_k{k}', r(nc['oracle_vs_k_wave_majority_label'][k]['mean'], 3), NC, f'/oracle_vs_k_wave_majority_label/{k}/mean, 3 dp')
put('nc_a4', r(obs['interaction-A4']['per_wave']['mean'], 3), NC, '/observed_predictors/interaction-A4/per_wave/mean, 3 dp')
put('nc_pointk', r(obs['point-K']['per_wave']['mean'], 3), NC, '/observed_predictors/point-K/per_wave/mean, 3 dp')
put('nc_charlen', r(obs['char-length (unfitted, longer=NR)']['per_wave']['mean'], 3), NC, '/observed_predictors/char-length (unfitted, longer=NR)/per_wave/mean, 3 dp')
put('nc_a4_share', r(obs['interaction-A4']['frac_of_ceiling_loo'], 2), NC, '/observed_predictors/interaction-A4/frac_of_ceiling_loo, 2 dp')
put('nc_a4_above_oracle', obs['interaction-A4']['waves_at_or_above_oracle_loo'], NC, '/observed_predictors/interaction-A4/waves_at_or_above_oracle_loo')
put('nc_gain_sd', r(obs['gain_A4_minus_pointK']['sd'], 3), NC, '/observed_predictors/gain_A4_minus_pointK/sd, 3 dp')
put('nc_waves_fixed', round(pw['conditional_on_34_originals']['waves_needed']), NC, '/power/conditional_on_34_originals/waves_needed, rounded')
put('nc_power_cap', r(pw['originals_random']['power_at_34_originals']['1000000'], 2), NC, '/power/originals_random/power_at_34_originals/1000000, 2 dp')
ob = pw['originals_random']['originals_needed_by_waves']
put('nc_orig_inf', round(ob['1000000']), NC, '/power/originals_random/originals_needed_by_waves/1000000, rounded')
put('nc_orig_100', round(ob['100']), NC, '/power/originals_random/originals_needed_by_waves/100, rounded')
put('nc_orig_4', round(ob['4']), NC, '/power/originals_random/originals_needed_by_waves/4, rounded')
put('nc_delta', pw['delta'], NC, '/power/delta')

# Checks against the two report files.
assert (v['f6h_roster'], v['f6h_attempts'], v['f6h_not_submitted'], v['f6h_trunc'], v['f6h_not_reached'], v['f6h_reached']) == (2657, 31884, 2203, 1563, 183, 2474)
assert (v['f6h_binary'], v['f6h_nr'], v['f6h_r'], v['f6h_unusable'], v['f6h_floor'], v['f6h_boot'], v['f6h_binding_fail']) == (1255, 286, 969, 1208, 11, 2000, 0)
assert (v['f6h_auc_a4'], v['f6h_auc_len'], v['f6h_auc_agree']) == (0.575, 0.620, 0.560)
assert (v['f6h_p1'], v['f6h_p1_ci975'], v['f6h_p1_ci95']) == (-0.045, [-0.088, -0.0002], [-0.083, -0.006])
assert (v['f6h_p2'], v['f6h_p2_ci975']) == (0.014, [-0.038, 0.065])
assert (v['f6h_s1_auc_agree'], v['f6h_s1_p2'], v['f6h_s1_p2_ci975'], v['f6h_s1_binary']) == (0.607, -0.046, [-0.101, 0.011], 1519)
assert (v['f6h_kappa_split'], v['f6h_kappa_split_n'], v['f6h_kappa_between'], v['f6h_kappa_between_n']) == (0.23, 1227, 0.316, 234)
assert (v['f6h_d1_p1'], v['f6h_d1_p1_ci975'], v['f6h_d2w1_p1'], v['f6h_d2w2_p1'], v['f6h_d2_reached']) == (-0.037, [-0.083, 0.010], -0.0005, 0.0132, 600)
assert (v['f6h_nr_prev'], v['f6h_a4_acc'], v['f6h_allr_acc']) == (0.228, 0.715, 0.772)
assert (v['nc_originals'], v['nc_q_min'], v['nc_q_max'], v['nc_q_mid_n'], v['nc_q_n']) == (34, 0.04, 0.7, 18, 32)
assert (v['nc_oracle_loo'], v['nc_oracle_loo_range'], v['nc_oracle_param'], v['nc_k3'], v['nc_k11']) == (0.764, [0.5, 0.96], 0.771, 0.805, 0.875)
assert (v['nc_a4'], v['nc_pointk'], v['nc_charlen'], v['nc_a4_share'], v['nc_a4_above_oracle'], v['nc_gain_sd']) == (0.623, 0.581, 0.559, 0.47, 14, 0.158)
assert (v['nc_waves_fixed'], v['nc_power_cap'], v['nc_orig_inf'], v['nc_orig_100'], v['nc_orig_4'], v['nc_delta']) == (79, 0.17, 272, 326, 1623, 0.05)

out = dict(tier='Exploratory; W9b t044 producer (fresh6h frozen test and the READY63 noise ceiling, for draft v7.8)', values=v, raw_pointers=raw,
           checks=dict(rule='values read from sha-pinned RESULT files as stated; fresh6h primary AUCs, P1 and P2 point estimates recomputed from PER-ORIGINAL.jsonl and PREDICTIONS-BEFORE-RECORDS.json to 1e-12; all asserted against the two report files'),
           _manifest=manifest, producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (Path(__file__).resolve().parent / 'w9b-t044.json').open('x', encoding='utf-8') as f:
    json.dump(out, f, indent=1)
print(len(v), 'values from', len(manifest), 'files')
print(json.dumps(v))
