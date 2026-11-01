"""t036b supersedes w9b-t036.json: its parser filter used the wrong status words (terminals.csv uses status "invalid" /
boxed_status "boxed_numeric", and records no boxed value), so it counted 0. t036b counts strict-invalid but boxed-numeric
Skywork terminals; equality of those boxed values with the key is NOT recomputable from terminals.csv and is not claimed here.
W9b turn 036 numbers for draft v7 ("Length is hard to beat"): X1's organiser-label screens, all EXPLORATORY.
Reads machine-readable X1 outputs only (never report prose):
- report 68 screen (explore/X1/screen0850-1792424621460828300: metrics.csv, cohort_summary.json): length/text floor on the
  137 organiser labels, best combination and its gain, the max-increment shuffle p, drift / nuisance-flip / reading-index /
  prefix entropy change on their cohorts with same-cohort refit length;
- primary_target_v2/available-* (familiarity), length-matched-* (drift after length matching), contraction-followup-*
  (entropy-change seeds);
- organiser_primary/label-transfer-* (definition shift), edit-level-* (within-problem final-readout sensitivity);
- gsm_live/SEMANTIC-FLAGS.json (benchmark meaning changes), hard_band snapshot terminals.csv (parser rejections).
Cross-checks: report-68 length/text equal the saved full-137 baselines in available-*/results.json; drift AUC equal in both.
Writes numbers/w9b-t036.json (exclusive create).
usage: python -I pair/aimo/paper/numbers/make_w9b_t036b.py
"""
import csv, hashlib, io, json
from pathlib import Path

X1 = Path(r'E:/work/research-cycle/explore/X1')
manifest = {}


def read(p):
    b = Path(p).read_bytes()
    manifest[str(Path(p))] = hashlib.sha256(b).hexdigest()
    return b.decode('utf-8-sig')


def js(p):
    return json.loads(read(p))


def rows(p):
    return list(csv.DictReader(io.StringIO(read(p))))


v, raw = {}, {}


def put(k, val, ptr):
    assert k not in v, k
    v[k], raw[k] = val, ptr


S = X1 / 'screen0850-1792424621460828300'
met = {(r['cohort'], r['predictor']): r for r in rows(S / 'metrics.csv')}
coh = {c['cohort']: c for c in js(S / 'cohort_summary.json')}


def m(c, p, f):
    val = met[(c, p)][f]
    return json.loads(val) if val.startswith('[') else float(val)


