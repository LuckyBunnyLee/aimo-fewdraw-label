"""AM1 27 Oct: how much can a 14-case public board separate teams?

Inputs: the public leaderboard JSON read 26 Oct 23:17 PT (E:/research-cycle/am1-aimo/leaderboards-20261026.json),
the site's baseline values (small 0.50, main 0.52), and our label-reliability numbers from report v1.0.
Model: a team's methods each have true accuracy p on the hidden population. On a board of n cases a
method's score is Binomial(n, p)/n, and the board shows each team's best of m submissions. Errors of a
team's m submissions are taken as independent, which overstates the selection gain if they are similar.
Seeded and deterministic. Writes out/board_noise.json.
"""
import json
from math import comb
from pathlib import Path
import numpy as np

OUT = Path(__file__).parent / "out" / "board_noise.json"
LB = Path("E:/research-cycle/am1-aimo/leaderboards-20261026.json")
rng = np.random.default_rng(1945)


def binom_ci(n, p):
    """Central 95% range of the observed score when the true accuracy is p."""
    cdf, lo, hi = 0.0, None, None
    for k in range(n + 1):
        cdf += comb(n, k) * p ** k * (1 - p) ** (n - k)
        if lo is None and cdf >= 0.025:
            lo = k / n
        if hi is None and cdf >= 0.975:
            hi = k / n
    return [round(lo, 3), round(hi, 3)]


def p_outrank(n, p1, p2, B=200000):
    a = rng.binomial(n, p1, B); b = rng.binomial(n, p2, B)
    return {"strictly_above": float((a > b).mean()), "tie": float((a == b).mean())}


def expected_perfect(n, p, m, teams):
    """Expected number of teams showing 100% when each submits m independent tries at true p."""
    one = p ** n
    return teams * (1 - (1 - one) ** m)


def main():
    lb = json.loads(LB.read_text())
    small = [r["accuracy"] for r in lb["leaderboards"]["small"]]
    res = {"board": {"small_teams": len(small), "small_n_cases": 14,
                     "small_perfect": sum(a == 1.0 for a in small),
                     "small_at_or_below_baseline_0.50": sum(a <= 0.5 for a in small),
                     "main_teams": len(lb["leaderboards"]["main"]), "main_n_cases": 21,
                     "last_updated_at": lb["last_updated_at"]}}
    res["score_range_95_n14"] = {str(p): binom_ci(14, p) for p in [0.5, 0.6, 0.7, 0.8, 0.9]}
    res["score_range_95_n21"] = {str(p): binom_ci(21, p) for p in [0.5, 0.6, 0.7, 0.8]}
    res["outrank_n14"] = {f"{p1}_vs_{p2}": p_outrank(14, p1, p2)
                          for p1, p2 in [(0.6, 0.5), (0.7, 0.6), (0.8, 0.7), (0.7, 0.5)]}
    res["expected_teams_at_100pct_of_95"] = {f"p{p}_m{m}": round(expected_perfect(14, p, m, 95), 2)
                                             for p in [0.6, 0.65, 0.7, 0.75] for m in [1, 5, 10, 20]}
    # label reliability ceiling on our own endpoint (report v1.0, thinking-on repeat):
    # kappa 0.386, pooled fragile rate 0.092 -> chance agreement pe, observed agreement po
    k, f = 0.386, 0.092
    pe = f * f + (1 - f) * (1 - f)
    res["label_repeat_agreement_own_endpoint"] = {"kappa": k, "fragile_rate": f, "pe": round(pe, 3),
                                                  "po": round(k * (1 - pe) + pe, 3)}
    OUT.write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
