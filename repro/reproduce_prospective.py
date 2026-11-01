"""Recompute the prospective identical-text control (report Section 4, Table 1) from the released draw records.

Calls the frozen scorer's own analyse() (repo/explore/W9b/sham1/v1.1/score_phase1.py, unchanged) on
DRAWS.jsonl (one row per draw: problem id, version, wave, replicate, answer status, correct, tokens) and the
cohort's fresh-test tags, then compares every value with the RESULT.json the scorer wrote on 26 Oct 2026.
No model, GPU or problem text is needed. CPU, about a minute.
usage: python repro/reproduce_prospective.py      (from the release root)
"""
import json, math, sys
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[1] / 'repo'
OUT = REPO / 'from-box/research/W9d/sham1-score/tree/explore/W9b/sham1/v1.1/out'
sys.path.insert(0, str(REPO / 'explore/W9b/sham1/v1.1'))
import score_phase1 as s  # the frozen scorer; importing it runs nothing

draws = [json.loads(line) for line in (OUT / 'DRAWS.jsonl').read_text(encoding='utf-8').splitlines()]
cohort = {r['problem_id']: r['fresh6h_primary_tag'] for r in json.loads((REPO / 'explore/W9b/sham1/COHORT.json').read_bytes())['selected']}
res, rows = s.analyse(draws, cohort, np.random.default_rng(s.SEED))
ref = json.loads((OUT / 'RESULT.json').read_bytes())


def diff(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            if k not in a or k not in b: out.append(path + '/' + k + ' missing')
            else: diff(a[k], b[k], path + '/' + k, out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)): diff(x, y, f'{path}/{i}', out)
    elif isinstance(a, float) or isinstance(b, float):
        if a is None or b is None or not math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-15): out.append(f'{path}: {a} vs {b}')
    elif a != b: out.append(f'{path}: {a!r} vs {b!r}')


bad = []
diff(json.loads(json.dumps(res)), {k: ref[k] for k in res}, '', bad)
diff(json.loads(json.dumps(rows)), ref['per_original'], '/per_original', bad)
P, C1, C2, T1, E = res['PRIMARY_solve_vs_sham'], res['CAL1_base_minus_sham'], res['CAL2_sham_z'], res['T1_joint'], res['E_eligible_T1']
print(f"draws {len(draws)}  problems {res['originals']}  waves {res['waves']}")
print(f"PRIMARY solve loss, rewrites vs identical copies: {P['est']:.3f} [{P['ci95'][0]:.3f}, {P['ci95'][1]:.3f}]  ({P['est']!r})")
print(f"CAL1 original minus copies: {C1['est']:.4f} [{C1['ci95'][0]:.4f}, {C1['ci95'][1]:.4f}]  ({C1['est']!r})")
print(f"CAL2 share |z|>1.96: {C2['share_abs_z_gt_1_96']:.4f} of {C2['tests']} tests ({C2['reading']});  reading: {res['PRIMARY_reading']}")
print(f"T1 eligible: {E['n']} problems ({100 * E['share']:.1f}%)")
print(f"T1 fragile rate, copies: {T1['sham']['est']:.3f} [{T1['sham']['ci95'][0]:.3f}, {T1['sham']['ci95'][1]:.3f}];"
      f"  real rewrites: {T1['real']['est']:.3f} [{T1['real']['ci95'][0]:.3f}, {T1['real']['ci95'][1]:.3f}]")
print('compared with the scorer output RESULT.json:', 'ALL MATCH' if not bad else f'{len(bad)} MISMATCHES')
for b in bad[:20]: print('  ', b)
sys.exit(1 if bad else 0)
