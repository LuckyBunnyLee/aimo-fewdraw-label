"""AR2 numbers (t107) for report v1.3: the RANDOM100 r5 frozen score-once (BX2, 27 Oct), Appendix H.
Gate (tasks/NOTE-AR1-from-AM1-AIMO-v1.1-INPUTS-20261027.md): no RANDOM100 number enters the report before a fresh blind
replay matches and the blindness audit passes. The lead verified on 27 Oct that the BR3 blind replay matched exactly
(explore/AR2-BRIEF.md item 2). Stored values only; the one derived value is the tag count sum over per-original rows.
- RESULT.json must hash to the value in the score's DONE.json and SCORE-COMPLETION.json, and carry the r5 freeze sha 28d7b0cf.
- Never pooled with SHAM (separate keys, separate paragraph).
Writes numbers/ar2-t107.json (exclusive create). usage: python -I pair/aimo/report/numbers/make_ar2_t107.py
"""
import collections, hashlib, json
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
J = 'from-box/research/AM1/random100-score/'
RES, DONE, SC = J + 'out/RESULT.json', J + 'DONE.json', J + 'SCORE-COMPLETION.json'
FRZ = 'from-box/research/W9d/random100-freeze-r5/pack/FREEZE.sha256'
manifest, raw = {}, {}
for rel in (RES, DONE, SC, FRZ):
    p = ROOT / rel; b = p.read_bytes(); manifest[str(p)] = hashlib.sha256(b).hexdigest(); raw[rel] = b
r = json.loads(raw[RES].decode('utf-8-sig')); done = json.loads(raw[DONE].decode('utf-8-sig')); sc = json.loads(raw[SC].decode('utf-8-sig'))
h = manifest[str(ROOT / RES)]
assert h == done['outputs_sha256']['out/RESULT.json'] == sc['outputs']['out/RESULT.json'] and done['exit_code'] == 0 == sc['exit_code']
assert r['freeze_sha256'] == manifest[str(ROOT / FRZ)] == done['script_sha256']['FREEZE.sha256'] and r['freeze_sha256'].startswith('28d7b0cf')
assert r['state']['abandoned'] == [] and r['state']['unsealed'] == [] and r['waves'] == len(r['state']['complete']) and r['originals'] == len(r['per_original'])

v, ptr = {}, {}


def put(key, value, pointer):
    assert key not in v; v[key] = value; ptr[key] = pointer


r4 = lambda x: round(x, 4); r3 = lambda x: round(x, 3); r2 = lambda x: round(x, 2)
put('r100_primary', r4(r['primary']['est']), RES + ' :: /primary/est (base minus mean rewrite, all answers); 4 dp')
put('r100_primary_ci', [r4(x) for x in r['primary']['ci95']], RES + ' :: /primary/ci95; 4 dp')
put('r100_reading', r['reading'], RES + ' :: /reading')
put('r100_elig', r['reliability']['eligible'], RES + ' :: /reliability/eligible (>= 5 binary waves)')
put('r100_elig_loss', r4(r['by_eligibility']['True']['est']), RES + ' :: /by_eligibility/True/est; 4 dp')
put('r100_elig_loss_ci', [r4(x) for x in r['by_eligibility']['True']['ci95']], RES + ' :: /by_eligibility/True/ci95; 4 dp')
put('r100_inelig_loss', r4(r['by_eligibility']['False']['est']), RES + ' :: /by_eligibility/False/est; 4 dp')
put('r100_inelig_loss_ci', [r4(x) for x in r['by_eligibility']['False']['ci95']], RES + ' :: /by_eligibility/False/ci95; 4 dp')
assert r['reliability']['defined_resamples'] == r['reliability']['planned_resamples']
put('r100_kappa', r3(r['reliability']['est']), RES + ' :: /reliability/est (Fleiss kappa, eligible problems); 3 dp')
put('r100_kappa_ci', [r2(x) for x in r['reliability']['ci95']], RES + ' :: /reliability/ci95; 2 dp')
put('r100_half', r4(r['half_change']['est']), RES + ' :: /half_change/est (second-half minus first-half loss); 4 dp')
put('r100_half_ci', [r4(x) for x in r['half_change']['ci95']], RES + ' :: /half_change/ci95; 4 dp')
tags = collections.Counter()
for row in r['per_original']: tags.update(row['tags'])
assert sum(tags.values()) == r['waves'] * r['originals']
for t, k in (('R', 'r'), ('NR', 'nr'), ('FLOOR', 'floor'), ('UNUSABLE', 'unus')):
    put('r100_tag_' + k, tags[t], RES + f' :: sum over /per_original/*/tags/{t}')
put('r100_tag_total', sum(tags.values()), RES + ' :: sum over /per_original/*/tags (original-waves)')
for fam, k in (('base', 'base'), ('surface_gs', 'gs'), ('surface_dlm', 'dlm')):
    put('r100_abst_' + k, r['status'][fam]['abstain'], RES + f' :: /status/{fam}/abstain')

out = HERE / 'ar2-t107.json'
with open(out, 'x', encoding='utf-8') as fh:
    json.dump(dict(tier='RANDOM100 r5 frozen score-once (BX2), blind replay BR3 matched (lead-verified 27 Oct). No contemporaneous sham; never pooled with SHAM. AR2 t107 producer for report v1.3.',
                   values=v, raw_pointers=ptr, _manifest=manifest), fh, indent=1, ensure_ascii=False)
print(json.dumps(v), hashlib.sha256(out.read_bytes()).hexdigest())
