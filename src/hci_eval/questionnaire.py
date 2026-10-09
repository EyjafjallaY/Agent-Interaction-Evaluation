"""Reviewed analysis primitives adapted from archived study notebooks.
See docs/provenance.md and docs/methods.md for version boundaries.
"""
import re
import numpy as np
import pandas as pd

TRAITS = ["E","A","C","N","O"]

COND_LABELS = {
    1: {1:"Free gaze", 2:"Focus gaze"},
    2: {1:"Keep", 2:"Let go"},
    3: {1:"Competitive", 2:"Cooperative"},
    4: {1:"Extrovert agent", 2:"Introvert agent"},
}

DIM_MAP = {
    1: {
        "Anthropomorphism":[1,2],
        "Psychological Engagement / Co-presence":[3,6,7],
        "Perceived Quality":[10,11,12],
        "Comfort":[4,5,8],
    },
    2: {
        "Anthropomorphism":[1,7],
        "Psychological Engagement / Co-presence":[8],   # single-item dimension
        "Perceived Quality":[2,3,6,9,10],
        "Interruption appropriateness":[4,5],
        "Independent question":[11],                    # single-item DV
    },
    3: {
        "Anthropomorphism":[1,8,11],
        "Psychological Engagement / Co-presence":[9,10],
        "Perceived Quality":[5,7,12,13,14],
        "Interruption appropriateness":[2,3,4],
        "Independent question":[6],                     # single-item DV
    },
    4: {
        "Anthropomorphism":[1,7],
        "Psychological Engagement / Co-presence":[2,4],
        "Perceived Quality":[5,8,11],
        "Comfort":[6,9,10],
        "Independent question":[3],                     # single-item DV
    }
}

IGNORE_ITEMS = {(1,9)}

OFFENSIVE_ITEMS = {(2,2),(3,5)}

def sanitize_name(s):
    s = s.strip()
    s = re.sub(r"[^\w]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s

def cronbach_alpha(X):
    """
    Cronbach's alpha for a dataframe X with rows=observations, cols=items.
    Drops rows with any missing values.
    """
    X = X.dropna(axis=0, how="any")
    k = X.shape[1]
    if k < 2 or X.shape[0] < 2:
        return np.nan

    item_vars = X.var(ddof=1, axis=0)
    total = X.sum(axis=1)
    total_var = total.var(ddof=1)
    if total_var == 0 or np.isnan(total_var):
        return np.nan

    return (k / (k - 1)) * (1 - item_vars.sum() / total_var)

def build_dv_long(df_in, score_col="Score_star"):
    base_cols = ["Participant_ID","Original_Phase","Condition","Condition01","Condition_label",
                 "Order_Sequence","Sequence01","Gender","Gender_F","Age"] + TRAITS + [f"{t}_c" for t in TRAITS]
    d0 = df_in[base_cols + ["Question", score_col]].copy()
    d0["Question"] = d0["Question"].astype(int)

    wide = d0.pivot_table(index=base_cols, columns="Question", values=score_col, aggfunc="mean")
    wide.columns = [int(c) for c in wide.columns]
    wide = wide.reset_index()

    out_rows = []
    for phase, dims in DIM_MAP.items():
        w_phase = wide[wide["Original_Phase"]==phase].copy()
        if w_phase.empty:
            continue
        for dim_name, items in dims.items():
            items = [int(x) for x in items]
            for item in items:
                if item not in w_phase:
                    w_phase[item] = np.nan
            k = len(items)
            if k >= 2:
                valid = w_phase.dropna(subset=items, how="any").copy()
            else:
                valid = w_phase.dropna(subset=items, how="all").copy()
            if valid.empty:
                continue
            dv_val = valid[items].mean(axis=1)
            dv_name = f"P{phase}_{sanitize_name(dim_name)}"
            tmp = valid[base_cols].copy()
            tmp["Dimension"] = dim_name
            tmp["DV"] = dv_name
            tmp["k_items"] = int(k)
            tmp["DV_value"] = dv_val.values
            out_rows.append(tmp)

    return pd.concat(out_rows, ignore_index=True) if out_rows else pd.DataFrame()


def preprocess_questionnaire(raw):
    """Keep original question numbering and raw scores; center traits per person."""
    from .validation import validate_questionnaire, participant_covariates
    validate_questionnaire(raw)
    df = raw.copy()
    df["Participant_ID"] = df["Participant_ID"].astype(str)
    df = df[~df.apply(lambda r: (int(r.Original_Phase), int(r.Question)) in IGNORE_ITEMS, axis=1)].copy()
    df["Condition01"] = df["Condition"].map({1:0, 2:1})
    df["Sequence01"] = df["Order_Sequence"].map({1:0, 2:1})
    df["Gender_F"] = df["Gender"].map({"M":0, "F":1})
    df["Score_raw"] = pd.to_numeric(df["Score"])
    df["Score_star"] = df["Score_raw"]
    mask = df.apply(lambda r: (int(r.Original_Phase), int(r.Question)) in OFFENSIVE_ITEMS, axis=1)
    df.loc[mask, "Score_star"] = 8.0 - df.loc[mask, "Score_raw"]
    means = participant_covariates(df)[TRAITS].mean()
    for t in TRAITS:
        df[f"{t}_c"] = df[t].astype(float) - float(means[t])
    df["Condition_label"] = df.apply(lambda r: COND_LABELS[int(r.Original_Phase)][int(r.Condition)], axis=1)
    return df


def reliability_table(prepared):
    """Historical pooled participant-by-condition alpha; not independent-person alpha."""
    rows = []
    for phase, dims in DIM_MAP.items():
        ph = prepared[prepared.Original_Phase == phase]
        if ph.empty:
            continue
        for name, items in dims.items():
            x = ph.pivot(index=["Participant_ID", "Condition"], columns="Question", values="Score_star")
            x = x.reindex(columns=items).dropna()
            rows.append({"Original_Phase":phase, "Dimension":name, "k_items":len(items),
                         "n_obs":len(x), "alpha":cronbach_alpha(x),
                         "unit":"participant x condition; pooled", "single_item":len(items)==1})
    return pd.DataFrame(rows)
