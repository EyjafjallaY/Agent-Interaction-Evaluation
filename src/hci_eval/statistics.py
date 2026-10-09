"""Reviewed analysis primitives adapted from archived study notebooks.
See docs/provenance.md and docs/methods.md for version boundaries.
"""
import math
import numpy as np
import pandas as pd
from scipy import stats


def fit_mixedlm(formula, data, maxiter=200, var_thresh=1e-6, sort_rows=False):
    """Retain ML/lbfgs and historical fallback; expose convergence without changing it."""
    import warnings
    import statsmodels.formula.api as smf
    if sort_rows:
        data = data.sort_values(["Participant_ID", "Condition01"]).copy()
    attempts = []
    for structure in ["1+Condition01", "1"]:
        attempt = {"structure":structure, "warnings":[], "converged":False}
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                model = smf.mixedlm(formula, data=data, groups=data["Participant_ID"], re_formula=structure)
                result = model.fit(reml=False, method="lbfgs", maxiter=maxiter, disp=False)
                attempt["converged"] = bool(result.converged)
                variance = float(result.cov_re.iloc[1,1]) if structure == "1+Condition01" else np.nan
                attempt["slope_variance"] = variance
                attempt["fallback"] = bool(structure == "1+Condition01" and np.isfinite(variance) and variance < var_thresh)
            except Exception as exc:
                result = None
                variance = np.nan
                attempt["error"] = type(exc).__name__
                attempt["fallback"] = structure == "1+Condition01"
        attempt["warnings"] = [str(w.message) for w in caught]
        attempts.append(attempt)
        if result is not None and not attempt["fallback"]:
            diagnostic = {"re_structure_used":structure, "Var_u1":variance,
                          "converged":attempt["converged"], "attempts":attempts,
                          "note":"fallback_to_random_intercept" if structure == "1" else ""}
            return result, diagnostic
    return None, {"re_structure_used":"fail", "Var_u1":np.nan, "converged":False,
                  "attempts":attempts, "note":"fit_failed"}

def bh_fdr(pvals):
    p = np.array(pvals, dtype=float)
    out = np.full_like(p, np.nan)
    mask = ~np.isnan(p)
    pv = p[mask]
    m = len(pv)
    if m == 0:
        return out
    order = np.argsort(pv)
    ranked = pv[order]
    adj = ranked * m / (np.arange(1, m+1))
    adj = np.minimum.accumulate(adj[::-1])[::-1]  # monotone
    adj = np.clip(adj, 0, 1)
    out_idx = np.where(mask)[0][order]
    out[out_idx] = adj
    return out

def holm_bonferroni(pvals):
    p = np.array(pvals, dtype=float)
    out = np.full_like(p, np.nan)
    mask = ~np.isnan(p)
    pv = p[mask]
    m = len(pv)
    if m == 0:
        return out
    order = np.argsort(pv)
    ranked = pv[order]
    adj = (m - np.arange(m)) * ranked
    adj = np.maximum.accumulate(adj)  # monotone non-decreasing
    adj = np.clip(adj, 0, 1)
    out_idx = np.where(mask)[0][order]
    out[out_idx] = adj
    return out

def wald_combo(beta_vec, cov_mat, L):
    """
    Wald test for linear combination L' beta.
    L: dict param_name -> weight
    """
    est = 0.0
    for k, w in L.items():
        est += w * beta_vec.get(k, np.nan)

    var = 0.0
    for k1, w1 in L.items():
        for k2, w2 in L.items():
            if (k1 in cov_mat.index) and (k2 in cov_mat.columns):
                var += w1*w2*cov_mat.loc[k1, k2]
            else:
                return (np.nan, np.nan, np.nan, np.nan, np.nan, np.nan)

    if var < 0:
        var = np.nan
    se = math.sqrt(var) if not pd.isna(var) else np.nan
    if pd.isna(est) or pd.isna(se) or se == 0:
        return (float(est), float(se), np.nan, np.nan, np.nan, np.nan)

    z = est / se
    p = 2*(1 - stats.norm.cdf(abs(z)))
    ci_low = est - 1.96*se
    ci_high = est + 1.96*se
    return (float(est), float(se), float(z), float(p), float(ci_low), float(ci_high))
