# Analysis profile and version boundaries

The only implemented profile is `archived_notebooks`. It preserves the statistical choices in the available corrected questionnaire and OpenFace notebooks. It is not labeled as the published paper's executable specification.

## Stable original numbering

| Original phase | Conditions 1 / 2 | ECSCW phase | AU aggregation |
| --- | --- | --- | --- |
| 1 | Free / Focus gaze | 1 | Full session (`ALL`) |
| 2 | Keep / Let go after interruption | 2 | Interruption windows (`IN`) |
| 3 | Competitive / Cooperative interruption | Omitted | Interruption windows (`IN`) |
| 4 | Extrovert / Introvert persona | 3 | Full session (`ALL`) |

`Original_Phase` is required at every input boundary. `ECSCW_Phase` is a reporting field; original phase 3 remains missing there. No original phase is silently renamed or removed. The demonstration covers original phases 1, 2 and 4. The extracted item map also retains original phase 3 for version comparison.

Questionnaire input uses original item numbering. Original phase 1 Q9 is omitted from scoring. Original phase 2 Q2 and phase 3 Q5 use `8 - Score` on a seven-point scale. The final supplement relabels original phase 1 Q12 as Q9; paper-numbered input requires an explicit conversion before use.

Dimension composites require all constituent items in each participant/phase/condition. Historical descriptive code sometimes averaged available items, whereas its LMM composites required complete items. The public model input uses the latter. Reliability follows the archived pooled participant-by-condition calculation; this should not be interpreted as independent-person reliability estimation.

## AU event windows

The four intensity columns are `AU06_r`, `AU09_r`, `AU12_r` and `AU15_r`, nominal range 0–5. Interruption rows must have `interruption == 1` and `start > 5.0` seconds. Events within 3.0 seconds of the first event in a group are merged into that first event. This is a first-event grouping rule, not a chain of neighboring gaps.

Each retained event aligns to the nearest facial-frame timestamp, with ties choosing the earlier frame. The interval includes both endpoints: 0.5 seconds before to 5.0 seconds after onset. Overlapping intervals form a union, so a frame is counted once. Missing windows retain missing AU outcomes. Confidence is reported for quality inspection but is not used to introduce a new automatic frame exclusion. AUs are averaged over available AU values; `n_valid_au_frames` reports the contributing count.

Canonical events for original phase 2 represent participant interruption; original phase 3 events represent agent interruption. Synchronization and seconds conversion must be completed by the data owner. The new schema rejects event onsets outside frame coverage instead of silently clamping them to a boundary frame.

## Model specifications

`Condition01` is 0/1 for conditions 1/2. `Sequence01` is 0/1 for orders 1/2. The archived gender covariate maps M/F to 0/1. Reusing this binary specification with a different population requires a separately reviewed modeling decision.

Model C:

```text
DV_value ~ Condition01 + Age + Gender_F + Sequence01
```

Model T, separately for E, A, C, N and O:

```text
DV_value ~ Condition01 + Trait_c + Condition01:Trait_c + Age + Gender_F + Sequence01
```

Traits are centered over unique participants. Both models use participant random intercepts and condition random slopes, maximum likelihood (`reml=False`), `lbfgs`, and at most 200 iterations. The archived fallback to a random intercept occurs on a fit exception or random-slope variance below `1e-6`.

Nonconvergence alone does not silently trigger a new estimator or fallback. Each attempt's warnings and convergence are exported. Coefficients and raw/adjusted p-values remain available, while `fit_review_required` marks estimates needing review. Plots use `significant_usable`, which additionally requires no fit warning, finite positive SE and reported convergence. CIs are unadjusted 95% Wald intervals. They do not define corrected significance.

## Implemented correction families

| Modality and model | Method | Family |
| --- | --- | --- |
| Questionnaire C | Holm | Original phase, across its constructed DVs |
| Questionnaire T | BH-FDR | Original phase × DV × effect, across five traits |
| AU C | Holm | Original phase × metric, across four AUs |
| AU T | BH-FDR | Original phase × metric × trait × effect, across four AUs |

Missing p-values are preserved and excluded from the finite test count, matching the archived helpers. The family columns and finite count are exported per result. These choices should not be changed merely to obtain preferred significance.

## Unresolved correspondence with the publication

The final ECSCW paper's §4.2 describes participant cluster-robust standard errors. The two current core notebooks use the default MixedLM covariance; a corresponding cluster-robust implementation was not found in them. This repository retains model-based covariance and does not claim CRSE.

The paper describes BH-FDR for AU analysis; the available corrected AU notebook uses Holm for Model C. For trait analyses, the paper groups pertinent DVs and all three contrasts within phase × trait, which differs from the notebook families listed above. The paper also mentions cross-phase Holm in a result passage, while the questionnaire notebook adjusts within original phase. Resolving these differences requires identifying the code and data snapshot used for the final results. This package does not resolve them by guessing or rewriting the paper.

The analysis input cited by the study notebooks and the facial data tree are external to the inspected archive. The available 64-to-40 keep list does not establish per-participant exclusion reasons. Consequently, exact paper-result reproduction remains unverified.
