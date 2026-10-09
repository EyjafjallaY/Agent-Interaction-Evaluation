# Verification record

Date: 2026-10-09. Environment: isolated Python 3.12.14 on Windows. Dependencies were downloaded from official PyPI after user approval and installed only in the task environment. Tested versions are in `requirements-tested.txt`.

## Software checks

- The package was built as a wheel and installed into the isolated environment. The installed command-line package executed the complete synthetic demonstration from outside the source directory.
- After adding the MIT declaration, the package was rebuilt in a separate task directory. The built wheel's `License-Expression: MIT`, `License-File: LICENSE` and included license text were verified. This metadata update changed no analysis code or synthetic results.
- All 16 tests passed; none were skipped. These include reverse scoring, original phase mapping, complete-item composites, event cutoffs/merging/window unions, invalid inputs, non-destructive selection, correction-oracle comparisons, nonconvergence reporting, historical fallback and correction families.
- All 13 Python source/test files parse. The new example's three code cells executed on synthetic inputs; the delivered notebook has no saved outputs or execution counts.
- Three committed synthetic CSV files were independently regenerated and matched numerically.
- The complete demonstration fitted 156 models and exported 416 effect rows. Every exported adjusted p-value and family test count matched an independent statsmodels `multipletests` calculation within `1e-12` tolerance.
- Three forest plots were rendered and visually inspected. Example aggregate model outputs and PNGs are in `examples/model-output/`.

## Fit diagnostics and interpretation

The 84 questionnaire fits reported convergence with no captured warnings in this synthetic run. All 72 AU fits had a parameter-boundary warning. Five AU fits also failed to converge: one condition model and four trait models. All warned fits retain `fit_review_required=True`; their plots use hollow points and do not mark them as usable significant effects. These are software-behavior examples, not validated substantive AU findings. No statistical estimator was changed to hide warnings.

The statistical formulas, optimizer, fallback and correction families follow the available notebooks. Participant cluster-robust standard errors and publication-family correspondence remain unresolved, as described in `methods.md`. No real-data or paper-result reproduction was performed.

The public whitelist includes only adapted code, newly authored documentation and independently generated synthetic assets. Notebook output clearance and checks for known local paths/private access patterns passed. This bounded review is not a universal anonymity guarantee.
