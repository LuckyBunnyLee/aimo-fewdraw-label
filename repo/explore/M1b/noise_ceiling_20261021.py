"""Noise ceiling for single-wave strict-n4 NR labels on READY63 (exploratory, CPU only, numpy/scipy).

Question 1: how high can ANY predictor's AUC go against ONE strict-n4 label run, when the label is a noisy
draw from each original's NR probability? An oracle that knows each original's P(NR | binary wave) is scored
against single waves; we report the distribution over waves.
Question 2: how many repeat waves are needed before a 0.05 gain in mean per-wave AUC is detectable at 80% power?

Inputs: raw records on D: (parsed exactly as in the M1b v7.6 re-derivation, which matched the scorer's DRAWS.jsonl
with 0 mismatches), REQUESTS/TRUTHS, frozen X3-64 V2 predictions, the scorer's RESULT.json (cross-check only).
Read-only. Writes only argv[1] (RESULT json).
"""
import collections
import hashlib
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy import optimize, special, stats

E = Path("E:/work/research-cycle/explore")
D = Path("D:/research-cycle/cl-ready63-reliability-20261020-1740")
CL = E / "CL-5070-recovery-20261020-1740/ready63-reliability"
PRED = E / "X3/afternoon-20261020/64/PREDICTIONS-V2-BEFORE-FRESH-OUTCOMES.json"
RES = E / "W9b/ready63rel/out/RESULT.json"
OUT = Path(sys.argv[1])
SEED = 20261021
FAM = ["base", "surface_gs", "surface_dlm"]
W = 100


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------- parse raw records (copied from the v7.6 re-derivation) ----------------
requests = json.loads((CL / "REQUESTS.json").read_text(encoding="utf-8"))
truths = json.loads((CL / "TRUTHS.json").read_text(encoding="utf-8"))
req = {r["identity_sha256"]: r for r in requests}
assert len(req) == 40800
recdir = D / "block-1792543703210030707" / "records"
files = sorted(p for p in recdir.iterdir() if p.suffix == ".json")
rec_digest = hashlib.sha256()
draws = {}
for p in files:
    b = p.read_bytes()
    rec_digest.update(p.name.encode() + b"\0" + hashlib.sha256(b).digest())
    r = json.loads(b)["record"]
    key = r["identity_sha256"]
    assert key in req and key not in draws and str(r["seed"]) == str(req[key]["seed"])
    assert r["output_tokens"] == len(r["token_ids"]) and hashlib.sha256(r["raw"].encode()).hexdigest() == r["raw_sha256"]
    finish, err, raw = r["finish_reason"], r["error"], r["raw"]
    status, correct = "invalid", 0
    if finish in ("length", "max_tokens", "context_limit"):
        status = "truncated"
    elif err is not None:
        status = "error"
    elif finish in ("stop", "eos"):
        lines = raw.rsplit("</think>", 1)[-1].strip().splitlines()
        m = re.fullmatch(r"ANSWER:\s*(.*?)\s*", lines[-1]) if lines else None
        if m:
            try:
                status, correct = "numeric", int(Fraction(m[1].replace(",", "")) == Fraction(str(truths[key])))
            except (ValueError, ZeroDivisionError):
                status = "abstain" if m[1] == "NaN" else "invalid"
    i = req[key]["identity"]
    draws[key] = dict(pid=i["problem_id"], family=i["family"], rep=i["replicate"], status=status, correct=correct)
assert len(draws) == 40800

cells = collections.defaultdict(list)
for k, d in draws.items():
    cells[(d["pid"], d["family"])].append((d["rep"], d))
pids = sorted({d["pid"] for d in draws.values()})


def tag(c):
    if any(x["status"] != "numeric" for f in FAM for x in c[f]):
        return "UNUSABLE"
    s = {f: sum(x["correct"] for x in c[f]) for f in FAM}
    if s["base"] == 0:
        return "FLOOR"
    return "NR" if min(s["surface_gs"], s["surface_dlm"]) < s["base"] else "R"


