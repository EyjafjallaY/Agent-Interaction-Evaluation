"""Quality observations without silently filtering research inputs."""
import pandas as pd


def quality_summary(questionnaire, frames, events):
    session = ["Participant_ID","Original_Phase","Condition"]
    keysets = [set(df[session].itertuples(index=False,name=None)) for df in [questionnaire,frames]]
    if keysets[0] != keysets[1]:
        raise ValueError("Questionnaire and frame session keys differ; reconcile before analysis")
    paired = questionnaire.groupby(["Participant_ID","Original_Phase"]).Condition.nunique()
    result = {"questionnaire_rows":len(questionnaire), "frame_rows":len(frames), "event_rows":len(events),
              "participants":int(questionnaire.Participant_ID.nunique()),
              "original_phases":sorted(int(p) for p in questionnaire.Original_Phase.unique()),
              "unpaired_person_phases":int((paired != 2).sum()),
              "confidence_filter_applied":False,
              "au_missing_values":{c:int(frames[c].isna().sum()) for c in frames if c.startswith('AU')},
              "all_data_synthetic":False}
    if "confidence" in frames:
        confidence = pd.to_numeric(frames.confidence, errors="coerce")
        result["frame_confidence_at_least_08_ratio"] = float((confidence >= .8).mean())
        result["missing_or_invalid_confidence_rows"] = int(confidence.isna().sum())
    return result
