"""W9b numbers (t043) for draft v7.7: values needed by the wording fixes from M1b's verification of v7.6
(pair/aimo/VERIFY-v7.6-M1b.md, items W1, W4-W7, W12). Every value is read or computed from a sha-pinned raw file:
the READY63 reliability RESULT.json, the X1-154 RESULT.json and frozen roster, the X3-81 RESULT.json, X1-180
METRICS.json and the Q1 resolution file. Asserts check each value against the figure M1b re-derived independently.
Writes numbers/w9b-t043.json (exclusive create).
usage: python -I pair/aimo/paper/numbers/make_w9b_t043.py
"""
import hashlib, json, statistics
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
manifest = {}


def load(rel):
    p = ROOT / rel
    b = p.read_bytes()
    manifest[str(p)] = hashlib.sha256(b).hexdigest()
    return json.loads(b.decode('utf-8-sig'))


REL = 'explore/W9b/ready63rel/out/RESULT.json'
K154 = 'explore/W9b/154/out/RESULT.json'
ROSTER = 'explore/X1/continuous0910/154/P34-FROZEN-ROSTER.json'
R81 = 'explore/X3/evening-20261020/81-ready63/RESULT.json'
M180 = 'explore/X1/round1530/180/METRICS.json'
Q1 = 'pair/aimo/evidence/w9-019/q1-resolution.json'
rel, k154, roster, r81, m180, q1 = (load(x) for x in (REL, K154, ROSTER, R81, M180, Q1))
v, raw = {}, {}


def put(k, val, src, ptr):
    assert k not in v, k
    v[k] = val; raw[k] = src + ' :: ' + ptr


# W4: repeat rates over binary waves only, and how many original-waves are not binary.
per = rel['S4']['per_original']
for tag, key in (('NR', 'nr'), ('R', 'r')):
    same = sum(r['counts'].get(tag, 0) for r in per.values() if r['tag81'] == tag)
    binary = sum(r['counts'].get('NR', 0) + r['counts'].get('R', 0) for r in per.values() if r['tag81'] == tag)
    put(f'rel_bin_{key}_repeat_pct', round(100 * same / binary, 1), REL, f'100 x sum counts/{tag} / sum (counts/NR + counts/R) over /S4/per_original with tag81 {tag}, 1 dp')
cells = sum(sum(r['counts'].values()) for r in per.values())
nonbin = sum(sum(n for t, n in r['counts'].items() if t not in ('NR', 'R')) for r in per.values())
put('rel_cells', cells, REL, 'sum of all /S4/per_original/*/counts')
put('rel_nonbinary_cells', nonbin, REL, 'sum of /S4/per_original/*/counts outside NR and R')
# W5: binary rows per wave; W2: how many waves show a loss.
e = rel['endpoints']['strict_n4']
wb, wn = e['per_wave_binary'], e['per_wave_NR']
put('rel_wave_binary_med', statistics.median(wb), REL, 'median /endpoints/strict_n4/per_wave_binary')
put('rel_wave_binary_range', [min(wb), max(wb)], REL, 'min, max /endpoints/strict_n4/per_wave_binary')
put('rel_wave_nr_med', statistics.median(wn), REL, 'median /endpoints/strict_n4/per_wave_NR')
put('rel_wave_losses', sum(g < 0 for g in e['per_wave_primary_gain']), REL, 'count of /endpoints/strict_n4/per_wave_primary_gain < 0')
# W6: X3-81 template-level interval for the gain.
put('f81_gain_tci', [round(x, 3) for x in r81['endpoints']['strict_n4']['bootstrap']['template']['interval95']['interaction-A4']['AUCgain']],
    R81, '/endpoints/strict_n4/bootstrap/template/interval95/interaction-A4/AUCgain, 3 dp')
