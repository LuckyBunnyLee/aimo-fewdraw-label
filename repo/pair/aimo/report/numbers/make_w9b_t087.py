"""W9b numbers (t087) for report draft v0.8: the R7 referee's must-fixes. Nothing is re-run or rescored; values are read or counted from sha-pinned outputs:
- explore/W9b/decomp/SHAM-JOINT-RESULT.json (joint-eligibility sham sensitivity, wave-order drift, second-wave AUC with the undefined-N0 problem excluded;
  EXP-w9b-sham-joint, run once)
- explore/W9b/decomp/RESULT.json (template-family intervals; per-problem solve rates for the worked example)
- explore/W9b/ready63rel/out/DRAWS.jsonl (binary even waves of the three most-harmed problems, frozen fresh81_pure.tag; no regrading)
- explore/R7/NUMBER-CHECKS.json (the second blind referee's recomputation)
Writes numbers/w9b-t087.json (exclusive create). No models, GPU, network or sealed data.
usage: python -I pair/aimo/report/numbers/make_w9b_t087.py
"""
import collections, hashlib, json, sys
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
JT, DC, DR, R7 = 'explore/W9b/decomp/SHAM-JOINT-RESULT.json', 'explore/W9b/decomp/RESULT.json', 'explore/W9b/ready63rel/out/DRAWS.jsonl', 'explore/R7/NUMBER-CHECKS.json'
FP = 'explore/X3/fresh81_pure.py'
PIN = {JT: '2fe5c50452fd09b53867118dc7e9b023c52da701a79a7c57f441c9549c70f9b3',
       DC: 'f70423eb7b03d70ac5252fdaee8464705b802cd0a3dc8b3d66127d3bb12ace0f',
       DR: 'e4c66547ecc6ac1aacc9a6921b5611f3e9e183eec7aab6b90e55cf49edaa01b3',
       R7: '42f40cb14fa6a10b046ea3b8f660c7802f9944d1735718d0454997d3c9df7b20',
       FP: '6b9c0e124f4d690c6bd1412aeccfdc8d12b8b20fb2ebe3d0576656c0b59f1e4d'}
manifest = {}


def raw(rel):
    p = ROOT / rel; b = p.read_bytes(); h = hashlib.sha256(b).hexdigest()
    assert h == PIN[rel], rel + ' changed'
    manifest[str(p)] = h
    return b


jt, dc, r7 = (json.loads(raw(x).decode('utf-8-sig')) for x in (JT, DC, R7))
draws = [json.loads(l) for l in raw(DR).decode('utf-8').splitlines()]
raw(FP); sys.path.insert(0, str(ROOT / 'explore/X3')); import fresh81_pure as f
v, ptr = {}, {}


def put(k, val, pointer, src):
    assert k not in v, k
    v[k] = val; ptr[k] = src + ' :: ' + pointer


r3 = lambda x: round(x, 3)
ci = lambda node, nd=3: [round(a, nd) for a in node['ci95']]

# ---- joint-eligibility sham sensitivity ----
j = jt['joint']
put('jt_n_used', j['n_used'], '/joint/n_used (of the 29 Phase 0 problems, >= 5 jointly binary triples)', JT)
put('jt_triples', j['n_joint_triples'], '/joint/n_joint_triples', JT)
nj = [r['n_joint'] for r in j['per_original']]
put('jt_per_min', min(nj), '/joint/per_original/n_joint: min', JT); put('jt_per_max', max(nj), '/joint/per_original/n_joint: max', JT)
put('jt_templates', j['n_templates_used'], '/joint/n_templates_used', JT)
for k, node in (('real', 'real'), ('sham', 'sham'), ('delta', 'real_minus_sham')):
    put('jt_' + k, r3(j[node]['est']), f'/joint/{node}/est; 3 dp', JT)
    put('jt_' + k + '_ci', ci(j[node]['ci_original']), f'/joint/{node}/ci_original/ci95; 3 dp', JT)
put('jt_delta_ci_t', ci(j['real_minus_sham']['ci_template']), '/joint/real_minus_sham/ci_template/ci95; 3 dp', JT)
put('jt_ratio', round(j['ratio_sham_over_real']['est'], 2), '/joint/ratio_sham_over_real/est; 2 dp', JT)
put('jt_ratio_ci', ci(j['ratio_sham_over_real']['ci_original'], 2), '/joint/ratio_sham_over_real/ci_original/ci95; 2 dp', JT)
st = j['state_table']; B2 = ('NR', 'R')
assert sum(st.values()) == j['n_triples_all'] == 957
both = sum(st[f'{a}|{b}'] for a in B2 for b in B2); assert both == j['n_joint_triples']
put('jt_both_bin', both, '/joint/state_table: real binary and sham binary', JT)
put('jt_real_only', sum(st[f'{a}|{b}'] for a in B2 for b in ('UNUSABLE', 'FLOOR')), '/joint/state_table: real binary, sham not', JT)
put('jt_sham_only', sum(st[f'{a}|{b}'] for a in ('UNUSABLE', 'FLOOR') for b in B2), '/joint/state_table: sham binary, real not', JT)
put('jt_neither', sum(st[f'{a}|{b}'] for a in ('UNUSABLE', 'FLOOR') for b in ('UNUSABLE', 'FLOOR')), '/joint/state_table: neither binary', JT)
for a in B2:
    for b in B2: put(f'jt_x_{a.lower()}_{b.lower()}', st[f'{a}|{b}'], f'/joint/state_table/{a}|{b}', JT)
