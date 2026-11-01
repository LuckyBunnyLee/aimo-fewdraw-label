"""W9b numbers (t090) for report draft v0.9 (R8 must-fixes 4 and GL7). Two stored values, no new computation:
- dc_E_base_plug: the base-only mean excess before bias correction (DECOMP RESULT.json /B1/plug_in/E_base), beside the
  existing dc_E_pool_plug, so the text can show both corrections.
- sh_n0_ref: the sham calibration reference, mean plug-in N0 at each original's base accuracy over all its numeric base
  draws (SHAM-PHASE0-RESULT.json /mean_N0; sham_phase0.py line 26 uses N0(p_b) with no correction).
Reads only sha-pinned outputs; writes numbers/w9b-t090.json (exclusive create).
usage: python -I pair/aimo/report/numbers/make_w9b_t090.py
"""
import hashlib, json
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
DC, SH = 'explore/W9b/decomp/RESULT.json', 'explore/W9b/decomp/SHAM-PHASE0-RESULT.json'
manifest, src = {}, {}
for rel in (DC, SH):
    p = ROOT / rel; b = p.read_bytes(); manifest[str(p)] = hashlib.sha256(b).hexdigest(); src[rel] = json.loads(b.decode('utf-8-sig'))
dc, sh = src[DC], src[SH]
assert round(dc['B1']['plug_in']['E_pool'], 3) == 0.043  # same file as the existing dc_E_pool_plug
assert round(sh['P0_1_false_fragility']['est'] - sh['mean_N0'], 6) == round(sh['P0_3_sham_minus_N0']['est'], 6)
v = dict(dc_E_base_plug=round(dc['B1']['plug_in']['E_base'], 3), sh_n0_ref=round(sh['mean_N0'], 3))
ptr = dict(dc_E_base_plug=DC + ' :: /B1/plug_in/E_base; 3 dp', sh_n0_ref=SH + ' :: /mean_N0 (plug-in N0 at all-wave numeric base accuracy); 3 dp')
out = HERE / 'w9b-t090.json'
with open(out, 'x', encoding='utf-8') as fh:
    json.dump(dict(tier='Exploratory; stored values, no new computation; W9b t090 producer for report v0.9.',
                   values=v, raw_pointers=ptr, _manifest=manifest), fh, indent=1, ensure_ascii=False)
print(v, hashlib.sha256(out.read_bytes()).hexdigest())
