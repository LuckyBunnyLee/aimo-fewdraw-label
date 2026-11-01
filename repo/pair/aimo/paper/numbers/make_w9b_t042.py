"""W9b numbers (t042) for draft v7.6: label reliability. Values are read from the two raw result files,
explore/W9b/ready63rel/out/RESULT.json (100 repeat waves on the 34 READY63 originals scored in X3-81) and
explore/W9b/154/out/RESULT.json (X1-154 independent second wave), plus the X3-81 tag file that the READY63 scorer
hash-bound (template families only). Derived values (counts, rates, medians) are computed here from those fields and
rounded as stated in raw_pointers. Every file is sha-pinned. Writes numbers/w9b-t042.json (exclusive create).
usage: python -I pair/aimo/paper/numbers/make_w9b_t042.py
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


REL, K154, TAGS81 = 'explore/W9b/ready63rel/out/RESULT.json', 'explore/W9b/154/out/RESULT.json', 'explore/X3/evening-20261020/81-ready63/strict_n4-ALL-ORIGINALS.json'
rel, k154, tags81 = load(REL), load(K154), load(TAGS81)
assert rel['bound_sha256'][str(ROOT / TAGS81).replace('/', '\\')] == manifest[str(ROOT / TAGS81)]
v, raw = {}, {}


def put(k, val, src, ptr):
    assert k not in v, k
    v[k] = val; raw[k] = src + ' :: ' + ptr


# --- READY63 reliability repeats ---
op, pr, pl, s4 = rel['operational'], rel['primary'], rel['placement_of_81'], rel['S4']
per = s4['per_original']
fams = sorted({k.split('|')[0] for k in op['status_by_family']})
put('rel_originals', len(per), REL, 'len(/S4/per_original)')
templates = {r['template'] for r in tags81 if r['pid'] in per}
assert {r['pid'] for r in tags81} >= set(per)
put('rel_templates', len(templates), TAGS81, 'distinct /*/template over the pids in /S4/per_original of ' + REL)
put('rel_requests', op['attempts'], REL, '/operational/attempts')
put('rel_binding_fail', op['binding_failures'], REL, '/operational/binding_failures')
put('rel_families', len(fams), REL, 'distinct family prefixes of /operational/status_by_family')
per_cell = op['attempts'] / (len(per) * len(fams)); assert per_cell == int(per_cell)
put('rel_per_cell', int(per_cell), REL, '/operational/attempts / (originals x families)')
put('rel_waves', pr['defined_waves'], REL, '/primary/defined_waves')
put('rel_trunc', op['truncated'], REL, '/operational/truncated')
put('rel_trunc_pct', round(100 * op['truncated'] / op['attempts'], 1), REL, '100 x /operational/truncated / /operational/attempts, 1 dp')
put('rel_gain', round(pr['observed'], 3), REL, '/primary/observed, 3 dp')
put('rel_gain_ci', [round(x, 3) for x in pr['original_bootstrap']['ci95']], REL, '/primary/original_bootstrap/ci95, 3 dp')
put('rel_gain_tci', [round(x, 3) for x in pr['template_bootstrap']['ci95']], REL, '/primary/template_bootstrap/ci95, 3 dp')
assert pr['original_bootstrap']['valid'] == pr['template_bootstrap']['valid']
put('rel_boot', pr['original_bootstrap']['valid'], REL, '/primary/original_bootstrap/valid')
e = rel['endpoints']['strict_n4']['observed']
put('rel_auc_a4', round(e['interaction-A4']['mean_AUC'], 3), REL, '/endpoints/strict_n4/observed/interaction-A4/mean_AUC, 3 dp')
put('rel_auc_pointk', round(e['point-K']['mean_AUC'], 3), REL, '/endpoints/strict_n4/observed/point-K/mean_AUC, 3 dp')
n2 = rel['endpoints']['hashed_n2B']
put('rel_n2b_gain', round(n2['observed']['interaction-A4']['mean_AUC_gain'], 3), REL, '/endpoints/hashed_n2B/observed/interaction-A4/mean_AUC_gain, 3 dp')
put('rel_n2b_gain_ci', [round(x, 3) for x in n2['bootstrap']['original']['interaction-A4']['mean_AUC_gain']['ci95']], REL, '/endpoints/hashed_n2B/bootstrap/original/interaction-A4/mean_AUC_gain/ci95, 3 dp')
put('rel_wave_min', round(pl['min'], 3), REL, '/placement_of_81/min, 3 dp')
put('rel_wave_max', round(pl['max'], 3), REL, '/placement_of_81/max, 3 dp')
put('rel_wave_median', round(pl['median'], 3), REL, '/placement_of_81/median, 3 dp')
below = pl['frac_below'] * pl['defined']; assert abs(below - round(below)) < 1e-9
put('rel_81_below', int(round(below)), REL, '/placement_of_81/frac_below x /placement_of_81/defined')
put('rel_gain81', round(pl['gain81'], 3), REL, '/placement_of_81/gain81, 3 dp')
kap = s4['fleiss_kappa_NR_R']
put('rel_kappa', round(kap['kappa'], 3), REL, '/S4/fleiss_kappa_NR_R/kappa, 3 dp')
put('rel_kappa_n', kap['subjects'], REL, '/S4/fleiss_kappa_NR_R/subjects')
put('rel_pooled_nr', round(kap['pooled_NR'], 2), REL, '/S4/fleiss_kappa_NR_R/pooled_NR, 2 dp')
ag = s4['agreement_by_81_class']
put('rel_agree_nr_pct', round(100 * ag['NR'], 1), REL, '100 x /S4/agreement_by_81_class/NR, 1 dp')
put('rel_agree_r_pct', round(100 * ag['R'], 1), REL, '100 x /S4/agreement_by_81_class/R, 1 dp')
put('rel_agree_all_pct', round(100 * s4['agreement_with_81_all_tags'], 1), REL, '100 x /S4/agreement_with_81_all_tags, 1 dp')
plotted = [r for r in per.values() if r.get('binary_waves', 0) > 0]
put('rel_plotted', len(plotted), REL, 'count of /S4/per_original with binary_waves >= 1')
put('rel_no_binary', len(op['originals_with_no_binary_wave']), REL, 'len(/operational/originals_with_no_binary_wave)')
assert len(plotted) + len(op['originals_with_no_binary_wave']) == len(per)
for tag, key in (('NR', 'nr'), ('R', 'r')):
    f = [r['NR_fraction'] for r in plotted if r['tag81'] == tag]
    put(f'rel_{key}81_n', len(f), REL, f'count of /S4/per_original with tag81 {tag} and binary_waves >= 1')
    put(f'rel_{key}81_med', round(statistics.median(f), 2), REL, f'median /S4/per_original/*/NR_fraction over tag81 {tag}, 2 dp')
    put(f'rel_{key}81_range', [round(min(f), 2), round(max(f), 2)], REL, f'min and max /S4/per_original/*/NR_fraction over tag81 {tag}, 2 dp')

# --- X1-154 independent second wave ---
ab, rec = k154['A_by_B'], k154['records']
put('k154_originals', sum(ab.values()), K154, 'sum of /A_by_B')
put('k154_records', rec['published'], K154, '/records/published')
put('k154_binding_fail', rec['binding_failures'], K154, '/records/binding_failures')
put('k154_trunc_pct', round(100 * rec['truncated'] / rec['published'], 1), K154, '100 x /records/truncated / /records/published, 1 dp')
both = {k: ab.get(k, 0) for k in ('NR->NR', 'NR->R', 'R->NR', 'R->R')}
put('k154_both_binary', sum(both.values()), K154, 'sum of /A_by_B over NR/R -> NR/R')
put('k154_flips', both['NR->R'] + both['R->NR'], K154, '/A_by_B/NR->R + /A_by_B/R->NR')
put('k154_nr_r', both['NR->R'], K154, '/A_by_B/NR->R')
put('k154_r_nr', both['R->NR'], K154, '/A_by_B/R->NR')
put('k154_nr_nr', both['NR->NR'], K154, '/A_by_B/NR->NR')
put('k154_r_r', both['R->R'], K154, '/A_by_B/R->R')
put('k154_b_nr', k154['B_tags']['NR'], K154, '/B_tags/NR')

# Consistency checks against the section's stated values and the X3-81 producer.
t041 = json.loads((Path(__file__).resolve().parent / 'w9b-t041.json').read_text(encoding='utf-8'))['values']
assert abs(pl['gain81'] - t041['f81_gain']) < 1e-12 and v['rel_originals'] == t041['f81_originals'] == 34
assert (v['rel_templates'], v['rel_requests'], v['rel_per_cell'], v['rel_waves'], v['rel_binding_fail']) == (25, 40800, 400, 100, 0)
assert v['rel_gain_ci'][0] < 0 < v['rel_gain_ci'][1] and v['rel_gain_tci'][0] < 0 < v['rel_gain_tci'][1]
assert (v['rel_kappa'], v['rel_81_below'], v['rel_plotted']) == (0.138, 62, 32)
assert (v['k154_originals'], v['k154_records'], v['k154_both_binary'], v['k154_flips']) == (31, 372, 11, 5)

out = dict(tier='Exploratory; W9b t042 producer (21 Oct label reliability: READY63 repeat waves and X1-154 second wave)', values=v, raw_pointers=raw,
           checks=dict(rule='values read from sha-pinned RESULT.json fields; derived values computed as stated; rounding stated per key'),
           _manifest=manifest, producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (Path(__file__).resolve().parent / 'w9b-t042.json').open('x', encoding='utf-8') as f:
    json.dump(out, f, indent=1)
print(len(v), 'values from', len(manifest), 'files')
print(json.dumps(v))
