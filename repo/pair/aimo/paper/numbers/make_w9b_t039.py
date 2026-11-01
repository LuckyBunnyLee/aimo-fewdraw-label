"""W9b turn 048 numbers (t039) for draft v7.3: X1 reports 73-76 (complete-volume neural screen, freeze of the
input-prior/start-entropy candidate, eligibility block, amended one-shot validation). AUCs are recomputed from per-problem
scores and asserted equal to the run summaries; the validation intervals are recomputed as 2.5/97.5 percentiles of the saved
paired bootstrap draws.
Writes numbers/w9b-t039.json (exclusive create).
usage: python -I pair/aimo/paper/numbers/make_w9b_t039.py
"""
import csv, hashlib, io, json
from pathlib import Path
import numpy as np

ROOT = Path(r'E:/work/research-cycle')
X1 = ROOT / 'explore/X1'
S = X1 / 'volume1955/run-1792464972961084800'
A = X1 / 'amended0055'
FREEZE_SHA = '6bdb06b7e69c8467d664fdf141942cf44a6b3b24fa3f06d6cc97c8a03eb686e2'
manifest = {}


def read(p):
    b = Path(p).read_bytes()
    manifest[str(Path(p))] = hashlib.sha256(b).hexdigest()
    return b.decode('utf-8-sig')


def rows(p):
    return list(csv.DictReader(io.StringIO(read(p))))


def auc(pairs):  # (score, is_NR); higher score predicts NR, ties count half
    pos = [s for s, y in pairs if y]; neg = [s for s, y in pairs if not y]
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def close(a, b, tol=1e-9):
    assert abs(a - b) < tol, (a, b)


# ---- report 73: neural screen on the 734 nuisance-only GSM-Plus originals ----
met = [r for r in rows(S / 'metrics.csv') if r['cohort'] == 'GSMPlus_nuisance']
mrow = {r['predictor']: r for r in met}
pred = [r for r in rows(S / 'predictions.csv') if r['cohort'] == 'GSMPlus_nuisance']
def cauc(p): return auc([(float(r['score']), r['NR'] == 'True') for r in pred if r['predictor'] == p])
for p in ('length', 'length_input_start3', 'text', 'frozen_prefix_entropy_change'):
    if any(r['predictor'] == p for r in pred):
        close(cauc(p), float(mrow[p]['auc']))
cand = mrow['length_input_start3']
assert int(cand['n']) == 734 and int(cand['NR']) == 181
close(float(cand['auc']) - float(mrow['length']['auc']), float(cand['delta_length']))
contr = [c for c in json.loads(read(S / 'additional_paired_contrasts.json'))
         if c['predictor'] == 'length_input_start3' and c['baseline'] == 'current_token_length']
assert len(contr) == 1
val = json.loads(read(S / 'VALIDATION.json')); assert val['passed']
v = dict(
    ns_n=734, ns_NR=181, ns_configs=len(met),
    ns_cand_auc=float(cand['auc']), ns_cand_auc_ci=json.loads(cand['ci95']), ns_length_auc=float(mrow['length']['auc']),
    ns_cand_gain=float(cand['delta_length']), ns_cand_gain_ci=json.loads(cand['delta_length_ci95']),
    ns_p_fold_source=float(cand['fold_source_max_gain_length_p']), ns_p_length_band=float(cand['fold_source_length_max_gain_length_p']),
    ns_cand_gain_tok=contr[0]['delta_auc'], ns_cand_gain_tok_ci=contr[0]['ci95'],
    ns_prefix_auc=float(mrow['frozen_prefix_entropy_change']['auc']),
    ns_drift_len_auc=float(mrow['length_drift_prompt12']['auc']) if 'length_drift_prompt12' in mrow else None,
)
assert v['ns_drift_len_auc'] is not None

# ---- report 74: freeze ----
fz_b = (X1 / 'validation_freeze2045/FREEZE.json').read_bytes(); read(X1 / 'validation_freeze2045/FREEZE.json')
assert hashlib.sha256(fz_b).hexdigest() == FREEZE_SHA
fz = json.loads(fz_b)
tr = rows(X1 / 'validation_freeze2045/TRAINING-DATA.csv')
assert (len(tr), sum(r['label'] == 'NR_POINT' for r in tr), sum(r['label'] == 'R_POINT' for r in tr)) == (734, 181, 553)
assert (fz['training_n'], fz['training_NR'], fz['training_R']) == (734, 181, 553)

# ---- report 75: eligibility block (no scores) ----
au = json.loads(read(X1 / 'independent0040/AUDIT.json'))
assert au['status'] == 'BLOCKED_FROZEN_ELIGIBILITY' and au['new_predictor_scores_computed'] == 0 and au['freeze_sha256'] == FREEZE_SHA
lc = au['label_counts']
v.update(val_roster=au['roster_n'], val_roster_R=lc['R_POINT'], val_roster_NR=lc['NR_POINT'], val_roster_floor=lc['FLOOR_UNINFORMATIVE'],
         val_roster_unusable=lc['UNUSABLE'], val_registry_overlap=au['frozen_registry_original_text_overlap'],
         val_prior_ids=au['frozen_registry_pid_overlap'], val_dev_overlap=au['development_binary_original_overlap'])

