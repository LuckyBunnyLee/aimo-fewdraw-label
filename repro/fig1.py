"""Redraw report Figure 1 by running the exact figure script (repo/pair/aimo/report/fig1_tag_null_sham_v4b.py)
with its machine-specific paths pointed at this folder. Only those path lines change; every check and plotting line
runs as written. Output: repro/out/fig1_tag_null_sham_v4b.png (+ .sha256); the released PNG is not touched.
The PNG bytes match the report's figure only with the same matplotlib version and fonts (requirements.txt);
the printed means and problem count do not depend on them.
usage: python -B repro/fig1.py      (from the release root)
"""
import hashlib, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1] / 'repo'
OUTDIR = Path(__file__).resolve().parent / 'out'
SCRIPT = REPO / 'pair/aimo/report/fig1_tag_null_sham_v4b.py'
REPORT_PNG_SHA = '781974c38833a8086213c4faa9b6e3c400ce4aef568ced52670d7ce95f3a508a'  # repo/pair/aimo/report/fig1_tag_null_sham_v4b.sha256
RES_KEY = r'E:\work\research-cycle\from-box\research\W9d\sham1-score\tree\explore\W9b\sham1\v1.1\out\RESULT.json'

src = SCRIPT.read_text(encoding='utf-8')
for a, b in [("ROOT = Path(r'E:/work/research-cycle')", 'ROOT = REPO'),
             ("HERE = Path(__file__).resolve().parent", "HERE = REPO / 'pair/aimo/report'"),
             ("num['_manifest'][str(RES).replace('/', '\\\\')]", 'num[\'_manifest\'][RES_KEY]'),
             ("out = HERE / 'fig1_tag_null_sham_v4b.png'", "out = OUTDIR / 'fig1_tag_null_sham_v4b.png'"),
             ("(HERE / 'fig1_tag_null_sham_v4b.sha256')", "(OUTDIR / 'fig1_tag_null_sham_v4b.sha256')")]:
    assert src.count(a) == 1, a
    src = src.replace(a, b)
OUTDIR.mkdir(exist_ok=True)
exec(compile(src, str(SCRIPT), 'exec'), dict(__name__='__main__', REPO=REPO, OUTDIR=OUTDIR, RES_KEY=RES_KEY))
h = hashlib.sha256((OUTDIR / 'fig1_tag_null_sham_v4b.png').read_bytes()).hexdigest()
import matplotlib
print('matplotlib', matplotlib.__version__, '| PNG', 'IDENTICAL to the report figure' if h == REPORT_PNG_SHA else 'differs in bytes from the report figure (compare visually)')