tags = {}
for p in pids:
    for w in range(W):
        c = {f: [d for rep, d in sorted(cells[(p, f)], key=lambda t: t[0]) if 1000 + 4 * w <= rep <= 1003 + 4 * w] for f in FAM}
        assert all(len(c[f]) == 4 for f in FAM)
        tags[(p, w)] = tag(c)

# ---------------- predictor scores ----------------
pred = json.loads(PRED.read_text(encoding="utf-8"))
prow = {r["pid"]: r for r in pred["rows"] if r["pid"] in pids}
assert len(prow) == 34
PREDS = ["interaction-A4", "point-K", "RF-length-source|alltrain", "LR-text|alltrain"]
score = {m: {p: round(float(prow[p]["NR_scores"][m]), 12) for p in pids} for m in PREDS}
score["char-length (unfitted, longer=NR)"] = {p: float(len(prow[p]["problem"])) for p in pids}
PRED_ALL = list(score)


def auc(y, s):
    y, s = np.asarray(y, bool), np.asarray(s, float)
    pos, neg = s[y], s[~y]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    return ((pos[:, None] > neg[None, :]).sum() + 0.5 * (pos[:, None] == neg[None, :]).sum()) / (len(pos) * len(neg))


def wave_rows(w, plist=pids):
    rows = [p for p in plist if tags[(p, w)] in ("NR", "R")]
    return rows, np.array([tags[(p, w)] == "NR" for p in rows])


# cross-check against the scorer: mean per-wave AUC gain A4 - point-K
obs = {m: np.array([auc(y, [score[m][p] for p in rows]) for rows, y in (wave_rows(w) for w in range(W))]) for m in PRED_ALL}
gain_obs = obs["interaction-A4"] - obs["point-K"]
scorer = json.loads(RES.read_text(encoding="utf-8"))
assert abs(np.nanmean(gain_obs) - scorer["primary"]["observed"]) < 1e-12, (np.nanmean(gain_obs), scorer["primary"]["observed"])
assert abs(np.nanmean(obs["RF-length-source|alltrain"]) - scorer["endpoints"]["strict_n4"]["observed"]["RF-length-source|alltrain"]["mean_AUC"]) < 1e-12

# ---------------- per-original NR probability ----------------
nb = np.array([sum(tags[(p, w)] in ("NR", "R") for w in range(W)) for p in pids])     # binary waves
nnr = np.array([sum(tags[(p, w)] == "NR" for w in range(W)) for p in pids])
q_hat = np.where(nb > 0, nnr / np.maximum(nb, 1), np.nan)                               # P(NR | binary)
b_hat = nb / W                                                                           # P(binary)
use = nb > 0
pooled = nnr.sum() / nb.sum()


# empirical-Bayes beta-binomial prior for q over originals with >=1 binary wave
def nll(t):
    a, b = np.exp(t)
    k, n = nnr[use], nb[use]
    return -np.sum(special.betaln(k + a, n - k + b) - special.betaln(a, b))


fit = optimize.minimize(nll, np.log([1.0, 1.0]), method="Nelder-Mead", options=dict(xatol=1e-10, fatol=1e-12, maxiter=20000))
alpha, beta = np.exp(fit.x)
q_eb = np.where(use, (nnr + alpha) / (nb + alpha + beta), np.nan)

