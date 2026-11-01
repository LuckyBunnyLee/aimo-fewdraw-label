"""AR1 numbers (t105b) for report v1.2d: leaderboard sensitivity asked for by the second blind referee (expected teams at 100%
under other assumed true accuracies). Stored values from AM1's board simulation; no new computation.
Writes numbers/ar1-t105b.json (exclusive create). usage: python -I pair/aimo/report/numbers/make_ar1_t105b.py
"""
import hashlib, json
from pathlib import Path

ROOT = Path(r'E:/work/research-cycle')
HERE = Path(__file__).resolve().parent
BN = 'explore/AM1-aimo/out/board_noise.json'
p = ROOT / BN; b = p.read_bytes(); manifest = {str(p): hashlib.sha256(b).hexdigest()}
e = json.loads(b.decode('utf-8-sig'))['expected_teams_at_100pct_of_95']
v = {'lb_perfect_060_10': round(e['p0.6_m10'], 2), 'lb_perfect_070_10': round(e['p0.7_m10'], 2)}
ptr = {'lb_perfect_060_10': BN + ' :: /expected_teams_at_100pct_of_95/p0.6_m10; 2 dp',
       'lb_perfect_070_10': BN + ' :: /expected_teams_at_100pct_of_95/p0.7_m10; 2 dp'}
out = HERE / 'ar1-t105b.json'
with open(out, 'x', encoding='utf-8') as fh:
    json.dump(dict(tier='Leaderboard simulation (AM1 board_noise.json), stored values; AR1 t105b producer for report v1.2d.',
                   values=v, raw_pointers=ptr, _manifest=manifest), fh, indent=1, ensure_ascii=False)
print(json.dumps(v), hashlib.sha256(out.read_bytes()).hexdigest())
