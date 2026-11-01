"""W9b numbers (t041b) for draft v7.7; t041 for draft v7.5: the 20 Oct evening syntheses (X1 reports 178-187, X3 reports 81, 97-V2, 106, 109,
114, W16 study 125). Values are parsed from the numbered report files (or, for X3-81, its RESULT.json), never from synthesis
prose. Each pattern must match exactly once within its region; every file is sha-pinned. Values keep the reports' rounding.
Writes numbers/w9b-t041b.json (exclusive create).
t041b (M1a, 21 Oct; M1b verification F1): g114_state/_ci and g114_paid/_ci are read from
statistics.PRIMARY_global_centered_NR in X3 114/RESULT.json, the primary the run declares, not from the first
'state' block in the report (raw_NR secondary). Rounded to 4 dp. All other keys are unchanged from t041.
usage: python -I pair/aimo/paper/numbers/make_w9b_t041b.py
"""
import glob, hashlib, json, re
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
EX = ROOT / 'explore'
manifest = {}
F = r'(-?[\d.]+(?:e-?\d+)?)'  # one float as printed in a Python-dict report


def load(pattern):
    hits = glob.glob(str(EX / pattern))
    assert len(hits) == 1, (pattern, hits)
    b = Path(hits[0]).read_bytes()
    manifest[str(Path(hits[0]))] = hashlib.sha256(b).hexdigest()
    return Path(hits[0]), b.decode('utf-8-sig')


def num(s):
    if re.search(r'[/%,]', s) or not re.search(r'\d', s): return s
    return float(s) if re.search(r'[.eE]', s) else int(s)


