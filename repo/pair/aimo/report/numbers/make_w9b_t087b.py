"""W9b numbers (t087b) for report draft v0.8: splits w9b-t087's top3_even_bin list into three scalars so the text can say
"0, 1 and 4" (the builder joins lists with "to"). Reads only the sha-pinned numbers file; writes numbers/w9b-t087b.json (exclusive create).
usage: python -I pair/aimo/report/numbers/make_w9b_t087b.py
"""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / 'w9b-t087.json'
b = SRC.read_bytes(); h = hashlib.sha256(b).hexdigest()
assert h == '17ea69b658ca1502af0d7c9d9a878cfc2f985020c29c7803d14c6ed0c2cd8957', 'w9b-t087 changed'
nb = json.loads(b.decode('utf-8'))['values']['top3_even_bin']
assert len(nb) == 3
v = {f'top3_even_bin_{i + 1}': x for i, x in enumerate(nb)}
ptr = {k: f'pair/aimo/report/numbers/w9b-t087.json :: /values/top3_even_bin[{i}] (binary even waves of the {"first second third".split()[i]}-largest mean loss)' for i, k in enumerate(v)}
out = HERE / 'w9b-t087b.json'
with open(out, 'x', encoding='utf-8') as fh:
    json.dump(dict(tier='Exploratory; split of an existing key, no new computation; W9b t087b producer for report v0.8.',
                   values=v, raw_pointers=ptr, _manifest={str(SRC): h}), fh, indent=1, ensure_ascii=False)
print(v, hashlib.sha256(out.read_bytes()).hexdigest())
