"""Check every measured number in the report against the released files.

The report's build manifest (repo/pair/aimo/report/REPORT-DRAFT-v1.4e.build.json) lists each of the 419 \\result
values with the numbers file, sha256 and JSON pointer it came from, and a scope string naming the upstream result
file and pointer that the numbers file copied it from. This script checks, for every value:
  1. stored: the released numbers file has the pinned sha256, and the pointer gives the printed value;
  2. upstream: where the scope names a released JSON file and a plain JSON pointer with "N dp", that file
     (sha-pinned in the manifest) gives the same value at N decimals.
Values whose scope is an expression over upstream fields (a difference, count or percent), a post hoc rebuild, a
constructed number or a file not in this release are checked at level 1 only; they are counted separately. CPU, seconds.
usage: python repro/check_numbers.py      (from the release root)
"""
import collections, hashlib, json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1] / 'repo'
ABS = 'E:\\work\\research-cycle\\'
B = json.loads((REPO / 'pair/aimo/report/REPORT-DRAFT-v1.4e.build.json').read_bytes())
pins = {k.replace(ABS, '').replace('\\', '/'): v['sha256'] for k, v in B['inputs'].items()}
local = lambda p: REPO / p.replace(ABS, '').replace('\\', '/')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
cache = {}


def load(p):
    if p not in cache: cache[p] = json.loads(p.read_text(encoding='utf-8-sig'))
    return cache[p]


def ptr(doc, pointer):
    for part in pointer.strip('/').split('/'):
        part = part.replace('~1', '/').replace('~0', '~')
        doc = doc[int(part)] if isinstance(doc, list) else doc[part]
    return doc


def close(a, b, tol):
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, bool) or isinstance(b, bool) or not all(isinstance(x, (int, float)) for x in (a, b)):
        return a == b
    return abs(a - b) <= tol


SCOPE = re.compile(r'^[^:]+:\s*(?P<path>[^:{}*]+?\.json)\s*::\s*(?P<ptr>/[^\s;]*);\s*(?P<dp>\d)\s*dp$')
count, fails = collections.Counter(), []
for key, m in B['measured_keys'].items():
    src = local(m['source'])
    rel = m['source'].replace(ABS, '').replace('\\', '/')
    if not src.exists(): fails.append(f'{key}: numbers file not in release ({rel})'); continue
    if sha(src) != m['sha256']: fails.append(f'{key}: {rel} sha differs from the build manifest'); continue
    if not close(ptr(load(src), m['pointer']), m['value'], 0): fails.append(f'{key}: stored value differs'); continue
    count['stored ok'] += 1
    g = SCOPE.match(m['scope'])
    up = REPO / g['path'].strip() if g else None
    if not g or not up.exists():
        count['upstream not machine-checked (scope is an expression, count, percent or post hoc rebuild, or its file is not released)'] += 1; continue
    if g['path'].strip() in pins and sha(up) != pins[g['path'].strip()]:
        fails.append(f'{key}: upstream {g["path"]} sha differs from the build manifest'); continue
    try:
        v = ptr(load(up), g['ptr'])
    except (KeyError, IndexError, ValueError, TypeError):
        count['upstream not checked (pointer is not a plain JSON pointer)'] += 1; continue
    dp = int(g['dp'])
    rnd = [round(x, dp) for x in v] if isinstance(v, list) and all(isinstance(x, (int, float)) for x in v) else round(v, dp) if isinstance(v, (int, float)) and not isinstance(v, bool) else v
    if close(rnd, m['value'], 0.5 * 10 ** -dp + 1e-9): count['upstream ok'] += 1
    else: fails.append(f'{key}: upstream {g["path"]}{g["ptr"]} = {v!r}, printed {m["shown"]}')
print(len(B['measured_keys']), 'measured values in the report')
for k, n in count.items(): print(f'  {n:4d}  {k}')
print('FAILURES:', len(fails))
for f in fails: print('  ', f)
sys.exit(1 if fails else 0)
