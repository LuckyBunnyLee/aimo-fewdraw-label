"""PREREG-FRESH6H section 3: frozen scores for the 2,657 roster originals, before any record is read.
Function source is lifted verbatim (ast) from the hash-bound X3 scripts; sklearn is replaced only inside point-K by a scipy LR."""
import ast, hashlib, json, math, re, sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import softmax, expit, logsumexp
from scipy.stats import rankdata

E = Path('E:/work/research-cycle/explore'); X = E / 'X3'; O = X / 'afternoon-20261020'; JOB = Path('D:/research-cycle/cl-fresh6h-20261021-0935')
OUT = E / 'W9b/fresh6h/PREDICTIONS-BEFORE-RECORDS.json'
H = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
BOUND = {
    E / 'W9b/PREREG-FRESH6H-20261021.md': 'f0aec861ac491f886b52b0d32867f20869b1603fc9771493798a075b29bcaf5c',
    JOB / 'ROSTER.json': 'b75af74ab88518e448950a49a089ba7d3af67c0aa038406115fc673241d9b05d',
    O / '64/PREDICTIONS-V2-BEFORE-FRESH-OUTCOMES.json': '833f74c8d34a2450831f1f1f30c07c29180e9f691d41087997566cc8ad4d90bb',
    O / '56/MODEL-PARAMETERS-FROZEN.json': '7360901b7d38a95c4d0eddc9d134465f476a795613925a30ebbeb85bd1194d7e',
    O / '56/FREEZE.json': 'ec02fdaaf217a7ea8f36398cd37bd94cc2fbc8ec4e3e91e2a3bc9a1cdeb11445',
    O / '56/ALL128-PREDICTIONS-BEFORE-THIS-JOIN.json': '7c1e1ccde2ffecdb5dc6228d30e4bcb054d2fcbc4fd593642bc843be43fd6e1e',
    O / '52/PREDICTIONS-BEFORE-THIS-JOIN.json': '0bb99188084ce114aef48b1d65c21fe1e88e0acc375e18027d35046a2bf41a6f',
    O / '49/DATA.json': '868aadad0dc235310b18ce864d28da87db35c064a58a869a8dbd987f7315cba6',
    X / 'run40_20261020.py': '46e3ceea038654e2c9376ded5d95a7fb749fcdc68573a75da29895dc63b77b7b',
    X / 'run52_20261020.py': 'ee29ba60ebeb62a742130d417084d4dbbc1c1bcf0406b8ee3bcb7f946f659530',
    X / 'run64_20261020.py': 'fd4f66ec6edabd0997e05f5cad353bd1382fdaa065cc1d767b101cc93569a24d',
    X / 'correct64_20261020.py': '7236f4abeda30e61f538061525f1e95b74e4ae113fe3fb1f5b2072ff35582102',
    X / 'sparse-repro-20261020/LABELS-AND-OOF.json': '18d2cea7ebe9207a1d3cbea0c0704abe5563fe0ace5b63327ceea9953191e78c',
    X / 'harder-packs-20261020/READY-01-mid-hard/REQUESTS.json': '490c120b18da687168182ca5bbf389e9f4e71bf2a1d97547a95f288072914791',
    Path('D:/research-cycle/cl-long6h-20261019/block-1792421061073452544/PLAN.json'): 'f04abbb9a9aee323ec70f0285613c475a0bfba258a139a34e4579fd9a87209bc',
}
for p, h in BOUND.items(): assert H(p) == h, f'ABORT hash {p}'
assert not OUT.exists(), 'predictions already written'
read = lambda p: json.loads(Path(p).read_bytes())

def lift(path, names):
    src = Path(path).read_text(encoding='utf8'); tree = ast.parse(src); out = []
    for node in tree.body:
        nm = node.name if isinstance(node, ast.FunctionDef) else (node.targets[0].id if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) else None)
        if nm in names: out.append(ast.get_source_segment(src, node))
    assert len(out) == len(names), (path, names, len(out)); return '\n'.join(out)

class LogisticRegression:  # scipy stand-in for sklearn lbfgs L2 LR (point-K only); minimizes C*sum(CE) + 0.5*||W||^2, intercept unpenalized
    def __init__(self, C=1, solver='lbfgs', max_iter=1000, **kw): self.C = C
    def fit(self, Xm, y):
        self.classes_ = np.unique(y); k = len(self.classes_); n, d = Xm.shape; Y = (y[:, None] == self.classes_[None]).astype(float)
        if k == 2:
            t = Y[:, 1]
            def fg(w):
                z = Xm @ w[:d] + w[d]; f = self.C * np.sum(np.logaddexp(0, z) - t * z) + 0.5 * w[:d] @ w[:d]; r = self.C * (expit(z) - t)
                return f, np.concatenate((Xm.T @ r + w[:d], [r.sum()]))
            w = minimize(fg, np.zeros(d + 1), jac=True, method='L-BFGS-B', options=dict(maxiter=100000, gtol=1e-13, ftol=1e-16)).x; self.w2 = w
        else:
            def fg(w):
                W = w[:k * d].reshape(k, d); b = w[k * d:]; Z = Xm @ W.T + b; L = logsumexp(Z, axis=1); P = np.exp(Z - L[:, None])
                f = self.C * np.sum(L - np.sum(Y * Z, axis=1)) + 0.5 * np.sum(W * W); R = self.C * (P - Y)
                return f, np.concatenate(((R.T @ Xm + W).ravel(), R.sum(0)))
            w = minimize(fg, np.zeros(k * d + k), jac=True, method='L-BFGS-B', options=dict(maxiter=100000, gtol=1e-13, ftol=1e-16)).x; self.W = w[:k * d].reshape(k, d); self.b = w[k * d:]
        return self
    def predict_proba(self, Xm):
        if len(self.classes_) == 2: p = expit(Xm @ self.w2[:-1] + self.w2[-1]); return np.column_stack((1 - p, p))
        return softmax(Xm @ self.W.T + self.b, axis=1)

