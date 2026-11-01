"""W9c numbers (t093) for report v1.0: THINKREP, scored once under THINKREP-SPEC-20261024-r2 (freeze eb403af6).
Stored values only, no new computation. Refuses unless INDEPENDENT-REPLAY.json has all_match true and the blind replay
comparison (explore/W9c/thinkrep-blind/BLIND-COMPARE.json) has all_agree true.
Reads only sha-pinned outputs; writes numbers/w9c-t093.json (exclusive create).
usage: python -I pair/aimo/report/numbers/make_w9c_t093.py
"""
import hashlib, json
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
RES, IND, BL = 'explore/W9b/thinkrep/out/RESULT.json', 'explore/W9b/thinkrep/out/INDEPENDENT-REPLAY.json', 'explore/W9c/thinkrep-blind/BLIND-COMPARE.json'
manifest, src = {}, {}
for rel in (RES, IND, BL):
    p = ROOT / rel; b = p.read_bytes(); manifest[str(p)] = hashlib.sha256(b).hexdigest(); src[rel] = json.loads(b.decode('utf-8-sig'))
r, ind, bl = src[RES], src[IND], src[BL]
assert ind['all_match'] is True, 'independent replay does not match'
assert bl['all_agree'] is True, 'blind replay does not agree'
assert r['freeze_sha256'] == 'eb403af6e019839d4a3fab78bfe8f2a50a41c6e0e9a4e277020137f821a57d4a' and r['dry_run'] is False
assert r['gate_decision'] == 'CONTINUE' and r['engine_cut_at_wave'] is None

op, p1, s1, s2 = r['operational'], r['P1_kappa_O'], r['S1_strict']['kappa'], r['S2_legacy_parser_kappa']
p2, p3, s3 = r['P2_noise_ceiling_O'], r['P3_repeat_gain_O'], r['S3_cross_endpoint']
st = op['status_by_family']
r3 = lambda x: round(x, 3)
v, ptr = {}, {}


def put(key, value, pointer):
    v[key] = value; ptr[key] = pointer


put('tr_waves', len(op['included_waves']), RES + ' :: /operational/included_waves (count)')
put('tr_w19_missing', 408 - op['layout']['present_per_wave'][19], RES + ' :: 408 - /operational/layout/present_per_wave/19')
put('tr_draws', op['draws_in_included_waves'], RES + ' :: /operational/draws_in_included_waves')
put('tr_trunc', sum(op['truncated_by_family'].values()), RES + ' :: sum /operational/truncated_by_family')
put('tr_missing', sum(n for k, n in st.items() if k.endswith('|missing')), RES + ' :: sum /operational/status_by_family/*|missing')
put('tr_abstain', sum(n for k, n in st.items() if k.endswith('|abstain')), RES + ' :: sum /operational/status_by_family/*|abstain')
put('tr_abstain_gs', st.get('surface_gs|abstain', 0), RES + ' :: /operational/status_by_family/surface_gs|abstain')
put('tr_kappa', r3(p1['kappa']), RES + ' :: /P1_kappa_O/kappa; 3 dp')
put('tr_kappa_ci', [r3(x) for x in p1['bootstrap']['ci95']], RES + ' :: /P1_kappa_O/bootstrap/ci95 (preregistered percentile); 3 dp')
put('tr_kappa_n', p1['subjects'], RES + ' :: /P1_kappa_O/subjects')
put('tr_nr_pooled', r3(p1['pooled_NR']), RES + ' :: /P1_kappa_O/pooled_NR; 3 dp')
put('tr_kappa_S', r3(s1['kappa']), RES + ' :: /S1_strict/kappa/kappa; 3 dp')
put('tr_kappa_S_ci', [r3(x) for x in s1['bootstrap']['ci95']], RES + ' :: /S1_strict/kappa/bootstrap/ci95; 3 dp')
put('tr_kappa_L', r3(s2['kappa']), RES + ' :: /S2_legacy_parser_kappa/kappa; 3 dp')
put('tr_kappa_L_ci', [r3(x) for x in s2['bootstrap']['ci95']], RES + ' :: /S2_legacy_parser_kappa/bootstrap/ci95; 3 dp')
put('tr_nr_L', r3(s2['pooled_NR']), RES + ' :: /S2_legacy_parser_kappa/pooled_NR; 3 dp')
put('tr_oracle_loo', r3(p2['oracle_leave_wave_out']['mean']), RES + ' :: /P2_noise_ceiling_O/oracle_leave_wave_out/mean (scorer only; not in either replay); 3 dp')
put('tr_gain', r3(p3['observed']), RES + ' :: /P3_repeat_gain_O/observed; 3 dp')
put('tr_gain_ci', [r3(x) for x in p3['original_bootstrap']['ci95']], RES + ' :: /P3_repeat_gain_O/original_bootstrap/ci95; 3 dp')
put('tr_gain_mde', r3(p3['mde80']), RES + ' :: /P3_repeat_gain_O/mde80; 3 dp')
put('tr_s3_rho', r3(s3['spearman']), RES + ' :: /S3_cross_endpoint/spearman; 3 dp')
put('tr_s3_rho_ci', [r3(x) for x in s3['ci95']], RES + ' :: /S3_cross_endpoint/ci95; 3 dp')
put('tr_s3_n', s3['n'], RES + ' :: /S3_cross_endpoint/n')
put('tr_nrfrac_on', r3(s3['mean_NR_fraction_thinking']), RES + ' :: /S3_cross_endpoint/mean_NR_fraction_thinking; 3 dp')
put('tr_nrfrac_off', r3(s3['mean_NR_fraction_nothink']), RES + ' :: /S3_cross_endpoint/mean_NR_fraction_nothink; 3 dp')

out = HERE / 'w9c-t093.json'
with open(out, 'x', encoding='utf-8') as fh:
    json.dump(dict(tier='Preregistered exploratory (THINKREP r2, scored once 25 Oct); stored values, no new computation; W9c t093 producer for report v1.0.',
                   values=v, raw_pointers=ptr, _manifest=manifest), fh, indent=1, ensure_ascii=False)
print(json.dumps(v), hashlib.sha256(out.read_bytes()).hexdigest())
