"""Condition and personality models with explicit notebook correction families."""
import json
import numpy as np
import pandas as pd
from .statistics import fit_mixedlm, wald_combo, bh_fdr, holm_bonferroni
from .validation import ECSCW_PHASE, TRAITS


def _effect(result, weights):
    if result is None:
        return dict(zip(["beta","SE","z","p","CI95_low","CI95_high"], [np.nan]*6))
    if len(weights) == 1 and next(iter(weights.values())) == 1:
        term = next(iter(weights))
        beta, se, p = (float(s.get(term,np.nan)) for s in [result.params,result.bse,result.pvalues])
        return {"beta":beta,"SE":se,"z":beta/se if se > 0 else np.nan,"p":p,
                "CI95_low":beta-1.96*se,"CI95_high":beta+1.96*se}
    return dict(zip(["beta","SE","z","p","CI95_low","CI95_high"], wald_combo(result.params, result.cov_params(), weights)))


def fit_models(long, modality, maxiter=200):
    if modality not in ["questionnaire", "openface"]:
        raise ValueError("unknown modality")
    groups = ["Original_Phase", "DV"] + (["metric"] if modality == "openface" else [])
    condition_rows, trait_rows = [], []
    for _, g in long.groupby(groups, sort=True):
        phase, dv = int(g.Original_Phase.iloc[0]), g.DV.iloc[0]
        base = {"modality":modality, "Original_Phase":phase, "ECSCW_Phase":ECSCW_PHASE[phase], "DV":dv}
        if modality == "openface":
            base["metric"] = g.metric.iloc[0]
        if modality == "questionnaire":
            base["Dimension"] = g.Dimension.iloc[0]
        for trait in [None] + TRAITS:
            required = ["DV_value","Condition01","Age","Gender_F","Sequence01","Participant_ID"]
            if trait:
                required.append(trait + "_c")
            data = g.dropna(subset=required).copy()
            n_people, n_obs = data.Participant_ID.nunique(), len(data)
            formula = "DV_value ~ Condition01 + Age + Gender_F + Sequence01"
            if trait:
                tc = trait + "_c"
                formula = f"DV_value ~ Condition01 + {tc} + Condition01:{tc} + Age + Gender_F + Sequence01"
            diagnostic = {"re_structure_used":"fail","Var_u1":np.nan,"converged":False,"attempts":[], "note":"insufficient_data"}
            result = None
            if n_people >= 3 and n_obs >= 6:
                result, diagnostic = fit_mixedlm(formula, data, maxiter=maxiter, sort_rows=modality == "openface")
            shared = base | {"N_participants":int(n_people), "N_obs":n_obs, "formula":formula,
                            **{k:v for k,v in diagnostic.items() if k != "attempts"},
                            "diagnostics":json.dumps([{k:(None if isinstance(v,float) and not np.isfinite(v) else v)
                                                        for k,v in a.items()} for a in diagnostic["attempts"]], allow_nan=False)}
            if trait is None:
                condition_rows.append(shared | {"Effect":"condition", **_effect(result,{"Condition01":1})})
            else:
                inter = "Condition01:" + tc
                for effect, weights in [("slope_cond1",{tc:1}), ("slope_cond2",{tc:1,inter:1}), ("interaction",{inter:1})]:
                    trait_rows.append(shared | {"Trait":trait,"Effect":effect, **_effect(result,weights)})
    condition = pd.DataFrame(condition_rows)
    trait_table = pd.DataFrame(trait_rows)
    if condition.empty:
        raise ValueError("No complete outcomes could be constructed")
    c_family = ["Original_Phase"] + (["metric"] if modality == "openface" else [])
    t_family = ["Original_Phase", "Effect"] + (["metric","Trait"] if modality == "openface" else ["DV"])
    for table, family, adjust, method in [(condition,c_family,holm_bonferroni,"holm"), (trait_table,t_family,bh_fdr,"fdr_bh")]:
        table["p_adjusted"] = np.nan
        table["correction"] = method
        table["family_columns"] = ",".join(family)
        table["n_tests_finite"] = 0
        for _, idx in table.groupby(family, sort=True).groups.items():
            table.loc[idx,"p_adjusted"] = adjust(table.loc[idx,"p"].to_numpy())
            table.loc[idx,"n_tests_finite"] = int(table.loc[idx,"p"].notna().sum())
        finite = np.isfinite(table["beta"]) & np.isfinite(table["SE"]) & (table["SE"] > 0)
        # Keep numerical outputs, but require review of every warned fit before interpretation.
        warned = table.diagnostics.map(lambda x: any(a.get("warnings") for a in json.loads(x)))
        table["fit_review_required"] = ~table.converged | ~finite | warned
        table["adjusted_p_below_05"] = table.p_adjusted < .05
        table["significant_usable"] = table.adjusted_p_below_05 & ~table.fit_review_required
    return condition, trait_table
