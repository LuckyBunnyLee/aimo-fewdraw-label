"""W9b numbers (t086) for report draft v0.7: populations, denominators and sensitivity facts the R6 referee asked
to see in the main text. Nothing is re-run or rescored; every value is read or counted from sha-pinned outputs:
- explore/W9b/decomp/SHAM-PHASE0-RESULT.json (per-original binary-triple counts and tag-state counts)
- explore/W9b/decomp/RESULT.json (plug-in pooled excess, rank-correlation difference, implied kappa, contrast counts)
- explore/X3/READY63-reviewed-MATH-20261020/MANIFEST.json and MEMBERS-WITH-PROOFS.json (how the repeat cohort was built)
- explore/R6/NUMBER-CHECKS.json (the blind referee's independent recomputation)
Writes numbers/w9b-t086.json (exclusive create). No models, GPU, network or sealed data.
usage: python -I pair/aimo/report/numbers/make_w9b_t086.py
"""
import hashlib, json, re
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
SH, DC = 'explore/W9b/decomp/SHAM-PHASE0-RESULT.json', 'explore/W9b/decomp/RESULT.json'
MAN, MEM = 'explore/X3/READY63-reviewed-MATH-20261020/MANIFEST.json', 'explore/X3/READY63-reviewed-MATH-20261020/MEMBERS-WITH-PROOFS.json'
R6 = 'explore/R6/NUMBER-CHECKS.json'
PIN = {SH: '7cbdc2f0c899ea72ad40e5726c6f8dde1d627f00e4e027572feeece3b92d7b91',
       DC: 'f70423eb7b03d70ac5252fdaee8464705b802cd0a3dc8b3d66127d3bb12ace0f',
       MAN: '96540a3a0281004d0b1e1795ec0c979da68dd88d5bd13378fea6b141826a3cfd',
       MEM: '1b27513c326e7c084c95f5921123d0c957764865804bc3e926b61e483954756d',
       R6: '2906e8812d6551679fb8e5d403461f11a5fb08fbbc6ff40e432b0425b95a0cf1'}
manifest = {}


def raw(rel):
    p = ROOT / rel; b = p.read_bytes(); h = hashlib.sha256(b).hexdigest()
    assert h == PIN[rel], rel + ' changed'
    manifest[str(p)] = h
    return json.loads(b.decode('utf-8-sig'))


sh, dc, man, mem, r6 = raw(SH), raw(DC), raw(MAN), raw(MEM), raw(R6)
v, ptr = {}, {}


def put(k, val, pointer, src):
    assert k not in v, k
    v[k] = val; ptr[k] = src + ' :: ' + pointer


# ---- sham denominators and tag states (29 used originals) ----
excl = set(sh['excluded'])
used = [r for r in sh['per_original'] if r['pid'] not in excl]
assert len(used) == sh['n_used'] == 29
put('sh_bin_real', sum(r['n_real_binary'] for r in used), '/per_original (used): sum n_real_binary', SH)
put('sh_bin_sham', sum(r['n_sham_binary'] for r in used), '/per_original (used): sum n_sham_binary', SH)
put('sh_n_fewer_real', sum(r['n_real_binary'] < r['n_sham_binary'] for r in used), '/per_original (used): count n_real_binary < n_sham_binary', SH)
ex = [r for r in used if r['pid'] == 'deepmathgap-dmgap_005881'][0]
put('sh_ex_real', ex['n_real_binary'], '/per_original[dmgap_005881]/n_real_binary', SH)
put('sh_ex_sham', ex['n_sham_binary'], '/per_original[dmgap_005881]/n_sham_binary', SH)
tot = 33 * len(used)
assert all(sum(r['real_counts'].values()) == 33 == sum(r['sham_counts'].values()) for r in used)
for arm in ('real', 'sham'):
    for st in ('NR', 'R', 'UNUSABLE', 'FLOOR'):
        put(f'sh_state_{arm}_{st.lower()}', round(100 * sum(r[f'{arm}_counts'].get(st, 0) for r in used) / tot, 1),
            f'/per_original (used): pooled share of {st} among all {arm} triples, %; 1 dp', SH)
put('sh_triples_all', tot, '/per_original (used): 33 triples x 29', SH)