# ---- report 76: amended one-shot validation ----
res = json.loads(read(A / 'RESULTS.json'))
ledger = json.loads(read(X1 / 'AMENDED-REPORT74-APPLIED-ONCE.json'))
assert ledger['status'] == 'complete' and ledger['results'] == res
plan = json.loads(read(A / 'PLAN-BEFORE-SCORES.json'))
assert plan['freeze_sha256'] == FREEZE_SHA and 'not exactly unchanged report74 validation' in plan['deviation']
assert plan['development_feature_text_overlap'] == 0 and plan['training_pid_overlap'] == 0
pids = {}
for tag, key in (('PRIMARY_no_prior_label', 'p'), ('SECONDARY_all_binary', 's')):
    r = res[tag]
    sc = json.loads(read(A / f'{tag}-SCORES.json'))
    assert all(x['label'] in ('R_POINT', 'NR_POINT') for x in sc) and len({x['pid'] for x in sc}) == len(sc) == r['n']
    nr = sum(x['label'] == 'NR_POINT' for x in sc); assert (nr, len(sc) - nr) == (r['NR'], r['R'])
    ca = auc([(x['candidate'], x['label'] == 'NR_POINT') for x in sc]); la = auc([(x['length'], x['label'] == 'NR_POINT') for x in sc])
    close(ca, r['candidate_auc']); close(la, r['length_auc']); close(ca - la, r['gain'])
    bs = np.array([[float(x['candidate_auc']), float(x['length_auc']), float(x['gain'])] for x in rows(A / f'{tag}-BOOTSTRAPS.csv')])
    assert len(bs) == 2000 == r['valid_bootstraps']
    lo, hi = np.percentile(bs, 2.5, axis=0), np.percentile(bs, 97.5, axis=0)
    for i in range(3):
        close(lo[i], r['interval95'][0][i], 1e-12); close(hi[i], r['interval95'][1][i], 1e-12)
    assert r['decision'] == 'FAIL' and r['status'] == 'AMENDED_VALIDATION'
    # frozen rule: PASS iff gain > 0 and lower bound > 0
    assert not (r['gain'] > 0 and r['interval95'][0][2] > 0)
    pids[key] = {x['pid'] for x in sc}
    v.update({f'val_{key}_n': r['n'], f'val_{key}_R': r['R'], f'val_{key}_NR': r['NR'],
              f'val_{key}_cand_auc': r['candidate_auc'], f'val_{key}_cand_auc_ci': [r['interval95'][0][0], r['interval95'][1][0]],
              f'val_{key}_length_auc': r['length_auc'], f'val_{key}_length_auc_ci': [r['interval95'][0][1], r['interval95'][1][1]],
              f'val_{key}_gain': r['gain'], f'val_{key}_gain_ci': [r['interval95'][0][2], r['interval95'][1][2]],
              f'val_{key}_decision': r['decision']})
assert pids['p'] < pids['s']
v['val_secondary_extra'] = len(pids['s'] - pids['p'])
assert v['val_secondary_extra'] == 44 and v['val_s_n'] == v['val_roster_R'] + v['val_roster_NR']
# X1 DECISIONS.md is append-only; not pinned. Record whether it still has the sha the amended plan bound.
dec_sha_now = hashlib.sha256((X1 / 'DECISIONS.md').read_bytes()).hexdigest()

raw = {}
for k in v:
    if k.startswith('ns_'): raw[k] = 'explore/X1/volume1955/run-1792464972961084800/{metrics.csv,predictions.csv,additional_paired_contrasts.json} (GSMPlus_nuisance)'
    elif k.startswith('val_roster') or k in ('val_registry_overlap', 'val_prior_ids', 'val_dev_overlap'): raw[k] = 'explore/X1/independent0040/AUDIT.json'
    else: raw[k] = 'explore/X1/amended0055/{RESULTS.json,*-SCORES.json,*-BOOTSTRAPS.csv}'
out = dict(tier='Exploratory; W9b t039 producer (X1 reports 73-76)', values=v, raw_pointers=raw,
           checks=dict(freeze_sha256=FREEZE_SHA, training=[734, 553, 181], decisions_sha_bound_in_plan=plan['decisions_sha256'],
                       decisions_sha_now=dec_sha_now, primary_subset_of_secondary=True),
           _manifest=manifest, producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (Path(__file__).resolve().parent / 'w9b-t039.json').open('x', encoding='utf-8') as f:
    json.dump(out, f, indent=1)
print(json.dumps(v)); print(out['checks'])
