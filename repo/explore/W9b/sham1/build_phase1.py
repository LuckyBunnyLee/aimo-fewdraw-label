"""SHAM Phase 1 request build (W9b, CPU, deterministic). Implements SHAM-PHASE1-AMENDMENT-20261025.md section 2.
Reads only sha-pinned fresh6h inputs (read-only) and writes COHORT.json, REQUESTS.json, TRUTHS.json and MANIFEST.json
next to this script (exclusive create). No engine, no outcomes: fresh6h tags are copied into COHORT.json for the S1
stratification only, after the cohort is fixed by a hash rule that does not read them.
usage: python -I explore/W9b/sham1/build_phase1.py
"""
import hashlib, json, pathlib, random
from fractions import Fraction

HERE = pathlib.Path(__file__).resolve().parent
JA = pathlib.Path('D:/research-cycle/cl-fresh6h-20261021-0935')
PER = pathlib.Path('E:/work/research-cycle/explore/W9b/fresh6h/out/PER-ORIGINAL.jsonl')
PINS = {JA / 'REQUESTS.json': 'daccdc4f5f81ff48a3b1567301b0879930f205d08345fae72d9c78a3da20b1d7',
        JA / 'TRUTHS.json': 'b06a6f45211c2ce08349c60e71020ade450c3d9fa471eba458dc6d245d45d282',
        JA / 'ROSTER.json': 'b75af74ab88518e448950a49a089ba7d3af67c0aa038406115fc673241d9b05d',
        JA / 'MANIFEST.json': '67d42df993ae19f1fefb2be262bb9e1df428abba88774418b7f5085d034360c0',
        PER: '0e6a6657b948e78a088bd83d6fc5174ee4f4c239b3e6e110dd54358cd52ed49e'}
PROTOCOL = 'W9b-sham-phase1-20261025'
SELECT_SEED = '20261025'          # cohort: first K reached originals by SHA256(SELECT_SEED|problem_id)
ORDER_SEED = 'sham1-order-20261025'
K, WAVES, NDRAW = 320, 15, 4      # 12 planned waves + 3 make-up waves, issued only to replace abandoned ones
FAMILIES = [('base', 'original', 'base'), ('surface_gs', 'gs', 'surface_gs'), ('surface_dlm', 'dlm', 'surface_dlm'),
            ('sham_a', 'original-copy-a', 'base'), ('sham_b', 'original-copy-b', 'base')]  # (family, variant_id, text source)

canon = lambda x: json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
sha = lambda b: hashlib.sha256(b).hexdigest()


def load():
    data = {}
    for p, h in PINS.items():
        b = p.read_bytes(); assert sha(b) == h, 'input changed: ' + str(p); data[p] = b
    J = lambda p: json.loads(data[p].decode('utf-8'))
    return J(JA / 'REQUESTS.json'), J(JA / 'TRUTHS.json'), J(JA / 'ROSTER.json'), J(JA / 'MANIFEST.json'), \
        [json.loads(l) for l in data[PER].decode('utf-8').splitlines() if l.strip()]


def build():
    reqs, truths, roster, man, per = load()
    order = [r['problem_id'] for r in roster['selected']]
    tag = {r['pid']: r['primary'] for r in per}; assert set(tag) == set(order)
    reached = [p for p in order if tag[p]['reached']]
    assert len(order) == 2657 and len(reached) == 2474 and reached == order[:2474], 'reached set is not the roster prefix'
    cohort = sorted(reached, key=lambda p: sha((SELECT_SEED + '|' + p).encode()))[:K]
    # texts and truths from the fresh6h replicate-0 requests of each original
    text, truth, template = {}, {}, {}
    for q in reqs:
        i = q['identity']
        if i['problem_id'] in cohort and i['replicate'] == 0:
            text[(i['problem_id'], i['family'])] = q['problem']; truth.setdefault(i['problem_id'], set()).add(str(truths[q['identity_sha256']]))
            template[i['problem_id']] = q
    assert all(len(v) == 1 for v in truth.values()) and len(truth) == K
    ans = {r['problem_id']: str(r['answer']) for r in roster['selected']}
    assert all(Fraction(next(iter(truth[p]))) == Fraction(ans[p]) for p in cohort), 'truth differs from roster answer'
    out, tru = [], {}
    for w in range(WAVES):
        rng = random.Random(f'{ORDER_SEED}|wave{w}')
        pids = cohort[:]; rng.shuffle(pids)
        for p in pids:
            fams = FAMILIES[:]; rng.shuffle(fams)
            for fam, variant, src in fams:
                body = text[(p, src)]; t0 = template[p]
                for r in range(NDRAW):
                    ident = dict(protocol=PROTOCOL, model=t0['identity']['model'], revision=t0['identity']['revision'], problem_id=p,
                                 family=fam, variant_id=variant, replicate=NDRAW * w + r, text_sha256=sha(body.encode()))
                    key = sha(canon(ident))
                    out.append(dict(order_index=len(out), wave=w, identity=ident, identity_sha256=key, seed=int(key[:16], 16) & ((1 << 63) - 1),
                                    system=t0['system'], problem=body, settings=t0['settings'], scope='EXPLORATORY_ONLY', production_labels_authorized=False))
                    tru[key] = next(iter(truth[p]))
    assert len(out) == K * WAVES * len(FAMILIES) * NDRAW and len({q['identity_sha256'] for q in out}) == len(out)
    assert all(q['problem'] == text[(q['identity']['problem_id'], 'base')] for q in out if q['identity']['family'].startswith('sham'))
    cohort_rows = [dict(problem_id=p, select_rank=i, fresh6h_primary_tag=tag[p]['strict']) for i, p in enumerate(cohort)]
    return cohort_rows, out, tru, man


def main():
    cohort, out, tru, man = build()
    files = {'COHORT.json': dict(protocol=PROTOCOL, rule=f'first {K} of the 2,474 fresh6h-reached originals by SHA256("{SELECT_SEED}|"+problem_id); '
                                 'fresh6h tags are copied after selection, for S1 only', pool=2474, selected=cohort),
             'REQUESTS.json': out, 'TRUTHS.json': tru}
    for name, obj in files.items():
        with (HERE / name).open('xb') as fh: fh.write(canon(obj))
    hs = {n: sha((HERE / n).read_bytes()) for n in files}
    manifest = dict(protocol=PROTOCOL, scope='EXPLORATORY_ONLY', requests=len(out), waves_built=WAVES, waves_planned=12, originals=K,
                    families=[f[0] for f in FAMILIES], draws_per_family_per_wave=NDRAW, requests_per_wave=K * len(FAMILIES) * NDRAW,
                    request_sha256=hs['REQUESTS.json'], truth_sha256=hs['TRUTHS.json'], cohort_sha256=hs['COHORT.json'],
                    max_new_tokens=man['max_new_tokens'], settings=man['settings'], model_revision=man['model_revision'],
                    inference_mode=man['inference_mode'], max_active=man['max_active'],
                    global_token_cap=90_000_000, gpu_hour_cap=20.0, inputs={str(p): h for p, h in PINS.items()})
    with (HERE / 'MANIFEST.json').open('xb') as fh: fh.write(canon(manifest))
    print(json.dumps(dict(hs, MANIFEST=sha((HERE / 'MANIFEST.json').read_bytes()), requests=len(out)), indent=1))


if __name__ == '__main__':
    main()
