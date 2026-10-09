"""Explicit schema checks. Invalid identities and joins must not disappear silently."""
import numpy as np
import pandas as pd

TRAITS = ["E", "A", "C", "N", "O"]
PERSON_COLUMNS = ["Age", "Gender"] + TRAITS
ECSCW_PHASE = {1:1, 2:2, 3:None, 4:3}


def require_columns(df, columns, name):
    missing = sorted(set(columns) - set(df.columns))
    if missing:
        raise ValueError(f"{name}: missing columns {missing}")
    if df.empty:
        raise ValueError(f"{name}: empty input")


def numeric(df, columns, name, allow_missing=False):
    for col in columns:
        values = pd.to_numeric(df[col], errors="coerce")
        bad = values.isna() & df[col].notna() if allow_missing else values.isna()
        bad |= values.notna() & ~np.isfinite(values)
        if bad.any():
            raise ValueError(f"{name}: nonnumeric, missing or nonfinite {col}")


def validate_keys(df, name, extra):
    require_columns(df, ["Participant_ID", "Original_Phase", "Condition"] + extra, name)
    if df.Participant_ID.isna().any() or df.Participant_ID.astype(str).str.strip().eq("").any():
        raise ValueError(f"{name}: missing Participant_ID")
    if not df.Original_Phase.isin([1,2,3,4]).all():
        raise ValueError(f"{name}: Original_Phase must use original numbering 1..4")
    if not df.Condition.isin([1,2]).all():
        raise ValueError(f"{name}: Condition must be 1 or 2")
    if df.duplicated(["Participant_ID", "Original_Phase", "Condition"] + extra).any():
        raise ValueError(f"{name}: duplicate record key")


def participant_covariates(df):
    require_columns(df, ["Participant_ID"] + PERSON_COLUMNS, "metadata")
    if (df.groupby("Participant_ID")[PERSON_COLUMNS].nunique(dropna=False) > 1).any().any():
        raise ValueError("metadata: inconsistent person-level covariates")
    return df[["Participant_ID"] + PERSON_COLUMNS].drop_duplicates("Participant_ID").copy()


def validate_questionnaire(df):
    require_columns(df, ["Participant_ID","Original_Phase","Condition","Question","Score", "Order_Sequence"] + PERSON_COLUMNS, "questionnaire")
    validate_keys(df, "questionnaire", ["Question"])
    numeric(df, ["Question","Score","Age"] + TRAITS, "questionnaire")
    if not df.Score.between(1,7).all():
        raise ValueError("questionnaire: raw Score must be in 1..7; do not submit already reversed scores")
    if not (df.Question >= 1).all() or not (df.Question % 1 == 0).all():
        raise ValueError("questionnaire: Question must be a positive original item number")
    maxima = df.Original_Phase.map({1:12, 2:11, 3:14, 4:11})
    if (df.Question > maxima).any():
        raise ValueError("questionnaire: item number exceeds the original phase questionnaire")
    if not df.Gender.isin(["M","F"]).all():
        raise ValueError("questionnaire: archived model expects Gender M/F; other coding needs an explicit method revision")
    if not df.Order_Sequence.isin([1,2]).all():
        raise ValueError("questionnaire: Order_Sequence must be 1 or 2")
    participant_covariates(df)
    if (df.groupby(["Participant_ID","Original_Phase"]).Order_Sequence.nunique() > 1).any():
        raise ValueError("questionnaire: inconsistent phase-level order sequence")


def validate_frames(df):
    from .openface import AU_COMPUTE
    validate_keys(df, "frames", ["timestamp"])
    require_columns(df, AU_COMPUTE, "frames")
    numeric(df, ["timestamp"], "frames")
    numeric(df, AU_COMPUTE, "frames", allow_missing=True)
    if (df.timestamp < 0).any():
        raise ValueError("frames: timestamp must be nonnegative seconds")
    for au in AU_COMPUTE:
        if (df[au].notna() & ~df[au].between(0,5)).any():
            raise ValueError(f"frames: {au} intensity must be 0..5 or missing")


def validate_events(df):
    require_columns(df, ["Participant_ID","Original_Phase","Condition","start","interruption"], "events")
    validate_keys(df, "events", ["start"])
    numeric(df, ["start","interruption"], "events")
    if (df.start < 0).any() or not df.interruption.isin([0,1]).all():
        raise ValueError("events: nonnegative seconds and binary interruption are required")
