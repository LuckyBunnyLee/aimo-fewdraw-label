"""W9b turn 047 numbers (t038) for draft v7.2: X1 report 72 (frozen prefix-entropy readout on 113 new organiser originals)
and X1 reports 70-71 (first-wave volume labels and predictor screen). Every AUC and count used in the draft is recomputed
from the per-row run files where they exist and asserted equal to the run's own summary JSON.
Writes numbers/w9b-t038.json (exclusive create).
usage: python -I pair/aimo/paper/numbers/make_w9b_t038.py
"""
import csv, hashlib, io, json
from collections import Counter
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
P = ROOT / 'explore/X1/prefix113_once/run-1792449357639288400'
V = ROOT / 'explore/X1/volume1355/run-1792443480055232400'
manifest = {}


def read(p):
    b = Path(p).read_bytes()
    manifest[str(Path(p))] = hashlib.sha256(b).hexdigest()
    return b.decode('utf-8-sig')


def rows(p):
    return list(csv.DictReader(io.StringIO(read(p))))


def auc(pairs):  # pairs of (score, is_NR); higher score predicts NR, ties count half
    pos = [s for s, y in pairs if y]; neg = [s for s, y in pairs if not y]
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def close(a, b):
    assert abs(a - b) < 1e-9, (a, b)


# ---- X1 report 72: frozen prefix readout, applied once ----
res = json.loads(read(P / 'results.json'))
ledger = json.loads(read(ROOT / 'explore/X1/PREFIX113-ONCE-EVALUATION.json'))
assert res['evaluation_count'] == 1 and ledger['evaluation_count'] == 1 and ledger['window'] == 'H[32:56]-H[0:32]'
pred = rows(P / 'problem_predictions.csv')
assert len(pred) == 113 and len({r['pid'] for r in pred}) == 113
nr = sum(r['NR'] == 'True' for r in pred)
assert (res['n'], res['NR'], res['R']) == (113, nr, 113 - nr)
m = res['metrics']
for k in ('frozen_entropy_change', 'saved_length_OOF', 'saved_text_OOF', 'frozen_combined_length', 'frozen_length_entropy_change'):
    close(auc([(float(r[k]), r['NR'] == 'True') for r in pred]), m[k]['auc'])
# no overlap with the 24 discovery problems (the freeze names them)
freeze = json.loads(read(P / 'freeze.json'))
disc = set()
def walk(o):
    if isinstance(o, dict):
        for kk, vv in o.items():
            if 'discovery' in kk.lower() and isinstance(vv, list) and all(isinstance(x, str) for x in vv): disc.update(vv)
            walk(vv)
    elif isinstance(o, list):
        for x in o: walk(x)
walk(freeze)
pref_overlap = len(disc & {r['pid'] for r in pred}) if disc else None

fe, sl = m['frozen_entropy_change'], m['saved_length_OOF']
v = dict(
    pfx_n=113, pfx_R=113 - nr, pfx_NR=nr, pfx_evaluations=1,
    pfx_auc=fe['auc'], pfx_auc_ci=fe['ci95'], pfx_gain=fe['delta_saved_length'], pfx_gain_ci=fe['delta_saved_length_ci95'],
    pfx_length_auc=sl['auc'], pfx_length_auc_ci=sl['ci95'], pfx_text_auc=m['saved_text_OOF']['auc'],
    pfx_comb_length_auc=m['frozen_combined_length']['auc'], pfx_comb_entropy_auc=m['frozen_length_entropy_change']['auc'],
    pfx_pair_increment=res['frozen_learned_pair_increment']['delta_auc'], pfx_pair_increment_ci=res['frozen_learned_pair_increment']['ci95'],
)

# ---- X1 reports 70-71: first-wave volume labels ----
audit = json.loads(read(V / 'AUDIT.json'))
lab = rows(V / 'all_group_labels.csv')
cls = Counter(r['label'] for r in lab)
# all_group_labels.csv omits the 64-row no-base MATH diagnostic (all UNUSABLE by design); counts_by_source.csv carries it
bysrc = rows(V / 'counts_by_source.csv')
nobase = [r for r in bysrc if r['protocol'] == 'CL-long6h-v1-math-perturb-text-numeric64-cap4096']
assert len(nobase) == 1 and nobase[0]['UNUSABLE'] == '64' and all(nobase[0][k] == '0' for k in ('BAND', 'FLOOR_UNINFORMATIVE', 'NR_POINT', 'R_POINT'))
assert 'CL-long6h-v1-math-perturb-text-numeric64-cap4096' not in {r['protocol'] for r in lab}
cls['UNUSABLE'] += 64
assert dict(cls) == audit['classes'] and len(lab) + 64 == audit['export_labels']
for k in ('BAND', 'FLOOR_UNINFORMATIVE', 'NR_POINT', 'R_POINT', 'UNUSABLE'):
    assert sum(int(r[k]) for r in bysrc) == cls[k]
