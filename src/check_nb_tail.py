"""Check the Model 2 tail claim: where does the negative binomial tail overtake the Poisson tail?

For X ~ NB(mean mu, shape k) and Y ~ Poisson(mu), S(x) = P(X >= x) - P(Y >= x) changes sign once,
from negative to positive, at x*. Below x* the Poisson tail can be the heavier one.
Adds the key nb_tail_check to results.json; changes no other key. Run after src/analysis.py.
"""
import json
import pathlib

import numpy as np
from scipy import stats
from scipy.special import logsumexp

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOG10 = np.log(10)


def nb(mu, k):
    return stats.nbinom(k, k / (k + mu))


def crossing(mu, k):
    """Smallest x >= 1 with S(x) > 0, and the number of sign changes of S."""
    x = np.arange(1, int(mu + 60 * np.sqrt(mu) + 200))
    s = nb(mu, k).sf(x - 1) - stats.poisson(mu).sf(x - 1)
    sign = np.sign(s[s != 0])
    return int(x[np.argmax(s > 0)]), int(np.sum(sign[1:] != sign[:-1]))


def log10_tail(dist, x, width=200000):
    """log10 P(X >= x) from the log-pmf, since sf underflows to 0 far in the tail."""
    return float(logsumexp(dist.logpmf(np.arange(x, x + width))) / LOG10)


R = json.load(open(ROOT / "results.json"))
out = {}

# (a) counterexample to "for x > mu, P_NB(X >= x) >= P_Pois(X >= x)"
out["counterexample"] = {"mu": 1, "k": 1, "x": 2,
                         "nb_tail": float(nb(1, 1).sf(1)), "poisson_tail": float(stats.poisson(1).sf(1))}

# (b) crossing point on a grid
out["grid"] = []
for mu in [0.5, 1, 5, 20, 100]:
    for k in [0.1, 1, 10, 100]:
        xs, n_changes = crossing(mu, k)
        out["grid"].append({"mu": mu, "k": k, "x_star": xs, "sign_changes": n_changes,
                            "x_star_minus_mu_over_sd": (xs - mu) / np.sqrt(mu)})

# (c) the report's setting: 52-day window, k by method of moments from the pre-decade daily dispersion,
#     summed over independent days (NB shapes add at fixed p)
p = R["poisson"]
T = p["expected_in_window"] / p["rate_per_day"]
k_daily = p["rate_per_day"] / (p["dispersion_pre_decade_daily"] - 1)
mu, k, x_obs = p["expected_in_window"], k_daily * T, p["observed"]
xs, n_changes = crossing(mu, k)
out["report_setting"] = {"window_days": T, "mu": mu, "k_daily": k_daily, "k_window": k,
                         "x_star": xs, "sign_changes": n_changes, "observed": x_obs,
                         "log10_nb_tail": log10_tail(nb(mu, k), x_obs),
                         "log10_poisson_tail": log10_tail(stats.poisson(mu), x_obs)}

R["nb_tail_check"] = out
json.dump(R, open(ROOT / "results.json", "w"), indent=1, default=str)

print("counterexample  NB %.4f < Poisson %.4f" % (out["counterexample"]["nb_tail"], out["counterexample"]["poisson_tail"]))
for g in out["grid"]:
    print("mu %5g  k %5g  x* %4d  sign changes %d  (x*-mu)/sqrt(mu) %.2f"
          % (g["mu"], g["k"], g["x_star"], g["sign_changes"], g["x_star_minus_mu_over_sd"]))
r = out["report_setting"]
print("report: mu %.3f  k %.3f  x* %d  observed %d  log10 tail NB %.1f  Poisson %.1f"
      % (r["mu"], r["k_window"], r["x_star"], r["observed"], r["log10_nb_tail"], r["log10_poisson_tail"]))
