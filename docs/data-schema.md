# Canonical input schema

All files are UTF-8 CSV. Participant keys must be strings, privately pseudonymized, with no contact details or embedded meeting identifiers. Input records use original phase and question numbering. Leading/trailing CSV header whitespace is removed at import.

## questionnaire.csv

Unique key: `Participant_ID`, `Original_Phase`, `Condition`, `Question`.

| Field | Required meaning |
| --- | --- |
| `Participant_ID` | Stable private participant key |
| `Original_Phase` | Original behavioral phase 1–4 |
| `Condition` | 1 or 2 in the archived phase map |
| `Question` | Positive original item number, before final-paper relabeling |
| `Score` | Unreversed seven-point score, 1–7 |
| `Order_Sequence` | Archived order coding 1/2, constant within person × phase |
| `Age` | Numeric participant age, constant within person |
| `Gender` | Archived M/F encoding, constant within person |
| `E`, `A`, `C`, `N`, `O` | Numeric Big Five scores, constant within person |

Duplicate question keys and conflicting person metadata are errors. Do not pre-reverse or silently impute scores. A participant-level filter may be performed with `data.select_participants`; filtering creates a copy and does not delete files. Keep selection reasons in a separate restricted study log.

## frames.csv

Unique key: `Participant_ID`, `Original_Phase`, `Condition`, `timestamp`.

Required AU intensity fields: `AU06_r`, `AU09_r`, `AU12_r`, `AU15_r`. Values must be 0–5 or missing. `timestamp` is nonnegative seconds on the same time origin as the event table. `confidence` is optional and reported, without silently imposing a new frame filter.

The table contains facial measurements of the human participant, not the digital-human actor. Conversion from native OpenFace files and media synchronization remain upstream tasks; this package does not run OpenFace or process raw video.

## events.csv

Unique key: `Participant_ID`, `Original_Phase`, `Condition`, `start`.

`start` is a nonnegative onset time in seconds. `interruption` is 0 or 1. Phase 2 events refer to participant interruption, phase 3 to agent interruption. Sessions with no eligible events retain missing `IN` outcomes. Event keys without matching frame sessions are rejected.

## Outputs and privacy

`questionnaire_outcomes.csv` and `au_outcomes.csv` retain participant keys and are restricted when real data are used. `*_condition.csv` and `*_traits.csv` contain aggregate model outputs, diagnostic warnings, correction families and sample counts. Aggregate output is not automatically anonymous or cleared for publication. Review all outputs before sharing them.

`data/demo/` contains only newly generated synthetic data. The `SYN_` prefix denotes fictional people. No real record was renamed, sampled, copied or perturbed to produce those examples.