binary = [r for r in lab if r['label'] in ('R_POINT', 'NR_POINT')]
groups = {r['original_group'] for r in binary}
assert (len(binary), len(groups)) == (audit['binary_rows'], audit['binary_original_groups'])
assert sum(r['truncated'] != '0' or r['non_numeric'] != '0' for r in binary) == 0 == audit['binary_with_truncation']
rc = audit['record_checks']; assert set(rc.values()) == {audit['firstwave_requests']} and len(rc) == 10
cov = rows(V / 'neural_cache_coverage.csv'); buid = {r['uid'] for r in binary}
neural_hits = {c: sum(1 for r in cov if r['uid'] in buid and r[c] != '') for c in ('qwen_surprisal', 'drift_slope', 'forced_nuisance_flip')}
assert set(neural_hits.values()) == {0}
v.update(
    vol_requests=audit['firstwave_requests'], vol_exports=audit['export_labels'], vol_binary=len(binary), vol_groups=len(groups),
    vol_R=cls['R_POINT'], vol_NR=cls['NR_POINT'], vol_band=cls['BAND'], vol_floor=cls['FLOOR_UNINFORMATIVE'], vol_unusable=cls['UNUSABLE'],
    vol_record_checks=len(rc), vol_label_mismatch=audit['label_recompute_mismatch_count'],
    vol_trunc=audit['primary_status_counts']['truncated'], vol_trunc_rate=audit['primary_truncation_rate'],
    vol_gsm_changed_key=sum(audit['gsm_changed_key_families'].values()), vol_neural_cov=0,
)

# predictor screen: recompute cohort length/best AUCs from OOF predictions
best = {b['cohort']: b for b in json.loads(read(V / 'SCREEN-cohort-best.json'))}
pr = rows(V / 'SCREEN-predictions.csv')
def cauc(c, p): return auc([(float(r['score']), r['NR'] == 'True') for r in pr if r['cohort'] == c and r['predictor'] == p])
for c in ('pooled1048', 'GSMPlus_nuisance', 'MATH_simple_hard'):
    close(cauc(c, 'length'), best[c]['length_auc']); close(cauc(c, best[c]['predictor']), best[c]['auc'])
adj = [a for a in json.loads(read(V / 'SOURCE-ADJUSTED-COMPARISONS.json')) if a['cohort'] == 'pooled1048' and a['predictor'] == 'text_source']
assert len(adj) == 1; adj = adj[0]
close(cauc('pooled1048', 'length_source'), adj['baseline_auc'])
val = json.loads(read(V / 'SCREEN-VALIDATION.json')); assert val['passed'] and val['frozen113_applied'] is False
g, mm, pl = best['GSMPlus_nuisance'], best['MATH_simple_hard'], best['pooled1048']
v.update(
    vol_configs=val['configurations'],
    vol_pool_length_auc=pl['length_auc'], vol_pool_text_auc=pl['text_auc'], vol_pool_lensrc_auc=adj['baseline_auc'],
    vol_pool_textsrc_gain=adj['delta'], vol_pool_textsrc_gain_ci=adj['ci95'],
    vol_nuis_n=g['n'], vol_nuis_NR=g['NR'], vol_nuis_length_auc=g['length_auc'], vol_nuis_gain=g['delta_length'], vol_nuis_gain_ci=g['delta_length_ci95'],
    vol_math_n=mm['n'], vol_math_NR=mm['NR'], vol_math_length_auc=mm['length_auc'], vol_math_gain=mm['delta_length'], vol_math_gain_ci=mm['delta_length_ci95'],
)

# CL neural extraction for the volume originals: launched, first output verified (status only, not a result)
fov = json.loads(read(ROOT / 'explore/CL-volume-features-20261019/FIRST-OUTPUT-VERIFICATION.json'))
assert fov['PASS'] is True
raw = {k: ('explore/X1/prefix113_once/run-1792449357639288400/results.json' if k.startswith('pfx_') else
           'explore/X1/volume1355/run-1792443480055232400/{AUDIT.json,all_group_labels.csv,SCREEN-cohort-best.json,SCREEN-predictions.csv,SOURCE-ADJUSTED-COMPARISONS.json}')
       for k in v}
out = dict(tier='Exploratory; W9b t038 producer (X1 reports 70-72)', values=v, raw_pointers=raw,
           checks=dict(prefix_discovery_overlap=pref_overlap, neural_hits=neural_hits, cl_volume_features_first_output_pass=True),
           _manifest=manifest, producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (Path(__file__).resolve().parent / 'w9b-t038.json').open('x', encoding='utf-8') as f:
    json.dump(out, f, indent=1)
print(json.dumps(v)); print(out['checks'])
