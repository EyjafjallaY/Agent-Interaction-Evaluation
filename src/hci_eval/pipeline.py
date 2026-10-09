"""Canonical CSV pipeline. Each modality is modeled separately with shared metadata."""
import json
from pathlib import Path
import pandas as pd
from .questionnaire import preprocess_questionnaire, build_dv_long, reliability_table, TRAITS
from .openface import aggregate_sessions
from .qc import quality_summary
from .validation import validate_frames, validate_events, ECSCW_PHASE


def prepare_outputs(out):
    out = Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError("Output directory is not empty; choose a new directory")
    out.mkdir(parents=True,exist_ok=True)
    return out


def analyze(questionnaire, frames, events, out, synthetic=False, maxiter=200, plots=True):
    from .modeling import fit_models
    prepared = preprocess_questionnaire(questionnaire)
    validate_frames(frames)
    validate_events(events)
    qc = quality_summary(prepared,frames,events)
    qc["all_data_synthetic"] = bool(synthetic)
    q_long = build_dv_long(prepared)
    au_long = aggregate_sessions(frames,events)
    keys = ["Participant_ID","Original_Phase","Condition"]
    cov_columns = ["Condition01","Sequence01","Gender_F","Age"] + [t+"_c" for t in TRAITS]
    metadata = prepared[keys+cov_columns].drop_duplicates(keys)
    au_long = au_long.merge(metadata,on=keys,how="left",validate="many_to_one",indicator=True)
    if not au_long._merge.eq("both").all():
        raise ValueError("OpenFace sessions without questionnaire metadata")
    au_long = au_long.drop(columns="_merge")
    au_long["ECSCW_Phase"] = au_long.Original_Phase.map(ECSCW_PHASE)
    out = prepare_outputs(out)
    q_long.to_csv(out/'questionnaire_outcomes.csv',index=False)
    au_long.to_csv(out/'au_outcomes.csv',index=False)
    reliability_table(prepared).to_csv(out/'questionnaire_reliability.csv',index=False)
    outputs = {}
    for modality,long in [("questionnaire",q_long),("openface",au_long)]:
        condition,traits = fit_models(long,modality,maxiter=maxiter)
        condition.to_csv(out/f'{modality}_condition.csv',index=False)
        traits.to_csv(out/f'{modality}_traits.csv',index=False)
        outputs[modality] = {"condition_rows":len(condition), "trait_rows":len(traits),
                             "condition_fits_requiring_review":int(condition.fit_review_required.sum()),
                             "trait_fits_requiring_review":int(traits.drop_duplicates(['Original_Phase','DV','Trait']).fit_review_required.sum())}
        if plots:
            from .plotting import forest_plot
            forest_plot(condition,out/f'{modality}_condition.png',f'{modality.title()}: condition 2 minus condition 1',synthetic=synthetic)
            if modality == "openface":
                selected = traits[(traits.Original_Phase == 1) & (traits.DV == 'AU12_r') & (traits.Effect == 'interaction')]
                if not selected.empty:
                    forest_plot(selected,out/'openface_trait_example.png','AU12: personality x condition',synthetic=synthetic)
    report = {"analysis_profile":"archived_notebooks", "synthetic":bool(synthetic),
              "paper_results_reproduced":False, "quality":qc,"outputs":outputs,
              "inference":"model-based covariance; not participant cluster-robust SE", "maxiter":maxiter}
    (out/'run_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
