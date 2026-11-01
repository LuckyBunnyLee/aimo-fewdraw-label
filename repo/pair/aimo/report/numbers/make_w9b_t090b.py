"""W9b numbers (t090b) for report draft v0.9: counts from the R8 blind referee's number checks, for Appendix A.
Reads only explore/R8/NUMBER-CHECKS.json (sha-pinned in the manifest); writes numbers/w9b-t090b.json (exclusive create).
usage: python -I pair/aimo/report/numbers/make_w9b_t090b.py
"""
import hashlib, json
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
R8 = 'explore/R8/NUMBER-CHECKS.json'
p = ROOT / R8; b = p.read_bytes(); h = hashlib.sha256(b).hexdigest(); r8 = json.loads(b.decode('utf-8-sig'))
ch = r8['checks']
v = dict(r8_checks=len(ch), r8_match=sum(c['status'] == 'MATCH' for c in ch),
         r8_indep=sum(c['basis'] == 'independent draw/formula recomputation' for c in ch))
ptr = dict(r8_checks=R8 + ' :: /checks: count', r8_match=R8 + ' :: /checks: status MATCH',
           r8_indep=R8 + ' :: /checks: basis "independent draw/formula recomputation"')
out = HERE / 'w9b-t090b.json'
with open(out, 'x', encoding='utf-8') as fh:
    json.dump(dict(tier='Exploratory; counts of a referee check ledger; W9b t090b producer for report v0.9.',
                   values=v, raw_pointers=ptr, _manifest={str(p): h}), fh, indent=1, ensure_ascii=False)
print(v, hashlib.sha256(out.read_bytes()).hexdigest())
