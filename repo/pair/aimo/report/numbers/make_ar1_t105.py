"""AR1 numbers (t105) for report v1.2: OUTCOME-FREE RANDOM100 r5 design and run facts (no score exists or is read here), and one
constructed leaderboard value for the organisers paragraph.
- RANDOM100: cohort size and pool from the frozen COHORT.json (sha checked against the r5 FREEZE.sha256); waves and records from
  CL4's FINAL-FOR-SCORING receipt. AM1 gate (tasks/NOTE-AR1-from-AM1-AIMO-v1.1-INPUTS-20261027.md): no RANDOM100 outcome enters
  the report before a fresh blind replay matches and the blindness audit passes. This producer reads no outcome file.
- lb_range70_n100: exact binomial 2.5% and 97.5% quantiles of the score of a true-0.70 method on 100 public problems, divided by 100
  (constructed; same quantity as board_noise.json /score_range_95_n14/0.7 at n = 100).
Writes numbers/ar1-t105.json (exclusive create). usage: python -I pair/aimo/report/numbers/make_ar1_t105.py
"""
import hashlib, json
from math import comb
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
PACK = 'from-box/research/W9d/random100-freeze-r5/pack/'
COH, FRZ, SPEC = PACK + 'COHORT.json', PACK + 'FREEZE.sha256', PACK + 'SPEC-v2-20261026.md'
RCP = 'planning/gpu-ops/RANDOM100-FINAL-FOR-SCORING-CL4-20261027.json'
manifest, raw = {}, {}
for rel in (COH, FRZ, SPEC, RCP):
    p = ROOT / rel; b = p.read_bytes(); manifest[str(p)] = hashlib.sha256(b).hexdigest(); raw[rel] = b
frz = dict(line.split()[::-1] for line in raw[FRZ].decode('utf-8').splitlines() if line.strip())
assert frz['COHORT.json'] == manifest[str(ROOT / COH)] and frz['SPEC-v2-20261026.md'] == manifest[str(ROOT / SPEC)]
assert hashlib.sha256(raw[FRZ]).hexdigest().startswith('28d7b0cf')
coh = json.loads(raw[COH].decode('utf-8-sig')); rcp = json.loads(raw[RCP].decode('utf-8-sig'))
assert rcp['final'] and rcp['no_more_generation'] and rcp['status']['abandoned'] == [] and rcp['status']['unsealed'] == []

v, ptr = {}, {}


def put(key, value, pointer):
    assert key not in v; v[key] = value; ptr[key] = pointer


put('r100_n', len(coh['selected']), COH + ' :: len(/selected)')
put('r100_pool', coh['pool_size'], COH + ' :: /pool_size')
put('r100_waves_done', rcp['complete_waves'], RCP + ' :: /complete_waves')
put('r100_waves_planned', rcp['planned_waves'], RCP + ' :: /planned_waves')
put('r100_records', sum(rcp['record_counts'].values()), RCP + ' :: sum /record_counts')
put('r100_stop', rcp['reason'].replace('_', ' '), RCP + ' :: /reason (underscores as spaces)')


def quantile(n, p, q):
    c = 0.0
    for k in range(n + 1):
        c += comb(n, k) * p ** k * (1 - p) ** (n - k)
        if c >= q: return k


put('lb_range70_n100', [quantile(100, 0.7, 0.025) / 100, quantile(100, 0.7, 0.975) / 100],
    'constructed: exact Binomial(100, 0.7) 2.5% and 97.5% quantiles / 100; 2 dp')

out = HERE / 'ar1-t105.json'
with open(out, 'x', encoding='utf-8') as fh:
    json.dump(dict(tier='RANDOM100 r5: outcome-free design and run facts only (no score read); leaderboard: constructed. AR1 t105 producer for report v1.2.',
                   values=v, raw_pointers=ptr, _manifest=manifest), fh, indent=1, ensure_ascii=False)
print(json.dumps(v), hashlib.sha256(out.read_bytes()).hexdigest())