ns = dict(np=np, re=re, math=math, softmax=softmax, expit=expit, rankdata=rankdata, read=read, O=O, LogisticRegression=LogisticRegression)
exec(lift(X / 'run40_20261020.py', ['TOPICS', 'TASK', 'features']), ns)
exec(lift(X / 'run52_20261020.py', ['tag', 'decode', 'trainpredict']), ns)
exec(lift(X / 'run64_20261020.py', ['infer56']), ns)
features, infer56, trainpredict = ns['features'], ns['infer56'], ns['trainpredict']

roster = read(JOB / 'ROSTER.json')['selected']; assert len(roster) == 2657 and all(r['members'][0]['family'] == 'base' for r in roster)
fresh = [r['members'][0]['problem'] for r in roster]
old128 = [r['problem'] for r in read(X / 'harder-packs-20261020/READY-01-mid-hard/REQUESTS.json') if r['identity']['family'] == 'base' and r['identity']['replicate'] == 0]
v2 = read(O / '64/PREDICTIONS-V2-BEFORE-FRESH-OUTCOMES.json')['rows']; t38 = [r['problem'] for r in v2]; assert len(old128) == 128 and len(v2) == 38
alltexts = old128 + t38 + fresh
nrs = lambda q: q[:, 1] / np.maximum(1 - q[:, 2], 1e-12)

# interaction-A4: frozen 56 weights, no refit; parity gate
q56 = infer56(alltexts, read(O / '56/MODEL-PARAMETERS-FROZEN.json'))['interaction-A4']
prior = read(O / '56/ALL128-PREDICTIONS-BEFORE-THIS-JOIN.json')
par128 = float(np.max(np.abs(q56[:128] - [r['probs']['interaction-A4-decode4'] for r in prior])))
par38 = float(np.max(np.abs(nrs(q56[128:166]) - [r['NR_scores']['interaction-A4'] for r in v2])))
print('interaction-A4 parity old128', par128, 'v2-38', par38)
assert par128 < 1e-7 and par38 < 1e-7, 'ABORT interaction-A4 parity failed'
a4 = nrs(q56[166:])

# point-K: literal correct64 reconstruction with the scipy LR; parity gate 1e-6, else not computable (no abort)
pk = None; pk_parity = None
try:
    old = read(O / '49/DATA.json')['old']; meta = {(r['source'], r['pid']): r for r in read(X / 'sparse-repro-20261020/LABELS-AND-OOF.json') if r['n'] == 4}
    tm = {(q['identity']['protocol'], q['identity']['problem_id']): q['problem'] for q in read('D:/research-cycle/cl-long6h-20261019/block-1792421061073452544/PLAN.json')['requests'] if q['identity']['family'] in ['base', 'simple']}
    cats = sorted({r['source'] for r in old}); xo = np.array([features(tm[meta[r['source'], r['pid']]['protocol'], r['pid']]) + [float(r['source'] == s) for s in cats] for r in old])
    K = np.array([len(r['families']) - 1 for r in old]); A = np.zeros((len(old), int(K.max()) + 1))
    for i, r in enumerate(old): A[i, :len(r['A'])] = r['A']
    xt = np.array([features(t) + [0.] * len(cats) for t in alltexts])
    pr = trainpredict(xo, A, K, np.arange(len(old)), xt, np.full(len(xt), 2), 'point-K', list(range(xo.shape[1] - len(cats), xo.shape[1])))
    p52 = read(O / '52/PREDICTIONS-BEFORE-THIS-JOIN.json')['new']
    pk_parity = dict(old128=float(np.max(np.abs(pr[:128] - [r['probs']['point-K'] for r in p52]))), v2_38=float(np.max(np.abs(nrs(pr[128:166]) - [r['NR_scores']['point-K'] for r in v2]))))
    print('point-K parity', pk_parity)
    if max(pk_parity.values()) < 1e-6: pk = nrs(pr[166:])
except Exception as exc:
    pk_parity = dict(error=repr(exc)); print('point-K not computable', exc)

rows = [dict(pid=r['problem_id'], text_sha256=hashlib.sha256(t.encode()).hexdigest(), words=len(t.split()), **{'interaction-A4': float(a), 'point-K': (float(pk[i]) if pk is not None else None)})
        for i, (r, t, a) in enumerate(zip(roster, fresh, a4))]
OUT.write_text(json.dumps(dict(prereg_sha256=BOUND[E / 'W9b/PREREG-FRESH6H-20261021.md'], script_sha256=H(__file__), parity_interactionA4=dict(old128=par128, v2_38=par38),
                               parity_pointK=pk_parity, pointK_computable=pk is not None, n=len(rows), no_records_read=True, rows=rows), indent=1), encoding='utf8', newline='\n')
print('wrote', OUT, H(OUT))