# ---- DECOMP extras ----
put('dc_E_pool_plug', round(dc['B1']['plug_in']['E_pool'], 3), '/B1/plug_in/E_pool; 3 dp', DC)
put('dc_rho_diff_ci', [round(a, 2) for a in dc['B2']['diff_base_minus_pool_ci']['ci95']], '/B2/diff_base_minus_pool_ci/ci95; 2 dp', DC)
put('dc_kappa_impl_n0', round(dc['B5']['kappa_implied_N0_base'], 3), '/B5/kappa_implied_N0_base; 3 dp', DC)
D1 = dc['D']['D1']['solve']
put('dc_contrasts', 2 * D1['n'], '/D/D1/solve/n x 2 rewrites', DC)
per = D1['per_original']
assert sum(1 for x in per for k in ('z_gs', 'z_dlm') if x[k] is not None) == D1['n_tests']
put('dc_zero_se', 2 * D1['n'] - D1['n_tests'], '/D/D1/solve: contrasts with zero standard error (z undefined)', DC)
odd = [x['odd']['base'][1] for x in dc['per_original']]
assert max(odd) == 200  # odd counts are numeric draws only; 50 odd waves x 4 draws when every draw is numeric
put('dc_odd_waves', max(odd) // 4, '/per_original/odd/base: max numeric draws / 4 (spec: odd/even wave split)', DC)
neb = [x['n_even_binary'] for x in dc['per_original']]
put('dc_even_bin_min', min(neb), '/per_original/n_even_binary: min over the 29', DC)
put('dc_even_bin_max', max(neb), '/per_original/n_even_binary: max over the 29', DC)
top = sorted(per, key=lambda r: -r['delta_edit'])[:3]
put('dc_top_mean_drop', round(top[0]['delta_edit'], 2), '/D/D1/solve/per_original: largest delta_edit (mean of both rewrites); 2 dp', DC)
put('dc_top3_min_mean_drop', round(top[2]['delta_edit'], 2), '/D/D1/solve/per_original: third-largest delta_edit; 2 dp', DC)
assert abs(D1['var_delta_hat'] - D1['mean_se2'] - D1['tau'] ** 2) < 1e-9

# ---- how the repeat cohort was built ----
m = re.search(r'(\d+)independentderivations beforepublisherkeyjoin;(\d+)matches;(\d+)equivalentpriororiginalsexcluded;(\d+)admitted', man['key_audit'])
assert m and int(m[4]) == man['ready_originals'] == len(mem) == 34
put('ready_derived', int(m[1]), '/key_audit: independent derivations before key join', MAN)
put('ready_matched', int(m[2]), '/key_audit: matches', MAN)
put('ready_dupes', int(m[3]), '/key_audit: equivalent prior originals excluded', MAN)
put('ready_families', len(man['template_families']), '/template_families: count', MAN)
diffs = sorted(float(d) for d in man['publisher_difficulty'])
put('ready_diff_min', diffs[0], '/publisher_difficulty: min key', MAN); put('ready_diff_max', diffs[-1], '/publisher_difficulty: max key', MAN)
assert all(x['key_match'] and x['certificate']['check'].startswith('inverse alpha rename') for x in mem)
put('ready_certified', sum(x['certificate']['check'].startswith('inverse alpha rename') for x in mem), 'members: inverse-rename certificates', MEM)

# ---- blind referee recomputation ----
put('r6_checks', len(r6['checks']), '/checks: count', R6)
put('r6_match', sum(c['status'] == 'MATCH' for c in r6['checks']), '/checks: status MATCH', R6)
put('r6_draws', r6['n_draws'], '/n_draws', R6)

out = HERE / 'w9b-t086.json'
with open(out, 'x', encoding='utf-8') as fh:
    json.dump(dict(tier='Exploratory; counts and fields read from outputs already analysed (no rerun, no rescore); '
                        'W9b t086 producer for report v0.7.',
                   values=v, raw_pointers=ptr, _manifest=manifest), fh, indent=1, ensure_ascii=False)
print(len(v), 'keys ->', out, hashlib.sha256(out.read_bytes()).hexdigest())
for k, x in v.items(): print(k, x)
