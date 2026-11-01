"""W9b numbers (t040) for draft v7.4: the 20 Oct afternoon syntheses (X1 reports 130-177, X3 reports 60-77,
W16 sprint studies 78-94). Every value is parsed from the numbered report file that the syntheses cite, never from
synthesis prose; each pattern must match exactly once, and every report file is sha-pinned.
Values are as the reports state them (their rounding); no value is recomputed here.
Writes numbers/w9b-t040.json (exclusive create).
usage: python -I pair/aimo/paper/numbers/make_w9b_t040.py
"""
import glob, hashlib, json, re
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
EX = ROOT / 'explore'
manifest = {}


def report(pattern):
    hits = glob.glob(str(EX / pattern))
    assert len(hits) == 1, (pattern, hits)
    b = Path(hits[0]).read_bytes()
    manifest[str(Path(hits[0]))] = hashlib.sha256(b).hexdigest()
    return Path(hits[0]), b.decode('utf-8-sig')


def num(s):
    if re.search(r'[/%,]', s) or not re.search(r'\d', s): return s
    return float(s) if re.search(r'[.eE]', s) else int(s)


# (report file glob, regex, keys). A key ending in _ci consumes two groups; other keys one.
SPECS = [
    # --- X1: operational NR versus edit effects ---
    ('X1/130-*.md', r'Use all (\d+) nuisance originals', ['x130_n']),
    ('X1/130-*.md', r'\|independent_families\|(-[\d.]+)\|([+-][\d.]+) \[([+-][\d.]+), ([+-][\d.]+)\]\|([\d.]+)\|',
     ['x130_logscore', 'x130_gain', 'x130_gain_ci', 'x130_p']),
    ('X1/130-*.md', r'\|shared_p\|(-[\d.]+)\|', ['x130_shared_logscore']),
    ('X1/132-*.md', r'\|shared_p\|([\d.]+)\|', ['x132_shared_auc']),
    ('X1/132-*.md', r'\|harm_constrained\|([\d.]+)\|([+-][\d.]+) \[([+-][\d.]+), ([+-][\d.]+)\]',
     ['x132_harm_auc', 'x132_harm_gain', 'x132_harm_gain_ci']),
    ('X1/156-*.md', r'stable edit-contrast variances is([\d.]+) \[([\d.]+),([\d.]+)\]', ['x156_var', 'x156_var_ci']),
    ('X1/156-*.md', r'after linear length projection it is([\d.]+) \[([\d.]+),([\d.]+)\]', ['x156_var_len', 'x156_var_len_ci']),
    ('X1/156-*.md', r'Each exceeds all([\d,]+) total-preserving', ['x156_null_draws']),
    ('X1/160-*.md', r'\|GSMPlus\|(\d+) / \d+\|([\d.]+)\|([\d.]+) \[([\d.]+), ([\d.]+)\]\|([\d.]+) \[([\d.]+), ([\d.]+)\]\|([\d.]+) \[',
     ['x160_gsm_n', 'x160_gsm_mismatch', 'x160_gsm_harm', 'x160_gsm_harm_ci', 'x160_gsm_benefit', 'x160_gsm_benefit_ci', 'x160_gsm_wrong']),
    ('X1/160-*.md', r'\|HarderMATH\|(\d+) / \d+\|([\d.]+)\|([\d.]+) \[([\d.]+), ([\d.]+)\]\|([\d.]+) \[([\d.]+), ([\d.]+)\]\|([\d.]+) \[',
     ['x160_hard_n', 'x160_hard_mismatch', 'x160_hard_harm', 'x160_hard_harm_ci', 'x160_hard_benefit', 'x160_hard_benefit_ci', 'x160_hard_wrong']),
    ('X1/172-*.md', r'gain (-[\d.]+), pipeline interval \[(-[\d.]+),(-[\d.]+)\]', ['x172_gain', 'x172_gain_ci']),
    ('X1/172-*.md', r'answer assay gains ([\d.]+) \[([\d.]+),([\d.]+)\]', ['x172_assay_gain', 'x172_assay_gain_ci']),
    # --- X1: selected-learner gain versus conditional information ---
    ('X1/150-*.md', r'"datasets": (\d+), "planned": (\d+)', ['x150_datasets', 'x150_planned']),
    ('X1/150-*.md', r'(\d+) fresh datasets give mean held-out proxy gain \+([\d.]+)', ['x150_setting_n', 'x150_proxy_gain']),
    ('X1/150-*.md', r'shuffles reject in ([\d.]+%) and([\d.]+%); oracle Y\|L and Z\|L references reject in([\d.]+%) and([\d.]+%)',
     ['x150_rej_global', 'x150_rej_tertile', 'x150_rej_oracle_y', 'x150_rej_oracle_z']),
    ('X1/150-*.md', r'flexible length learner gains \+([\d.]+)', ['x150_flex_gain']),
    # --- X1: state directions, development and transfer ---
    ('X1/168-*.md', r'Primary AUC ([\d.]+) versus length ([\d.]+) gives \+([\d.]+): conditional interval \[[\d.,]+\], complete-pipeline interval \[([\d.]+),([\d.]+)\]',
     ['x168_auc', 'x168_len', 'x168_gain', 'x168_gain_ci']),
    ('X1/168-*.md', r'only ([\d.]+) \[(-?[\d.]+),(-?[\d.]+)\] over base-answer behaviour', ['x168_vs_base', 'x168_vs_base_ci']),
    ('X1/174-*.md', r'Primary gain = ([\d.]+), pipeline 95% interval \[([\d.]+), ([\d.]+)\]', ['x174_gain', 'x174_gain_ci']),
    ('X1/174-*.md', r'"logchars_CVR2": ([\d.]+)', ['x174_len_r2']),
    ('X1/170-*.md', r'On MATH, (\d+) originals/(\d+) NR, frozen state AUC ([\d.]+) versus frozen length ([\d.]+) gives (-[\d.]+) \[(-[\d.]+),([\d.]+)\]',
     ['x170_n', 'x170_nr', 'x170_auc', 'x170_len', 'x170_gain', 'x170_gain_ci']),
    ('X1/176-*.md', r'\|PRIMARY_no_prior_label\|(\d+)/(\d+)\|([\d.]+) \[[\d.,]+\]\|([\d.]+) \[[\d.,]+\]\|\+([\d.]+) \[(-[\d.]+),([\d.]+)\]\|(FAIL)\|',
     ['x176_n', 'x176_nr', 'x176_auc', 'x176_len', 'x176_gain', 'x176_gain_ci', 'x176_decision']),
    ('X1/166-*.md', r'assay\+drift gain over assay is \+([\d.]+), but its full-pipeline interval is \[(-[\d.]+),([\d.]+)\]', ['x166_gain', 'x166_gain_ci']),
    # --- X1: access (supplied-variant assay) and harder transfer ---
    ('X1/158-*.md', r'\|length\|([\d.]+)\|([\d.]+) \[([\d.]+), ([\d.]+)\]\|', ['x158_len_dev', 'x158_len', 'x158_len_ci']),
    ('X1/158-*.md', r'\|PRIMARY_originalmean\|([\d.]+)\|([\d.]+) \[([\d.]+), ([\d.]+)\]\|\+([\d.]+) \[(-[\d.]+), \+([\d.]+)\]',
     ['x158_orig_dev', 'x158_orig', 'x158_orig_ci', 'x158_orig_gain', 'x158_orig_gain_ci']),
    ('X1/158-*.md', r'\|assay_allstate\|([\d.]+)\|([\d.]+) \[([\d.]+), ([\d.]+)\]\|\+([\d.]+) \[\+([\d.]+), \+([\d.]+)\]',
     ['x158_assay_dev', 'x158_assay', 'x158_assay_ci', 'x158_assay_gain', 'x158_assay_gain_ci']),
    ('X1/158-*.md', r'It needs (\w+) feature calls', ['x158_calls']),
    ('X1/158-*.md', r'Binary analysis has(\d+) views from(\d+) distinct originals', ['x158_views', 'x158_originals']),
    ('X1/161-*.md', r'\|GSMPlus / average\|(\d+) / (\d+)\|[^|]*\|([+-][\d.]+) \[([+-][\d.]+), ([+-][\d.]+)\]\|([+-][\d.]+) \[([+-][\d.]+), ([+-][\d.]+)\]',
     ['x161_gsm_views', 'x161_gsm_n', 'x161_gsm_excess', 'x161_gsm_excess_ci', 'x161_gsm_rho', 'x161_gsm_rho_ci']),
    ('X1/161-*.md', r'\|HarderMATH / average\|(\d+) / (\d+)\|[^|]*\|([+-][\d.]+) \[([+-][\d.]+), ([+-][\d.]+)\]\|([+-][\d.]+) \[([+-][\d.]+), ([+-][\d.]+)\]',
     ['x161_hard_views', 'x161_hard_n', 'x161_hard_excess', 'x161_hard_excess_ci', 'x161_hard_rho', 'x161_hard_rho_ci']),
    ('X1/163-*.md', r'retains all(\d+) sampled point-NR cases by the endpoint definition, at([\d.]+%) of full generated tokens',
     ['x163_nr', 'x163_token_share']),
    ('X1/163-*.md', r'primary model gate0\.7 keeps only(\d+/\d+)', ['x163_model_keeps']),
    ('X1/177-*.md', r'reference width difference \(functional minus PMF\) = (-[\d.]+) with Monte Carlo95% interval \[(-[\d.]+), (-[\d.]+)\]',
     ['x177_width', 'x177_width_ci']),
    # --- X3: point-tag design, count structure and its transport ---
    ('X3/60-*.md', r'\*\*([\d.]+%)at4draws/family\*\*, rising to\*\*([\d.]+%)at256\*\*', ['y60_nr_n4', 'y60_nr_n256']),
    ('X3/73-*.md', r'\| Discovery(\d+) \| [\d.]+ \| [\d.]+ \| ([\d.]+) \|', ['y73_disc_n', 'y73_disc_gain']),
    ('X3/73-*.md', r'\| Hardertransfer(\d+) \| -[\d.]+ \| -[\d.]+ \| (-[\d.]+) \|', ['y73_hard_n', 'y73_hard_gain']),
    ('X3/73-*.md', r'\*\*(\d+/\d+) source-weight fits', ['y73_fits']),
    ('X3/65-*.md', r'"completed": (\d+)', ['y65_null_done']),
    ('X3/65-*.md', r'"upper_tail": ([\d.]+)', ['y65_null_tail']),
    ('X3/71-*.md', r'\*\*(\d+)identifiedbinarytags\((\d+)R/(\d+)NR', ['y71_n', 'y71_r', 'y71_nr']),
    ('X3/72-*.md', r'baseline \.(\d+)→\.(\d+)', ['y72_base_strict_milli', 'y72_base_partial_milli']),
    ('X3/72-*.md', r'\|52\|count-interaction-structure\|([\d.]+)\|([\d.]+)\|', ['y72_count_strict', 'y72_count_partial']),
    ('X3/72-*.md', r'RFnumericsecondaryAUC(\.\d+)', ['y72_rf']),
    ('X3/74-*.md', r'\| Three-class disagreement across all (\d+) \| [\d–]+ /\d+ \(([\d.]+)–([\d.]+)%\) \|', ['y74_n', 'y74_range_pct_ci']),
    ('X3/76-*.md', r'\|52\|count-interaction-structure\|([\d.]+)\|\[([\d.]+), ([\d.]+)\]\|', ['y76_auc', 'y76_auc_ci']),
    ('X3/77-*.md', r'\|count-interaction-structure VS constant\|(-[\d.]+)\|\[(-[\d.]+), ([\d.]+)\]\|', ['y77_gain', 'y77_gain_ci']),
    # --- W16: identification and design ---
    ('W16-sprint-20261020/78-*/78-RESULT.md', r'In (\d+) of (\d+) exact synthetic regimes', ['w78_wins', 'w78_regimes']),
    ('W16-sprint-20261020/78-*/78-RESULT.md', r'finite-label AUC (\.\d+) for intrinsic-only versus (\.\d+) for the perfect latent-class score',
     ['w78_intrinsic_auc', 'w78_oracle_auc']),
    ('W16-sprint-20261020/80-*/80-RESULT.md', r'finite-NR AUC (\.\d+) in both, but latent-harm AUC \d+/\d+=(\.\d+) in world A and \d+/\d+=(\.\d+) in world B',
     ['w80_finite_auc', 'w80_latent_a', 'w80_latent_b']),
    ('W16-sprint-20261020/82-*/82-RESULT.md', r'\| Numeric retention \| [\d.]+ \| [\d.]+ \| [\d.]+ \| (\.\d+) \|', ['w82_retention_bonf']),
    ('W16-sprint-20261020/82-*/82-RESULT.md', r'\| Correctness given numeric retention \| [\d.]+ \| [\d.]+ \| (\.\d+) \|', ['w82_correct_tail']),
    ('W16-sprint-20261020/86-*/86-RESULT.md', r'original length Brier is (\.\d+), word (\.\d+) and temperature-2 length (\.\d+)',
     ['w86_len_brier', 'w86_word_brier', 'w86_t2_brier']),
    ('W16-sprint-20261020/86-*/86-RESULT.md', r"improvement over temperature-2 length is (-\.\d+), paired target-only bootstrap interval \[(-\.\d+),(-\.\d+)\]",
     ['w86_gain', 'w86_gain_ci']),
    ('W16-sprint-20261020/88-*/88-RESULT.md', r"accuracy, (\d+/\d+) versus constant robust's (\d+/\d+), has current-library label-shuffle reference tail (\.\d+)",
     ['w88_best', 'w88_const', 'w88_tail']),
    ('W16-sprint-20261020/88-*/88-RESULT.md', r'\| Nested adaptation-set model selection \| (\.\d+) \|', ['w88_nested']),
    ('W16-sprint-20261020/89-*/89-RESULT.md', r'at least (\d+/\d+)=(\.\d+) with two responses per cell, and \d+/\d+=(\.\d+) with four',
     ['w89_floor_n2_frac', 'w89_floor_n2', 'w89_floor_n4']),
    ('W16-sprint-20261020/89-*/89-RESULT.md', r'\| Harder full4 numeric \| (\d+/\d+) \| (\d+/\d+) \|', ['w89_full4_finite', 'w89_full4_upper']),
    ('W16-sprint-20261020/92-*/92-RESULT.md', r'minimum is (\.\d+) at n4 but (\.\d+) at n5', ['w92_n4', 'w92_n5']),
    ('W16-sprint-20261020/94-*/94-RESULT.md', r'At n4 the event-bound asymptote is(\.\d+)', ['w94_n4']),
]