# W1: X1-154 sampling by prior tag, and the inverse-probability-weighted flip share among both-binary originals.
st = roster['strata']
put('k154_incl_nr', round(st['NR']['inclusion_probability'], 2), ROSTER, '/strata/NR/inclusion_probability, 2 dp')
put('k154_incl_r', round(st['R']['inclusion_probability'], 2), ROSTER, '/strata/R/inclusion_probability, 2 dp')
ab = k154['A_by_B']
w = {t: st[t]['inverse_probability_weight'] for t in ('NR', 'R')}
flip_w = ab['NR->R'] * w['NR'] + ab['R->NR'] * w['R']
all_w = (ab['NR->R'] + ab['NR->NR']) * w['NR'] + (ab['R->R'] + ab['R->NR']) * w['R']
both = ab['NR->R'] + ab['NR->NR'] + ab['R->R'] + ab['R->NR']
put('k154_prior_nr_both', ab['NR->R'] + ab['NR->NR'], K154, '/A_by_B/NR->R + /A_by_B/NR->NR')
put('k154_flip_share', round((ab['NR->R'] + ab['R->NR']) / both, 2), K154, 'flips / both-binary from /A_by_B, 2 dp')
put('k154_ipw_flip_share', round(flip_w / all_w, 2), K154 + ' + ' + ROSTER, '/A_by_B weighted by /strata/*/inverse_probability_weight of the prior tag, 2 dp')
# W12: X1-180 power when the two worlds sit 0.01 (not 0.001) from the threshold, same design.
row = [r for r in m180 if r['world'] == 'boundary' and r['N'] == 716 and r['draws'] == 4 and r['epsilon'] == 0.01]
row1 = [r for r in m180 if r['world'] == 'boundary' and r['N'] == 716 and r['draws'] == 4 and r['epsilon'] == 0.001]
assert len(row) == len(row1) == 1
put('e180_eps', 0.001, M180, 'epsilon of the boundary row (N 716, draws 4) whose NP_power the draft reports as e180_power')
put('e180_power_01', round(row[0]['NP_power'], 2), M180, 'boundary, N 716, draws 4, epsilon 0.01: /NP_power, 2 dp')
assert abs(row1[0]['NP_power'] - 0.0809) < 1e-3
# W7: what the S1 variance split rests on.
va, sa = q1['variance']['dev_all_models'], q1['sibling_agreement']['dev_all_models']
put('q1_rows', va['n'], Q1, '/variance/dev_all_models/n')
put('q1_problems', va['levels_problem'], Q1, '/variance/dev_all_models/levels_problem')
put('q1_sibling_groups', sa['groups'], Q1, '/sibling_agreement/dev_all_models/groups')
put('q1_adj_r2_problem', round(va['adj_r2_problem_only'], 2), Q1, '/variance/dev_all_models/adj_r2_problem_only, 2 dp')

# Checks against M1b's independent re-derivation (VERIFY-v7.6-M1b.md).
assert (v['rel_bin_nr_repeat_pct'], v['rel_bin_r_repeat_pct'], v['rel_cells'], v['rel_nonbinary_cells']) == (46.8, 77.3, 3400, 1155)
assert (v['rel_wave_binary_med'], v['rel_wave_binary_range'], v['rel_wave_nr_med'], v['rel_wave_losses']) == (22, [18, 30], 7, 42)
assert v['f81_gain_tci'] == [-0.197, 0.523]
assert (v['k154_incl_nr'], v['k154_incl_r'], v['k154_prior_nr_both'], v['k154_flip_share'], v['k154_ipw_flip_share']) == (0.54, 0.21, 6, 0.45, 0.35)
assert v['e180_power_01'] == 0.79
assert (v['q1_rows'], v['q1_problems'], v['q1_sibling_groups'], v['q1_adj_r2_problem']) == (53, 18, 11, 0.85)

out = dict(tier='Exploratory; W9b t043 producer (values for the M1b wording fixes to draft v7.6)', values=v, raw_pointers=raw,
           checks=dict(rule='values read or computed from sha-pinned raw files as stated; asserted against M1b re-derivations'),
           _manifest=manifest, producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (Path(__file__).resolve().parent / 'w9b-t043.json').open('x', encoding='utf-8') as f:
    json.dump(out, f, indent=1)
print(len(v), 'values from', len(manifest), 'files')
print(json.dumps(v))