# draw-level iid check: per original-family accuracy and usable rate -> predicted P(NR | binary)
def pred_q_iid(p):
    acc, okr = {}, {}
    for f in FAM:
        ds = [d for _, d in cells[(p, f)]]
        num = [d for d in ds if d["status"] == "numeric"]
        okr[f] = len(num) / len(ds)
        acc[f] = np.mean([d["correct"] for d in num]) if num else 0.0
    pb = stats.binom.pmf(np.arange(5), 4, acc["base"])
    cg = stats.binom.cdf(np.arange(5) - 1, 4, acc["surface_gs"])        # P(s_gs < k)
    cd = stats.binom.cdf(np.arange(5) - 1, 4, acc["surface_dlm"])
    p_nr = sum(pb[k] * (1 - (1 - cg[k]) * (1 - cd[k])) for k in range(1, 5))
    p_r = sum(pb[k] * (1 - cg[k]) * (1 - cd[k]) for k in range(1, 5))
    p_usable = np.prod([okr[f] ** 4 for f in FAM])
    return p_nr / (p_nr + p_r) if p_nr + p_r > 0 else np.nan, p_usable * (p_nr + p_r)


iid = np.array([pred_q_iid(p) for p in pids])
iid_q, iid_b = iid[:, 0], iid[:, 1]

# overdispersion of binary-wave outcomes across waves (wave order effects): runs over waves per original
def runs_z(seq):
    seq = np.asarray(seq)
    n1, n0 = seq.sum(), len(seq) - seq.sum()
    if n1 == 0 or n0 == 0:
        return np.nan
    r = 1 + np.sum(seq[1:] != seq[:-1])
    mu = 2 * n1 * n0 / (n1 + n0) + 1
    var = 2 * n1 * n0 * (2 * n1 * n0 - n1 - n0) / ((n1 + n0) ** 2 * (n1 + n0 - 1))
    return (r - mu) / np.sqrt(var)


rz = np.array([runs_z([tags[(p, w)] == "NR" for w in range(W) if tags[(p, w)] in ("NR", "R")]) for p in pids])
rz = rz[~np.isnan(rz)]

# ---------------- Q1: oracle ceiling ----------------
idx = {p: i for i, p in enumerate(pids)}


def summ(x):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    pc = np.percentile(x, [2.5, 10, 25, 50, 75, 90, 97.5])
    return dict(n=int(len(x)), mean=float(x.mean()), sd=float(x.std(ddof=1)), min=float(x.min()),
                p2_5=float(pc[0]), p10=float(pc[1]), p25=float(pc[2]), median=float(pc[3]), p75=float(pc[4]),
                p90=float(pc[5]), p97_5=float(pc[6]), max=float(x.max()))


orc_in, orc_loo, orc_loo_eb = [], [], []
for w in range(W):
    rows, y = wave_rows(w)
    ii = [idx[p] for p in rows]
    orc_in.append(auc(y, q_hat[ii]))
    # leave-this-wave-out: q estimated from the other 99 waves only
    k = nnr[ii] - y
    n = nb[ii] - 1
    orc_loo.append(auc(y, np.where(n > 0, k / np.maximum(n, 1), pooled)))
    orc_loo_eb.append(auc(y, (k + alpha) / (n + alpha + beta)))
orc_in, orc_loo, orc_loo_eb = map(np.array, (orc_in, orc_loo, orc_loo_eb))

# parametric: true q_i drawn from the EB posterior each simulated wave; oracle knows the drawn q_i
rng = np.random.default_rng(SEED)
NSIM = 20000
ui = np.where(use)[0]


def sim_waves(nsim, scores_fn):
    """Simulate nsim single waves; returns AUC per wave for each scorer returned by scores_fn(q_true)."""
    out = collections.defaultdict(list)
    for _ in range(nsim):
        qt = rng.beta(alpha + nnr[ui], beta + nb[ui] - nnr[ui])
        binary = rng.random(len(ui)) < b_hat[ui]
        y = rng.random(len(ui)) < qt
        for name, s in scores_fn(qt).items():
            out[name].append(auc(y[binary], s[binary]))
    return {k: np.array(v) for k, v in out.items()}


sim1 = sim_waves(NSIM, lambda qt: {"oracle_true_q": qt, **{m: np.array([score[m][pids[i]] for i in ui]) for m in PRED_ALL}})
# idealised: binary every wave for every usable original (removes the varying-subset noise)
b_save = b_hat.copy()
b_hat = np.where(use, 1.0, 0.0)
sim_allbin = sim_waves(5000, lambda qt: {"oracle_true_q": qt})
b_hat = b_save

