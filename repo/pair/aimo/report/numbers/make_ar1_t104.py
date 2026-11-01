"""AR1 numbers (t104) for report v1.1: SHAM Phase 1 (prospective identical-text control, freeze cf704ca3, scored once
on the box 26 Oct 18:21 PT) and the public Small-track leaderboard read (AM1 board_noise.json).
Stored values only, no new computation except two constructed values marked as such (lb_step, p1s_gpu_h).
BLIND REPLAY PENDING: unlike make_w9c_t093.py this producer does not refuse without a replay, because none exists yet
(BR1 stopped on a blindness breach, from-box/research/W9d/sham1-replay-br1/BREACH-BR1.md). The tier says so, and the
report tags every Phase 1 number as pending replay. Re-run nothing here once a replay lands; write a new producer.
Reads only sha-pinned files; writes numbers/ar1-t104.json (exclusive create).
usage: python -I pair/aimo/report/numbers/make_ar1_t104.py
"""
import hashlib, json, re
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
OUT = 'from-box/research/W9d/sham1-score/tree/explore/W9b/sham1/v1.1/out/'
RES, DRW, ONCE = OUT + 'RESULT.json', OUT + 'DRAWS.jsonl', OUT + 'SCORE-ONCE-STARTED.json'
FRZ, SCO = 'explore/W9b/sham1/v1.1/SHAM1-FREEZE-v1.1.sha256', 'explore/W9b/sham1/v1.1/score_phase1.py'
CL = 'planning/gpu-ops/SHAM-PHASE1-FINAL-CL4-20261026.json'
BN = 'explore/AM1-aimo/out/board_noise.json'
manifest, raw = {}, {}
for rel in (RES, DRW, ONCE, FRZ, SCO, CL, BN):
    p = ROOT / rel; b = p.read_bytes(); manifest[str(p)] = hashlib.sha256(b).hexdigest(); raw[rel] = b
r = json.loads(raw[RES].decode('utf-8-sig')); cl = json.loads(raw[CL].decode('utf-8-sig')); bn = json.loads(raw[BN].decode('utf-8-sig'))
once = json.loads(raw[ONCE].decode('utf-8-sig'))
# bindings: result <- frozen scorer and freeze; run complete with no abandoned wave
assert r['freeze_sha256'] == manifest[str(ROOT / FRZ)] == 'cf704ca303b4791351426d97f9be715e7a475644be557e1498e1f11794a94b5b'
assert r['scorer_sha256'] == once['scorer'] == manifest[str(ROOT / SCO)]
assert r['meta']['abandoned'] == [] and r['meta']['scored_waves'] == list(range(12)) and cl['exit']['reason'] == 'complete'
assert cl['freeze_sha256'] == r['freeze_sha256']
n_draws = sum(1 for line in raw[DRW].decode('utf-8').splitlines() if line.strip())
assert n_draws == sum(sum(v.values()) for v in r['status_counts'].values()) == r['originals'] * 5 * r['draws_per_version']

r3 = lambda x: round(x, 3); r2 = lambda x: round(x, 2); r4 = lambda x: round(x, 4)
v, ptr = {}, {}


def put(key, value, pointer):
    assert key not in v; v[key] = value; ptr[key] = pointer


def est(key, node, path, rnd=r3, dp='3 dp'):
    put(key, rnd(node['est']), f'{RES} :: {path}/est; {dp}')
    put(key + '_ci', [rnd(x) for x in node['ci95']], f'{RES} :: {path}/ci95; {dp}')


put('p1s_n', r['originals'], RES + ' :: /originals')
put('p1s_waves', r['waves'], RES + ' :: /waves')
put('p1s_dpv', r['draws_per_version'], RES + ' :: /draws_per_version')
put('p1s_draws', n_draws, DRW + ' :: non-empty lines (= sum /status_counts = originals x 5 x draws_per_version)')
put('p1s_tokens', cl['exit']['charged_tokens'], CL + ' :: /exit/charged_tokens')
put('p1s_gpu_h', round(cl['exit']['charged_seconds'] / 3600, 1), CL + ' :: constructed: /exit/charged_seconds / 3600; 1 dp')
est('p1s_primary', r['PRIMARY_solve_vs_sham'], '/PRIMARY_solve_vs_sham')
put('p1s_reading', r['PRIMARY_reading'], RES + ' :: /PRIMARY_reading')
est('p1s_cal1', r['CAL1_base_minus_sham'], '/CAL1_base_minus_sham', r4, '4 dp')
put('p1s_cal2_tests', r['CAL2_sham_z']['tests'], RES + ' :: /CAL2_sham_z/tests')
put('p1s_cal2_share', r3(r['CAL2_sham_z']['share_abs_z_gt_1_96']), RES + ' :: /CAL2_sham_z/share_abs_z_gt_1_96; 3 dp')
put('p1s_cal2_reading', r['CAL2_sham_z']['reading'], RES + ' :: /CAL2_sham_z/reading')
est('p1s_S', r['S_solve_vs_base'], '/S_solve_vs_base')
put('p1s_tau', r3(r['S_tau']), RES + ' :: /S_tau; 3 dp')
for t, node in (('t1', 'T1_joint'), ('t2', 'T2_own'), ('t3', 'T3_own_spec_rule')):
    T = r[node]
    put(f'p1s_{t}_n', T['n'], f'{RES} :: /{node}/n')
    est(f'p1s_{t}_real', T['real'], f'/{node}/real')
    est(f'p1s_{t}_sham', T['sham'], f'/{node}/sham')
    est(f'p1s_{t}_delta', T['delta'], f'/{node}/delta')
    est(f'p1s_{t}_ratio', T['ratio_sham_over_real'], f'/{node}/ratio_sham_over_real', r2, '2 dp')
    assert T['ratio_sham_over_real']['undefined_resamples'] == 0
