# Software provenance

The current package is a 2026 adaptation prepared with AI assistance. It is not a frozen as-run study snapshot. Original notebook authorship and redistribution rights remain to be confirmed.

Project name: **Digital Human Interaction Evaluation**. The maintainer selected the [MIT License](../LICENSE) for this candidate on 2026-10-09. Its copyright notice uses collective project-contributor attribution rather than asserting sole authorship. This declared license does not independently resolve ownership or redistribution permission for the extracted archival functions listed below.

## Direct function extraction

- Source: `questionnaire LMM corrected.ipynb`. SHA-256: `281bd686f0b428a175bcc4dd8136660bb0d87f59811ba5d7d66ec9f66e0b42b4`. Target: `src/hci_eval/statistics.py`. Extracted functions: bh_fdr, holm_bonferroni, wald_combo.

- Source: `questionnaire LMM corrected.ipynb`. SHA-256: `281bd686f0b428a175bcc4dd8136660bb0d87f59811ba5d7d66ec9f66e0b42b4`. Target: `src/hci_eval/questionnaire.py`. Extracted functions: sanitize_name, cronbach_alpha, build_dv_long.

- Source: `openface_holm_c_corrected.ipynb`. SHA-256: `59b6f7148cdbc178641b68ee5404641562510478331729f08f8bc3feb837f601`. Target: `src/hci_eval/openface.py`. Extracted functions: build_pivots_from_timestamp, align_pivot_to_openface, compute_segment_masks, segment_means.


`Phase` fields were renamed `Original_Phase`. Import-time file operations, absolute paths and saved outputs were excluded. Questionnaire construction now handles absent phases/items as empty or incomplete outcomes instead of a column error.


The model loops and fitting wrapper were rewritten around the same fixed-effect formulas, ML optimizer and notebook correction families. Warnings and convergence are exposed. No CRSE or paper-family substitute was introduced. Default fit ordering follows the original questionnaire and AU choices.


The quality-check and participant-selection notebooks informed new `validation.py`, `qc.py` and `data.py`; these do not reproduce every original directory traversal or exclusion-log detail. Four historical plotting notebooks informed a new shared forest-plot function rather than being copied verbatim.


The synthetic generator, command-line entry point, canonical input adapters, tests, documentation and example notebook were newly authored for this release candidate. No real data, figures, publication PDF or private archive index was copied into the public candidate.
