"""CAUSAL-LENGTH P1-only evaluation builder (W9b, 23 Oct 2026). EXPLORATORY. CPU only; never launches a model.
Implements W9b/CAUSAL-LENGTH-AMENDMENT-P1-20261023.md. The frozen revision-2 builder (build_causal_length.py) is imported
unchanged, hash-checked, and supplies every text, identity and setting rule; this file only picks the cohort and the waves.
  build-eval-p1 OUT  -> OUT/P1-COHORT.json, EVAL-REQUESTS.json, TRUTHS.json, EVAL-FREEZE.json (refuses to overwrite)
  selftest      OUT  -> the same into a scratch dir, plus structural checks
Cohort: the first 80 NR and first 80 R of the frozen POOL.json in its seeded order. No generator, solver or audit result enters."""
import json, hashlib, pathlib, sys, collections, math
HERE = pathlib.Path(__file__).resolve().parent
FROZEN_BUILDER_SHA = '20b8763656e14926922d837d995987657f0a971ac4b75855e9f265c7a509b835'
assert hashlib.sha256((HERE / 'build_causal_length.py').read_bytes()).hexdigest() == FROZEN_BUILDER_SHA, 'frozen builder changed'
sys.path.insert(0, str(HERE)); import build_causal_length as B, power_causal_length as pw
POOL_SHA = '3e7c4951fafe9f1e6c98724c752a2401c65229fe7ddc859c7b5c22c723036ed9'
PAD_SHA = 'd8c89f5a237509e75b056eb0f8a231d717a867d53c54c43c7ad3cd5e9b3ab09b'
N_PER_TAG, WAVES = 80, 12
CONDS = ('control', 'pad')

def put_new(p, x):
    with pathlib.Path(p).open('x', encoding='utf-8') as fh: json.dump(x, fh, indent=1, ensure_ascii=False)