est('p1s_t4', {'est': r['T4_sham_minus_N0']['est'], 'ci95': r['T4_sham_minus_N0']['ci95']}, '/T4_sham_minus_N0', r4, '4 dp')
put('p1s_t4_n', r['T4_sham_minus_N0']['n'], RES + ' :: /T4_sham_minus_N0/n')
put('p1s_t4_reading', r['T4_reading'], RES + ' :: /T4_reading')
put('p1s_elig_pct', round(100 * r['E_eligible_T1']['share'], 1), RES + ' :: 100 x /E_eligible_T1/share; 1 dp')
est('p1s_solve_elig', r['E_solve_by_T1']['eligible'], '/E_solve_by_T1/eligible')
est('p1s_solve_inelig', r['E_solve_by_T1']['ineligible'], '/E_solve_by_T1/ineligible')
put('p1s_inelig_n', r['E_solve_by_T1']['ineligible']['n'], RES + ' :: /E_solve_by_T1/ineligible/n')
est('p1s_solve_unus', r['S1_solve_by_fresh6h']['UNUSABLE'], '/S1_solve_by_fresh6h/UNUSABLE')
put('p1s_unus_n', r['S1_solve_by_fresh6h']['UNUSABLE']['n'], RES + ' :: /S1_solve_by_fresh6h/UNUSABLE/n')
est('p1s_solve_rest', r['S1_solve_by_fresh6h']['binary_or_floor'], '/S1_solve_by_fresh6h/binary_or_floor')
for ver in ('base', 'surface_gs', 'surface_dlm', 'sham_a', 'sham_b'):
    put('p1s_abst_' + ver, r['status_counts'][ver].get('abstain', 0), f'{RES} :: /status_counts/{ver}/abstain')

b = bn['board']
put('lb_teams', b['small_teams'], BN + ' :: /board/small_teams')
put('lb_cases', b['small_n_cases'], BN + ' :: /board/small_n_cases')
put('lb_perfect', b['small_perfect'], BN + ' :: /board/small_perfect')
put('lb_step', round(100 / b['small_n_cases'], 1), BN + ' :: constructed: 100 / /board/small_n_cases (points per case); 1 dp')
base_keys = [k for k in b if k.startswith('small_at_or_below_baseline_')]
assert len(base_keys) == 1
put('lb_baseline', float(re.fullmatch(r'small_at_or_below_baseline_([\d.]+)', base_keys[0])[1]),
    BN + ' :: the Small baseline as recorded in the key name /board/' + base_keys[0] + '; 2 dp')
put('lb_at_or_below', b[base_keys[0]], BN + ' :: /board/' + base_keys[0])
put('lb_read_utc', b['last_updated_at'][:16].replace('T', ' '), BN + ' :: /board/last_updated_at (minute)')
put('lb_range70', bn['score_range_95_n14']['0.7'], BN + ' :: /score_range_95_n14/0.7 (95% range of a true-0.70 method on 14 cases); 3 dp')
put('lb_outrank', r2(bn['outrank_n14']['0.7_vs_0.6']['strictly_above']), BN + ' :: /outrank_n14/0.7_vs_0.6/strictly_above; 2 dp')
put('lb_tie', r2(bn['outrank_n14']['0.7_vs_0.6']['tie']), BN + ' :: /outrank_n14/0.7_vs_0.6/tie; 2 dp')
put('lb_perfect_065_10', r2(bn['expected_teams_at_100pct_of_95']['p0.65_m10']), BN + ' :: /expected_teams_at_100pct_of_95/p0.65_m10; 2 dp')

out = HERE / 'ar1-t104.json'
with open(out, 'x', encoding='utf-8') as fh:
    json.dump(dict(tier='SHAM Phase 1: preregistered exploratory (freeze cf704ca3), scored once on the box 26 Oct; BLIND REPLAY PENDING. '
                        'Leaderboard: AM1 board read and simulation. Stored values; AR1 t104 producer for report v1.1.',
                   values=v, raw_pointers=ptr, _manifest=manifest), fh, indent=1, ensure_ascii=False)
print(json.dumps(v), hashlib.sha256(out.read_bytes()).hexdigest())