# ceiling against a label aggregated over k waves (majority NR among binary waves), oracle = true q
def sim_kwave(k, nsim=3000):
    a = []
    for _ in range(nsim):
        qt = rng.beta(alpha + nnr[ui], beta + nb[ui] - nnr[ui])
        nbin = rng.binomial(k, b_hat[ui])
        knr = rng.binomial(nbin, qt)
        ok = nbin > 0
        y = knr[ok] * 2 > nbin[ok]
        tie = knr[ok] * 2 == nbin[ok]
        y = np.where(tie, rng.random(ok.sum()) < 0.5, y)
        a.append(auc(y, qt[ok]))
    return summ(a)


kwave = {k: sim_kwave(k) for k in (1, 3, 5, 11, 25)}

# ---------------- observed predictors vs the ceiling ----------------
cmp = {}
for m in PRED_ALL:
    o = obs[m]
    cmp[m] = dict(per_wave=summ(o),
                  frac_of_ceiling_loo=float((np.nanmean(o) - 0.5) / (np.nanmean(orc_loo) - 0.5)),
                  waves_at_or_above_oracle_loo=int(np.nansum(o >= orc_loo)),
                  sim_single_wave_given_eb_truth=summ(sim1[m]))
cmp["gain_A4_minus_pointK"] = summ(gain_obs)
cmp["headroom_oracle_loo_minus_pointK"] = summ(orc_loo - obs["point-K"])

# ---------------- Q2: power for a 0.05 gain in mean per-wave AUC ----------------
z = stats.norm.ppf(0.975) + stats.norm.ppf(0.80)
DELTA = 0.05
sd_w = float(np.nanstd(gain_obs, ddof=1))
# (a) conditional on these 34 originals: waves are the only random unit; waves treated as independent
w_cond = float((z * sd_w / DELTA) ** 2)
# lag-1 autocorrelation of per-wave gains (independence check)
g = gain_obs[~np.isnan(gain_obs)]
ac1 = float(np.corrcoef(g[:-1], g[1:])[0, 1])

# (b) originals random as well (what the prereg original bootstrap targets): SE^2(Wn) = A + B/Wn, empirical two-stage
B2 = 2000
WGRID = [1, 2, 4, 10, 25, 50, 100]
per_wave_orig = {}   # cache per (wave) AUCs for resampled original lists is too costly; resample directly
se_emp = {}
A4, PK = score["interaction-A4"], score["point-K"]
for Wn in WGRID:
    vals = []
    for _ in range(B2):
        plist = [pids[i] for i in rng.integers(0, len(pids), len(pids))]
        ws = rng.integers(0, W, Wn) if Wn < W else np.arange(W)
        gs = []
        for w in ws:
            rows = [p for p in plist if tags[(p, w)] in ("NR", "R")]
            y = np.array([tags[(p, w)] == "NR" for p in rows])
            a = auc(y, [A4[p] for p in rows])
            if not np.isnan(a):
                gs.append(a - auc(y, [PK[p] for p in rows]))
        if gs:
            vals.append(np.mean(gs))
    se_emp[Wn] = float(np.std(vals, ddof=1))
# fit SE^2 = A + B/W by least squares on the grid
Xf = np.array([[1.0, 1.0 / w] for w in WGRID])
coef, *_ = np.linalg.lstsq(Xf, np.array([se_emp[w] ** 2 for w in WGRID]), rcond=None)
A_var, B_var = (float(c) for c in coef)


def power(se):
    return float(stats.norm.cdf(DELTA / se - stats.norm.ppf(0.975)))


pow_grid = {Wn: power(np.sqrt(max(A_var, 0) + B_var / Wn)) for Wn in [1, 4, 10, 25, 100, 1000, 10**6]}
target = (DELTA / z) ** 2
w_needed_34 = (B_var / (target - A_var)) if target > A_var else None