a137 = coh['all137']
assert a137['n'] == 137 and a137['NR'] == 101 and a137['best'] == 'length_m0_state16'
put('org_n', a137['n'], 'X1 screen0850 cohort_summary.json all137 /n')
put('org_nr', a137['NR'], 'cohort_summary all137 /NR')
put('org_r', a137['n'] - a137['NR'], 'cohort_summary all137 n - NR')
put('org_length_auc', m('all137', 'length', 'auc'), 'screen0850 metrics.csv all137,length /auc')
put('org_length_ci', m('all137', 'length', 'ci'), 'metrics.csv all137,length /ci')
put('org_text_auc', m('all137', 'text', 'auc'), 'metrics.csv all137,text /auc')
put('org_best_auc', m('all137', 'length_m0_state16', 'auc'), 'metrics.csv all137,length_m0_state16 /auc')
put('org_best_gain', m('all137', 'length_m0_state16', 'delta_length'), 'metrics.csv all137,length_m0_state16 /delta_length')
put('org_best_gain_ci', m('all137', 'length_m0_state16', 'delta_length_ci'), 'metrics.csv all137,length_m0_state16 /delta_length_ci')
put('org_configs', a137['configurations'], 'cohort_summary all137 /configurations')
put('org_increment_p', a137['screen_max_increment_p'], 'cohort_summary all137 /screen_max_increment_p')
av = js(X1 / 'primary_target_v2/available-1792414144591790100/results.json')
assert abs(av['baseline_full137']['length']['auc'] - v['org_length_auc']) < 1e-9
assert abs(av['baseline_full137']['text']['auc'] - v['org_text_auc']) < 1e-9
put('org_drift_n', int(met[('drift135', 'frozen_minus_drift')]['n']), 'metrics.csv drift135,frozen_minus_drift /n')
put('org_drift_auc', m('drift135', 'frozen_minus_drift', 'auc'), 'metrics.csv drift135,frozen_minus_drift /auc')
put('org_drift_ci', m('drift135', 'frozen_minus_drift', 'ci'), 'metrics.csv drift135,frozen_minus_drift /ci')
put('org_drift_cohort_length', m('drift135', 'frozen_minus_drift', 'length_auc'), 'metrics.csv drift135 /length_auc (same-cohort refit)')
assert abs(av['metrics']['frozen_minus_Qwen_drift']['auc'] - v['org_drift_auc']) < 1e-9
put('org_flip_n', int(met[('paired62', 'frozen_nuisance_flip')]['n']), 'metrics.csv paired62,frozen_nuisance_flip /n')
put('org_flip_auc', m('paired62', 'frozen_nuisance_flip', 'auc'), 'metrics.csv paired62,frozen_nuisance_flip /auc')
put('org_flip_ci', m('paired62', 'frozen_nuisance_flip', 'ci'), 'metrics.csv paired62,frozen_nuisance_flip /ci')
put('org_flip_cohort_length', m('paired62', 'frozen_nuisance_flip', 'length_auc'), 'metrics.csv paired62 /length_auc (same-cohort refit)')
put('org_reading_auc', m('paired62', 'frozen_minus_reading_index', 'auc'), 'metrics.csv paired62,frozen_minus_reading_index /auc')
put('org_familiarity_auc', av['metrics']['frozen_prompt_familiarity']['auc'], 'available-*/results.json /metrics/frozen_prompt_familiarity/auc')
lm = js(X1 / 'primary_target_v2/length-matched-1792414359475745300/results.json')['metrics']['frozen_minus_Qwen_drift']
put('org_drift_matched_pairs', lm['valid_pairs'], 'length-matched-*/results.json /metrics/frozen_minus_Qwen_drift/valid_pairs')
put('org_drift_matched_auc', lm['matched_subset_auc'], 'length-matched /metrics/frozen_minus_Qwen_drift/matched_subset_auc')
p24 = coh['prefix24']
put('prefix_n', p24['n'], 'cohort_summary prefix24 /n')
put('prefix_r', p24['n'] - p24['NR'], 'cohort_summary prefix24 n - NR')
put('prefix_entropy_auc', m('prefix24', 'frozen_entropy_change', 'auc'), 'metrics.csv prefix24,frozen_entropy_change /auc')
put('prefix_entropy_ci', m('prefix24', 'frozen_entropy_change', 'ci'), 'metrics.csv prefix24,frozen_entropy_change /ci')
put('prefix_cohort_length', m('prefix24', 'frozen_entropy_change', 'length_auc'), 'metrics.csv prefix24 /length_auc (same-cohort refit)')
put('prefix_increment_p', p24['screen_max_increment_p'], 'cohort_summary prefix24 /screen_max_increment_p')
cf = [r for r in js(X1 / 'primary_target_v2/contraction-followup-1792415455403172300/results.json')['metrics'] if r['feature'] == 'entropy_change']
mean4 = [r for r in cf if r['seed'] == 'mean4']
assert len(mean4) == 1 and len(cf) == 5
put('prefix_entropy_mean4', mean4[0]['auc'], 'contraction-followup-*/results.json /metrics[feature=entropy_change,seed=mean4]/auc')

lt = js(X1 / 'organiser_primary/label-transfer-1792407474936230200/results.json')
put('def_n', lt['n_common'], 'label-transfer-*/results.json /n_common')
put('def_changed', lt['changed_label_count'], 'label-transfer /changed_label_count')
tr = [r for r in lt['results'] if (r['train_label'], r['heldout_target_label'], r['method']) == ('official', 'nodomain', 'length_state16')]
assert len(tr) == 1
put('def_transfer_auc', tr[0]['auc'], 'label-transfer /results[official->nodomain,length_state16]/auc')
el = js(X1 / 'organiser_primary/edit-level-1792409623836107500/results.json')
put('edit_problems', el['problems'], 'edit-level-*/results.json /problems')
put('edit_within_auc', el['metrics']['js_final']['mean_within_problem_auc'], 'edit-level /metrics/js_final/mean_within_problem_auc')
put('edit_within_ci', el['metrics']['js_final']['within_problem_bootstrap_ci95'], 'edit-level /metrics/js_final/within_problem_bootstrap_ci95')

fl = js(X1 / 'gsm_live/SEMANTIC-FLAGS.json')['flags']
put('gsm_meaning_changes', sum(f['status'] == 'CLEAR_MEANING_CHANGE_SENSITIVITY_EXCLUDE' for f in fl), 'gsm_live/SEMANTIC-FLAGS.json count status CLEAR_MEANING_CHANGE_SENSITIVITY_EXCLUDE')
term = [r for r in rows(X1 / 'hard_band/snapshot-1792406520069398100/terminals.csv') if r['model'].startswith('Skywork')]
rej = [r for r in term if r['status'] == 'invalid' and r['boxed_status'] == 'boxed_numeric']
put('parser_skywork_terminals', len(term), 'hard_band snapshot terminals.csv rows with model Skywork*')
put('parser_skywork_boxed_rejected', len(rej), 'terminals.csv Skywork rows: status invalid (strict) and boxed_status boxed_numeric')

out = dict(tier='Exploratory; W9b turn 036b producer (supersedes w9b-t036.json)', values=v, raw_pointers=raw, _manifest=manifest,
           producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (Path(__file__).resolve().parent / 'w9b-t036b.json').open('x', encoding='utf-8') as f:
    json.dump(out, f, indent=1)
print(json.dumps(v, indent=1))