def build(src, out):
    """src: folder holding the frozen POOL.json and PAD.json; out: where the four files go."""
    assert B.HF(src / 'POOL.json') == POOL_SHA and B.HF(src / 'PAD.json') == PAD_SHA, 'pool/pad hash'
    B.check_inputs(); ros = B.load_roster(); pool = B.get(src / 'POOL.json')['pool']; pad = B.get(src / 'PAD.json')['pad']
    assert [x['order'] for x in pool] == sorted(x['order'] for x in pool)
    cohort = [x for t in ('NR', 'R') for x in [y for y in pool if y['tag'] == t][:N_PER_TAG]]
    cohort.sort(key=lambda x: x['order']); assert len(cohort) == 2 * N_PER_TAG
    stim = {}
    for x in cohort:
        pid = x['problem_id']; fam = {m['family']: m['problem'] for m in ros[pid]['members']}; padt = pad[pid]['texts']
        for f, _ in B.FAMILIES:
            assert padt[f] == pad[pid]['preamble'] + '\n\n' + fam[f] and len(padt[f]) <= B.MAX_INPUT_CHARS and fam[f].strip()
        stim[pid] = dict(tag=x['tag'], answer=x['answer'], texts=dict(control=fam, pad=padt),
                         base_words={c: B.words(t['base']) for c, t in (('control', fam), ('pad', padt))})
    system = json.loads((B.F6 / 'REQUESTS.json').read_bytes())[0]['system']; assert B.H(system.encode()) == B.X3_SYSTEM_SHA
    reqs, truths, blocks = [], {}, []
    for w in range(WAVES):                          # one block per wave, both conditions: an early stop never unbalances P1
        blocks.append((w, list(CONDS)))
        for pid in sorted(stim, key=lambda p: B.H(f'{B.SEED}|o|{p}'.encode())):
            for c in sorted(CONDS, key=lambda c: B.H(f'{B.SEED}|cond|{pid}|{w}|{c}'.encode())):
                for f, v in B.FAMILIES:
                    for r in range(w * B.PER_WAVE, (w + 1) * B.PER_WAVE):
                        text = stim[pid]['texts'][c][f]
                        ident = dict(protocol=B.PROTOCOL, model=B.X3_MODEL, revision=B.X3_REV, problem_id=pid, family=f, variant_id=f'{v}|{c}', condition=c,
                                     replicate=r, text_sha256=B.H(text.encode()))
                        ih = B.H(B.canon(ident))
                        reqs.append(dict(order_index=len(reqs), identity=ident, identity_sha256=ih, seed=int(ih[:16], 16) & ((1 << 63) - 1), system=system,
                                         problem=text, settings=dict(B.X3_SETTINGS), scope='EXPLORATORY_ONLY', production_labels_authorized=False))
                        truths[ih] = stim[pid]['answer']
    expect = len(stim) * len(CONDS) * len(B.FAMILIES) * WAVES * B.PER_WAVE
    assert len({q['identity_sha256'] for q in reqs}) == len(reqs) == expect, (len(reqs), expect)
    dlog = [math.log(s['base_words']['pad'] / s['base_words']['control']) for s in stim.values()]
    est = [x['fresh6h_mean_tokens'] for x in cohort if x['fresh6h_mean_tokens']]
    elig = B.get(src / 'POOL.json')['eligible']; br = elig['NR'] / (elig['NR'] + elig['R'])
    power = {f'{b:.3f}': {k: pw.simulate(len(stim), WAVES, WAVES, d, b)[m] for k, d, m in (('power_at_0p05', 0.05, 'power'), ('power_at_dose', pw.OBS_GRADIENT * sum(dlog) / len(dlog), 'power'),
                                                                                    ('p_ci95_inside_0p05_under_null', 0.0, 'p_ci95_inside_0p05'), ('mean_se_null', 0.0, 'mean_se'))}
             for b in (br, pw.EP0)}
    put_new(out / 'P1-COHORT.json', dict(rule=f'first {N_PER_TAG} NR and first {N_PER_TAG} R of POOL.json in its seeded order (sha256 of seed||pid); '
                                     'no generator, solver or audit result enters', pool_sha256=POOL_SHA, pad_sha256=PAD_SHA, cohort=[x['problem_id'] for x in cohort],
                                     counts=dict(collections.Counter(s['tag'] for s in stim.values())), stimuli=stim))
    put_new(out / 'EVAL-REQUESTS.json', reqs); put_new(out / 'TRUTHS.json', truths)
    ev = dict(design='P1-only amendment', amendment='explore/W9b/CAUSAL-LENGTH-AMENDMENT-P1-20261023.md (sha in its .sha256)', conditions=list(CONDS), waves=WAVES,
              block_order=blocks, cohort=len(stim), cohort_counts=dict(collections.Counter(s['tag'] for s in stim.values())), requests=len(reqs),
              requests_per_block=len(reqs) // WAVES, mean_dlog_pad_vs_control=sum(dlog) / len(dlog), min_dlog_pad_vs_control=min(dlog),
              est_tokens_per_request=sum(est) / len(est), est_output_tokens=round(len(reqs) * sum(est) / len(est)),
              base_rate_rule='eligible NR share (no solver filter in this cohort); fresh6h 0.199 shown beside it', power_by_base_rate=power,
              files={k: B.HF(out / k) for k in ('P1-COHORT.json', 'EVAL-REQUESTS.json', 'TRUTHS.json')},
              frozen_inputs=dict(POOL=POOL_SHA, PAD=PAD_SHA, builder_r2=FROZEN_BUILDER_SHA, power_producer=B.HF(HERE / 'power_causal_length.py')),
              p1_builder_sha256=B.HF(__file__))
    put_new(out / 'EVAL-FREEZE.json', ev); return ev, reqs, stim

def selftest(src, out):
    ev, reqs, stim = build(src, out)
    cnt = collections.Counter((q['identity']['problem_id'], q['identity']['condition'], q['identity']['family']) for q in reqs)
    assert set(cnt.values()) == {WAVES * B.PER_WAVE} and len(cnt) == 160 * 2 * 3
    waves = [q['identity']['replicate'] // B.PER_WAVE for q in reqs]; assert waves == sorted(waves), 'blocks must run wave by wave'
    for q in reqs:
        i = q['identity']; t = stim[i['problem_id']]['texts'][i['condition']][i['family']]
        assert q['problem'] == t and i['text_sha256'] == B.H(t.encode()) and q['seed'] == int(q['identity_sha256'][:16], 16) & ((1 << 63) - 1)
    try: build(src, out); raise AssertionError('overwrite not refused')
    except FileExistsError: pass
    print(json.dumps({k: ev[k] for k in ('cohort', 'cohort_counts', 'requests', 'requests_per_block', 'mean_dlog_pad_vs_control', 'min_dlog_pad_vs_control',
                                         'est_tokens_per_request', 'est_output_tokens', 'power_by_base_rate')}, indent=1))

if __name__ == '__main__':
    stage, out = sys.argv[1], pathlib.Path(sys.argv[2]); src = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else HERE / 'final'
    out.mkdir(parents=True, exist_ok=True)
    {'build-eval-p1': lambda: print(json.dumps(build(src, out)[0], indent=1)), 'selftest': lambda: selftest(src, out)}[stage]()