# originals needed (variance scales as 34/n, an extrapolation) for several wave counts
def n_needed(Wn):
    return float(34 * (A_var + B_var / Wn) / target)


n_need = {Wn: n_needed(Wn) for Wn in [1, 4, 10, 100, 10**6]}

res = dict(
    scope="EXPLORATORY noise-ceiling analysis of READY63 strict-n4 single-wave NR labels; not preregistered; CPU only",
    seed=SEED, script_sha256=sha(__file__),
    inputs_sha256={str(CL / "REQUESTS.json"): sha(CL / "REQUESTS.json"), str(CL / "TRUTHS.json"): sha(CL / "TRUTHS.json"),
                   str(PRED): sha(PRED), str(RES): sha(RES),
                   "records_dir_digest(sorted name+sha256 of 40800 files)": rec_digest.hexdigest()},
    crosscheck=dict(primary_gain_matches_scorer=True, rf_length_auc_matches_scorer=True,
                    mean_gain=float(np.nanmean(gain_obs)), scorer_primary=scorer["primary"]["observed"]),
    originals=dict(n=len(pids), with_binary_wave=int(use.sum()), binary_waves=nb.tolist(), nr_waves=nnr.tolist(),
                   q_hat=[None if np.isnan(x) else float(x) for x in q_hat], pooled_nr=float(pooled),
                   q_hat_summary=summ(q_hat), n_q_ge_0_9=int(np.nansum(q_hat >= 0.9)), n_q_le_0_1=int(np.nansum(q_hat <= 0.1)),
                   n_q_between_0_3_0_7=int(np.nansum((q_hat > 0.3) & (q_hat < 0.7))),
                   eb_prior=dict(alpha=float(alpha), beta=float(beta), prior_mean=float(alpha / (alpha + beta)),
                                 prior_sd=float(np.sqrt(alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1))))),
                   mean_binary_per_wave=float(np.mean([len(wave_rows(w)[0]) for w in range(W)]))),
    iid_draw_check=dict(corr_q_hat_vs_iid=float(np.corrcoef(q_hat[use & ~np.isnan(iid_q)], iid_q[use & ~np.isnan(iid_q)])[0, 1]),
                        max_abs_diff_q=float(np.nanmax(np.abs(q_hat[use] - iid_q[use]))),
                        mean_abs_diff_q=float(np.nanmean(np.abs(q_hat[use] - iid_q[use]))),
                        corr_b_hat_vs_iid=float(np.corrcoef(b_hat, iid_b)[0, 1]),
                        runs_test_z=summ(rz), runs_abs_z_gt_1_96=int(np.sum(np.abs(rz) > 1.96)), runs_tested=int(len(rz))),
    oracle_single_wave=dict(in_sample=summ(orc_in), leave_wave_out=summ(orc_loo), leave_wave_out_eb=summ(orc_loo_eb),
                            parametric_eb_truth=summ(sim1["oracle_true_q"]),
                            parametric_eb_truth_all_binary=summ(sim_allbin["oracle_true_q"])),
    oracle_vs_k_wave_majority_label=kwave,
    observed_predictors=cmp,
    power=dict(delta=DELTA, alpha_two_sided=0.05, target_power=0.80,
               per_wave_gain_sd=sd_w, lag1_autocorr_gain=ac1,
               conditional_on_34_originals=dict(waves_needed=w_cond, note="waves as the only random unit"),
               originals_random=dict(se_empirical_by_waves=se_emp, var_fit=dict(A_originals=A_var, B_wave=B_var),
                                     power_at_34_originals=pow_grid, waves_needed_at_34=w_needed_34,
                                     originals_needed_by_waves=n_need, se_needed=float(DELTA / z))),
)
OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps({k: res[k] for k in ("crosscheck", "oracle_single_wave", "power")}, indent=1))