put('jt_real_unus_sham_bin', st['UNUSABLE|NR'] + st['UNUSABLE|R'], '/joint/state_table: real UNUSABLE, sham binary', JT)

# ---- wave-order drift ----
o = jt['order']; assert o['wave_major'] and o['per_wave_requests'] == [408]
put('ord_per_wave', 408, '/order/per_wave_requests (wave-major queue order verified)', JT)
d = jt['drift']
put('dr_solve', r3(d['base_solve_late_minus_early']['est']), '/drift/base_solve_late_minus_early/est; 3 dp', JT)
put('dr_solve_ci', ci(d['base_solve_late_minus_early']['ci_original']), '/drift/base_solve_late_minus_early/ci_original/ci95; 3 dp', JT)
put('dr_num', r3(d['base_numeric_late_minus_early']['est']), '/drift/base_numeric_late_minus_early/est; 3 dp', JT)
put('dr_num_ci', ci(d['base_numeric_late_minus_early']['ci_original']), '/drift/base_numeric_late_minus_early/ci_original/ci95; 3 dp', JT)
sd = j['sham_drift_late_minus_early']
put('dr_sham', r3(sd['est']), '/joint/sham_drift_late_minus_early/est; 3 dp', JT)
put('dr_sham_ci', ci(sd['ci_original'], 2), '/joint/sham_drift_late_minus_early/ci_original/ci95; 2 dp', JT)

# ---- second-wave AUC: the undefined base-only N0 ----
s = jt['s1']
put('s1_undef', s['n_undefined'], '/s1/n_undefined (base 0 of 4 correct)', JT)
assert s['undefined_y'] == [0]
put('s1_undef_tag', 'robust', '/s1/undefined_y == [0]: its fresh-test tag was robust', JT)
put('s1_auc_base_excl', r3(s['auc_base_excl']), '/s1/auc_base_excl; 3 dp', JT)
put('s1_auc_base_excl_ci', ci(s['auc_base_excl_ci']), '/s1/auc_base_excl_ci/ci95; 3 dp', JT)
put('s1_auc_pool_excl', r3(s['auc_pool_excl']), '/s1/auc_pool_excl; 3 dp', JT)
put('s1_auc_base_s0', r3(s['auc_base_scored0']), '/s1/auc_base_scored0 (undefined scored 0.0); 3 dp', JT)
put('tmpl_used29', jt['n_templates_used29'], '/n_templates_used29', JT)

# ---- template-family intervals (DECOMP) ----
for k, path in (('E_base', ('B1', 'E_base')), ('E_pool', ('B1', 'E_pool')), ('null', ('B4', 'null_at_base')), ('edit', ('B4', 'edit_component')), ('resid', ('B4', 'residual'))):
    put(f'dc_{k}_ci_t', ci(dc[path[0]][path[1]]['ci_template']), f'/{path[0]}/{path[1]}/ci_template/ci95; 3 dp', DC)
put('dc_delta_solve_ci_t', ci(dc['D']['D1']['solve']['ci_template']), '/D/D1/solve/ci_template/ci95; 3 dp', DC)

# ---- the three most-harmed problems: worked example and binary even waves ----
per = dc['D']['D1']['solve']['per_original']
top = sorted(per, key=lambda r: -r['delta_edit'])[:3]
put('ex_top_pb', round(top[0]['p_b'], 2), '/D/D1/solve/per_original[largest delta_edit]/p_b; 2 dp', DC)
put('ex_top_pg', round(top[0]['p_g'], 2), '/D/D1/solve/per_original[largest delta_edit]/p_g; 2 dp', DC)
put('ex_top_pd', round(top[0]['p_d'], 2), '/D/D1/solve/per_original[largest delta_edit]/p_d; 2 dp', DC)
by = collections.defaultdict(list)
for x in draws: by[(x['pid'], (x['replicate'] - 1000) // 4, x['family'])].append(x)
cell = lambda ds: [dict(status=x['status'], correct=x['correct'] or 0) for x in sorted(ds, key=lambda x: x['replicate'])]
nb = []
for r in top:
    tags = [f.tag({fm: cell(by[(r['pid'], w, fm)]) for fm in ('base', 'surface_gs', 'surface_dlm')}, 4) for w in range(0, 100, 2)]
    nb.append(sum(t in ('NR', 'R') for t in tags))
put('top3_even_bin', nb, 'DRAWS: binary even waves (0, 2, ..., 98) of the three largest delta_edit problems, in that order; frozen tag', DR)

# ---- blind referee R7 recomputation ----
put('r7_checks', len(r7['checks']), '/checks: count', R7)
put('r7_match', sum(c['status'] == 'MATCH' for c in r7['checks']), '/checks: status MATCH', R7)
put('r7_indep', sum(c['basis'] != 'pinned corrected per-problem outputs; bootstrap not rerun' for c in r7['checks']), '/checks: basis independent (draws or formula)', R7)

out = HERE / 'w9b-t087.json'
with open(out, 'x', encoding='utf-8') as fh:
    json.dump(dict(tier='Exploratory; counts and fields read from sha-pinned outputs, including the post hoc joint-eligibility sensitivity '
                        '(EXP-w9b-sham-joint, run once); W9b t087 producer for report v0.8.',
                   values=v, raw_pointers=ptr, _manifest=manifest), fh, indent=1, ensure_ascii=False)
print(len(v), 'keys ->', out, hashlib.sha256(out.read_bytes()).hexdigest())
for k, x in v.items(): print(k, x)