# (file glob, region (start marker, end marker) or None, regex, keys); a key ending in _ci takes two groups.
S97 = ("'strict_disjoint'", "'operational38'")
SPECS = [
    # --- X1: state forecasts ability, not edit-specific structure ---
    ('X1/178-*.md', None, r'\| Length \+ state, shared probability \| [−\-\d.]+ \| state increment \+([\d.]+) \| \[([−\-\d.]+), ([\d.]+)\] \|', ['e178_shared', 'e178_shared_ci']),
    ('X1/178-*.md', None, r'\*\*primary state increment \+([\d.]+)\*\* \| \*\*\[([−\-\d.]+), ([\d.]+)\]\*\*', ['e178_family', 'e178_family_ci']),
    ('X1/182-*.md', None, r'state-interaction gain is \*\*([−\-\d.]+)\*\*, full-pipeline interval \*\*\[([−\-\d.]+), ([\d.]+)\]\*\*', ['e182_gain', 'e182_gain_ci']),
    ('X1/183-*.md', None, r'state gain in MSE is \*\*([−\-\d.]+)\*\*, pipeline95% \*\*\[([−\-\d.]+), \+([\d.]+)\]\*\*', ['e183_gain', 'e183_gain_ci']),
    ('X1/187-*.md', None, r'remains \*\*\+([\d.]+)\*\*, but the500-refit whole-pipeline95% interval is \*\*\[([−\-\d.]+), ([\d.]+)\]\*\*', ['e187_gain', 'e187_gain_ci']),
    ('X1/180-*.md', None, r'With (\d+) originals and four independent draws per arm, even a test observing all the counts has total-variation separation \*\*([\d.]+)\*\*, equal-prior optimal world-classification error \*\*([\d.]+)\*\*, and most-powerful size-0\.05 power \*\*([\d.]+)\*\*',
     ['e180_n', 'e180_tv', 'e180_error', 'e180_power']),
    # --- X3: fresh-question transfer (81) and the fresh disjoint paid assay (97-V2) ---
    ('X3/81-fresh-transfer-ready63-*.md', None, r'Charged block-wall GPUh([\d.]+), usable/hour([\d.]+), NR/hour([\d.]+)', ['f81_gpuh', 'f81_usable_h', 'f81_nr_h']),
    ('X3/81-fresh-transfer-ready63-*.md', None, r'All(\d+) expected records for(\d+) fresh originals', ['f81_records', 'f81_originals']),
    ('X3/81-fresh-transfer-all38-*.md', None, r"Strict classes:\{'NR': (\d+), 'R': (\d+), 'UNUSABLE': (\d+)\}", ['f81all_nr', 'f81all_r', 'f81all_unusable']),
    ('X3/81-fresh-transfer-all38-*.md', None, r'\|interaction-A4\|([\d.]+)\|[\d.]+\|[\d.]+\|\r?\n\|point-K\|([\d.]+)\|', ['f81all_count', 'f81all_pointk']),
    ('X3/97-V2-*.md', S97, r"'strict_disjoint': \{'originals': (\d+)", ['f97_n']),
    ('X3/97-V2-*.md', S97, r"'frozen_full': " + F + r", 'frozen_noise': " + F + r", 'global_constant': " + F, ['f97_frozen', 'f97_frozen_noise', 'f97_constant']),
    ('X3/97-V2-*.md', S97, r"'A2_vs_matched_prior': \{'observed': " + F + r", 'bootstrap95': \[" + F + ', ' + F + r"\]", ['f97_base', 'f97_base_ci']),
    ('X3/97-V2-*.md', S97, r"'allA6_vs_A2': \{'observed': " + F + r", 'bootstrap95': \[" + F + ', ' + F + r"\]", ['f97_edits', 'f97_edits_ci']),
    ('X3/97-V2-*.md', S97, r"'individual_vs_global_after_A2': \{'observed': " + F + r", 'bootstrap95': \[" + F + ', ' + F + r"\]", ['f97_item', 'f97_item_ci']),
    ('X3/97-V2-*.md', S97, r"'paid_feature_output_tokens': \{'A_base2': (\d+), 'A_all6': (\d+)\}", ['f97_tok_base', 'f97_tok_all']),
    # --- X3: regularization, repeatability, bounded probe ---
    ('X3/106-*.md', None, r"'LOSO8-source': \{'observed': " + F + r", 'pipeline_bootstrap95': \[" + F + ', ' + F + r"\]", ['g106_gain', 'g106_gain_ci']),
    ('X3/109-global-*.md', ("'old917_numeric'", "'fresh23_numeric'"), r"'global_adjusted': \{'crossproduct': \{'observed': " + F + r"[^}]*?'pipeline95': \[" + F + ', ' + F + r"\]", ['g109_obs', 'g109_ci']),
    ('X3/109-global-*.md', None, r"'old917_numeric': \{'originals': (\d+)", ['g109_n']),
    ('X3/109-V2-*.md', ("'fresh23_numeric'", "'fresh38_operational'"), r"'crossproduct': \{'percentile95': \[" + F + ', ' + F + r"\]", ['g109_fresh_ci']),
    ('X3/114-*.md', None, r"'originals': (\d+), 'statistics'", ['g114_n']),
    # --- W16 ---
    ('W16-round-20261020-1530/125-*/125-RESULT.md', None, r'match across all ([\d,]+) requests', ['h125_requests']),
]

v, raw = {}, {}
for pat, region, rx, keys in SPECS:
    path, text = load(pat)
    if region:
        a = text.index(region[0]); b = text.index(region[1], a)
        assert text.count(region[0]) >= 1 and a < b
        text = text[a:b]
    found = re.findall(rx, text, re.S)
    assert len(found) == 1, (pat, rx, len(found))
    groups = found[0] if isinstance(found[0], tuple) else (found[0],)
    groups = [g.replace('−', '-') for g in groups]
    i = 0
    for k in keys:
        assert k not in v, k
        if k.endswith('_ci'): v[k] = [num(groups[i]), num(groups[i + 1])]; i += 2
        else: v[k] = num(groups[i]); i += 1
        raw[k] = path.relative_to(ROOT).as_posix() + (f' within [{region[0]} .. {region[1]})' if region else '') + ' :: /' + rx + '/'
    assert i == len(groups), (pat, rx)