v, raw = {}, {}
for pat, rx, keys in SPECS:
    path, text = report(pat)
    found = re.findall(rx, text)
    assert len(found) == 1, (pat, rx, len(found))
    groups = found[0] if isinstance(found[0], tuple) else (found[0],)
    i = 0
    for k in keys:
        assert k not in v, k
        if k.endswith('_ci'): v[k] = [num(groups[i]), num(groups[i + 1])]; i += 2
        else: v[k] = num(groups[i]); i += 1
        raw[k] = path.relative_to(ROOT).as_posix() + ' :: /' + rx + '/'
    assert i == len(groups), (pat, rx)

# Report 72 prints the baseline without the leading zero; restore it as the AUC it is.
v['y72_base_strict'] = float('0.' + str(v.pop('y72_base_strict_milli'))); raw['y72_base_strict'] = raw.pop('y72_base_strict_milli')
v['y72_base_partial'] = float('0.' + str(v.pop('y72_base_partial_milli'))); raw['y72_base_partial'] = raw.pop('y72_base_partial_milli')
v['x158_calls'] = {'six': 6}[v['x158_calls']]

# Consistency checks across what the reports say about each other.
assert v['x176_decision'] == 'FAIL' and v['x176_gain_ci'][0] < 0
assert v['x170_gain'] < 0 < v['x170_gain_ci'][1]
assert v['x172_gain_ci'][1] < 0 and v['y73_hard_gain'] < 0 < v['y73_disc_gain']
assert v['x158_assay_gain_ci'][0] > 0 and v['x158_orig_gain_ci'][0] < 0
assert v['x161_hard_rho_ci'][0] < 0 < v['x161_hard_rho_ci'][1] and v['x161_gsm_rho_ci'][0] > 0
assert v['w86_gain_ci'][1] < 0 and v['w80_latent_a'] + v['w80_latent_b'] == 1.0
assert abs(v['x168_auc'] - v['x168_len'] - v['x168_gain']) < 0.0015

out = dict(tier='Exploratory; W9b t040 producer (20 Oct afternoon syntheses: X1 130-177, X3 60-77, W16 78-94)', values=v, raw_pointers=raw,
           checks=dict(rule='each regex matched exactly once in its sha-pinned report file; values as printed in the report'),
           _manifest=manifest, producer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (Path(__file__).resolve().parent / 'w9b-t040.json').open('x', encoding='utf-8') as f:
    json.dump(out, f, indent=1)
print(len(v), 'values from', len(manifest), 'reports')
print(json.dumps(v))
