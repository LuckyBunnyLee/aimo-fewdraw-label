"""Offline KA-1 audit of frozen request/draw records; no scoring or inference."""
import hashlib, json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DATA = ROOT / 'explore/W9b/sham1'
OUT = ROOT / 'from-box/research/W9d/sham1-score/tree/explore/W9b/sham1/v1.1/out'
canon = lambda x: json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
paths = [DATA / n for n in ['build_phase1.py', 'REQUESTS.json', 'TRUTHS.json', 'MANIFEST.json', 'COHORT.json', 'launch_shim_d2.py']]
paths += [DATA / 'v1.1' / n for n in ['wave_runner.py', 'wave_core.py', 'score_phase1.py', 'SHAM1-FREEZE-v1.1.sha256']]
paths += [ROOT / 'explore/X3/fresh81_pure.py', OUT / 'DRAWS.jsonl', OUT / 'RESULT.json', Path(__file__).resolve()]
pins = {str(p): sha(p) for p in paths}
m = json.loads((DATA / 'MANIFEST.json').read_bytes())
req = json.loads((DATA / 'REQUESTS.json').read_bytes())
truth = json.loads((DATA / 'TRUTHS.json').read_bytes())
assert sha(DATA / 'REQUESTS.json') == m['request_sha256']
assert sha(DATA / 'TRUTHS.json') == m['truth_sha256']
bykey = {}; cells = {}
for i, q in enumerate(req):
    ident = q['identity']; key = hashlib.sha256(canon(ident)).hexdigest()
    assert key == q['identity_sha256'] and key not in bykey
    assert q['seed'] == int(key[:16], 16) & ((1 << 63) - 1)
    assert q['order_index'] == i
    assert ident['replicate'] // m['draws_per_family_per_wave'] == q['wave']
    assert hashlib.sha256(q['problem'].encode()).hexdigest() == ident['text_sha256']
    bykey[key] = q
    cells.setdefault((q['wave'], ident['problem_id'], ident['replicate']), {})[ident['family']] = q
copy_checks = 0
for group in cells.values():
    assert set(group) == set(m['families'])
    base = group['base']
    for fam in ['sham_a', 'sham_b']:
        q = group[fam]
        assert {k: v for k, v in q.items() if k not in ['identity', 'identity_sha256', 'seed', 'order_index']} == {k: v for k, v in base.items() if k not in ['identity', 'identity_sha256', 'seed', 'order_index']}
        assert {k: v for k, v in q['identity'].items() if k not in ['family', 'variant_id']} == {k: v for k, v in base['identity'].items() if k not in ['family', 'variant_id']}
        assert truth[q['identity_sha256']] == truth[base['identity_sha256']]
        copy_checks += 1
cohort = [r['problem_id'] for r in json.loads((DATA / 'COHORT.json').read_bytes())['selected']]
expected = []
families = [('base', 'original'), ('surface_gs', 'gs'), ('surface_dlm', 'dlm'), ('sham_a', 'original-copy-a'), ('sham_b', 'original-copy-b')]
for w in range(m['waves_built']):
    rng = random.Random(f'sham1-order-20261025|wave{w}')
    pids = cohort[:]; rng.shuffle(pids)
    for p in pids:
        fs = families[:]; rng.shuffle(fs)
        for fam, variant in fs:
            for r in range(m['draws_per_family_per_wave']): expected.append((w, p, fam, variant, 4*w+r))
assert expected == [(q['wave'], q['identity']['problem_id'], q['identity']['family'], q['identity']['variant_id'], q['identity']['replicate']) for q in req]
draws = [json.loads(l) for l in (OUT / 'DRAWS.jsonl').read_bytes().splitlines()]
seen = set()
for d in draws:
    q = bykey[d['key']]; ident = q['identity']
    assert d['key'] not in seen; seen.add(d['key'])
    assert (d['pid'], d['family'], d['wave'], d['replicate']) == (ident['problem_id'], ident['family'], q['wave'], ident['replicate'])
result = json.loads((OUT / 'RESULT.json').read_bytes())
waves = result['meta']['scored_waves']
assert seen == {k for k, q in bykey.items() if q['wave'] in waves}
values = dict(cx2_request_count=len(req), cx2_copy_checks=copy_checks, cx2_draw_count=len(draws), cx2_sham_pct=round(100*result['T1_joint']['sham']['est'], 1), cx2_real_pct=round(100*result['T1_joint']['real']['est'], 1))
for p in paths:
    values['cx2_sha_' + str(paths.index(p))] = pins[str(p)]
report = dict(tier='CX2 offline request identity audit, no new outcome analysis', values=values,
              raw_pointers={k: ('deterministic assertions in make_cx2_repro.py; 1 dp' if k.endswith('_pct') else 'deterministic assertions and SHA256 in make_cx2_repro.py') for k in values},
              _manifest=pins)
with (HERE / 'numbers/cx2-repro.json').open('x', encoding='utf-8') as f: json.dump(report, f, indent=1)
print(json.dumps(values, indent=1))