# X3-81 ready63 primary endpoint: read from the run's RESULT.json (the report prints the point gain but not its interval).
rp, rt = load('X3/evening-20261020/81-ready63/RESULT.json')
r = json.loads(rt)
e = r['endpoints']['strict_n4']
assert r['primary'] == 'interaction-A4'
v.update(f81_binary=e['binary'], f81_r=e['R'], f81_nr=e['NR'], f81_templates=e['templates'],
         f81_count=e['metrics']['interaction-A4']['AUC'], f81_pointk=e['metrics']['point-K']['AUC'],
         f81_gain_ci=e['bootstrap']['original']['interval95']['interaction-A4']['AUCgain'],
         f81_boot=e['bootstrap']['original']['completed'])
v['f81_gain'] = v['f81_count'] - v['f81_pointk']
for k, ptr in (('f81_binary', 'binary'), ('f81_r', 'R'), ('f81_nr', 'NR'), ('f81_templates', 'templates'), ('f81_count', 'metrics/interaction-A4/AUC'),
               ('f81_pointk', 'metrics/point-K/AUC'), ('f81_gain_ci', 'bootstrap/original/interval95/interaction-A4/AUCgain'),
               ('f81_boot', 'bootstrap/original/completed'), ('f81_gain', 'metrics/interaction-A4/AUC minus metrics/point-K/AUC')):
    raw[k] = rp.relative_to(ROOT).as_posix() + ' :: /endpoints/strict_n4/' + ptr
_, md81 = load('X3/81-fresh-transfer-ready63-*.md')
assert 'Primary AUC gain vs point-K:0.10096153846153844' in md81 and abs(v['f81_gain'] - 0.10096153846153844) < 1e-12
assert (v['f81_binary'], v['f81_r'], v['f81_nr']) == (21, 13, 8) and v['f81_gain_ci'][0] < 0 < v['f81_gain_ci'][1]

# X3-114 primary (M1b F1): read the declared PRIMARY block from RESULT.json.
p114, t114 = load('X3/evening-20261020/114/RESULT.json')
r114 = json.loads(t114)
assert 'global-centered' in r114['primary'] and 'PRIMARY_global_centered_NR' in r114['statistics']
pb = r114['statistics']['PRIMARY_global_centered_NR']
for k, blk in (('g114_state', 'state'), ('g114_paid', 'paid_residual')):
    v[k] = round(pb[blk]['projected_gain'], 4); v[k + '_ci'] = [round(x, 4) for x in pb[blk]['projected_pipeline95']]
    raw[k] = p114.relative_to(ROOT).as_posix() + f' :: /statistics/PRIMARY_global_centered_NR/{blk}/projected_gain, 4 dp'
    raw[k + '_ci'] = p114.relative_to(ROOT).as_posix() + f' :: /statistics/PRIMARY_global_centered_NR/{blk}/projected_pipeline95, 4 dp'
assert v['g114_state'] < 0 and v['g114_state_ci'][1] < 0 and v['g114_paid_ci'][0] > 0

# Consistency checks.
assert v['e178_family_ci'][0] < 0 and v['e182_gain'] < 0 < v['e182_gain_ci'][1] and v['e187_gain_ci'][0] < 0
assert v['f97_edits_ci'][0] < 0 < v['f97_edits_ci'][1] and v['f97_item_ci'][0] < 0 < v['f97_item_ci'][1] and v['f97_base_ci'][0] > 0
assert v['f97_frozen'] < v['f97_constant'] and v['g114_paid_ci'][0] > 0 and v['g114_state_ci'][0] < 0
assert v['g109_ci'][0] > 0 and v['g109_fresh_ci'][0] < 0 and v['f81all_nr'] + v['f81all_r'] == 23

out = dict(tier='Exploratory; W9b t041b producer (t041 with the X3-114 primary) (20 Oct evening syntheses: X1 178-187, X3 81/97-V2/106/109/114, W16 125)', values=v, raw_pointers=raw,
           checks=dict(rule='each regex matched exactly once in its region of a sha-pinned report file; X3-81 primary from RESULT.json; values as printed'),
           _manifest=manifest, producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (Path(__file__).resolve().parent / 'w9b-t041b.json').open('x', encoding='utf-8') as f:
    json.dump(out, f, indent=1)
print(len(v), 'values from', len(manifest), 'files')
print(json.dumps(v))
