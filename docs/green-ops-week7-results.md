# Week 7 — frozen analytical regression results

All results below are **analytical_simulation**, not hardware observations. The
recipe was frozen in `6c4662e`; dataset audit `13b6064`; numerical core `ea8fafd`;
workflow/tests `58cbe92`. Real selected model/selection snapshots were committed
as **`8b18a39` before any real test/stress score was inspected**. The locked
evaluator performed no fitting, selection or tuning. No train+validation refit.

Review update: [Week7 review](plans/green-ops-week7-review.md) preserves these
historical snapshots. Metric-v2 replacement reports live in
`docs/results/week7-regression-v1/review/`;16 per-family R2 fields change only
at rounding scale. Aggregate scores, all MAE/RMSE, predictions and frozen models
are unchanged. Existing validation/test/stress are consumed.

## Experiment and locked choices

540 primary rows / 36 traffic families: 360 train (24 groups), 90 validation
(6 groups), 90 test (6 groups). Two separate 90-row assumed-airtime stress
panels use only the six untouched test families, for 180 additional rows.
Every duration, seeded repetition and parameter variant stays with its family.
Group-local random streams prevent cross-group seed sharing; this is procedural
isolation, not proof of physical independence. All720 source bundles were replay-
audited against the frozen plan. No design correction was necessary.

X is exactly payload, interval, requested TX power and planned fixed duration.
No engineered terms, labels, energies, IDs, seeds, groups, model hashes, actual
deliveries or attempt outcomes enter X. TX power is constant19dBm in this scope.
Input preprocessing is fitted only on labeled training rows, separately per
energy target; CV preprocessing is fitted only on each training fold.

Four fixed grouped CV folds rank ridge alphas0.01/1/100; the two best ridge
settings plus the training-mean baseline enter validation selection. Validation
RMSE chooses the model, with the predeclared baseline/larger-alpha tie rule.
All three choices were ridge: alpha1 for power; alpha0.01 for the two energy
targets. The solver uses augmented Householder QR (no normal equations),
population-standardized X, centered y and an unpenalized intercept. Constant
features have scale1/coefficient0. Predictions are never clipped.

## Primary locked test

Each target has90 labeled rows /6 families; no missing labels occurred in this
particular held-out dataset. Missing per-delivery labels are still explicitly
excluded by the implementation and tested; they are never replaced with zero.

| Target | Unit | Selected MAE | Selected RMSE | Selected R² | Mean baseline RMSE |
|---|---|---:|---:|---:|---:|
| Mean power | mW | 5.2156 | 6.3664 | 0.631611 | 10.4908 |
| Total energy | mJ | 35.0090 | 51.1850 | 0.991539 | 556.4636 |
| Energy per delivery | uJ | 412.7401 | 991.1826 | 0.998600 | 27864.9393 |

uJ means microjoules (µJ). The full machine report contains both models’ MAE,
RMSE and R², chosen-minus-baseline differences, per-family errors, sample/group
counts, missing labels and negative-prediction counts. R² is null with an
explicit reason for fewer than two labels or constant truth, even for a perfect
constant prediction. No negative selected predictions occurred in the real
held-out panels. Very small within-family variance makes family R² unstable;
per-family MAE/RMSE are retained rather than hiding difficult families.

## Stress — same frozen models, hidden timing coefficient shifts

No adaptation or re-selection was performed. Timings are assumed1 or10us/byte
versus nominal4us/byte. Model parameters are not predictive inputs; these
stress rows were kept outside primary training. Each panel has90 rows /6 groups.

| Panel | Target | Unit | Selected MAE | Selected RMSE | Selected R² | Baseline RMSE |
|---|---|---|---:|---:|---:|---:|
| airtime-low | Mean power | mW | 5.1424 | 6.2246 | 0.168827 | 7.8911 |
| airtime-low | Total energy | mJ | 35.6238 | 44.0073 | 0.993328 | 539.1590 |
| airtime-low | Energy per delivery | uJ | 905.3024 | 1258.4033 | 0.997714 | 27523.5837 |
| airtime-high | Mean power | mW | 9.0304 | 15.8202 | 0.264121 | 20.2930 |
| airtime-high | Total energy | mJ | 53.6392 | 112.6823 | 0.964153 | 596.8929 |
| airtime-high | Energy per delivery | uJ | 1143.0163 | 1654.3572 | 0.996203 | 28587.1639 |

Power performance is modest on nominal test and weak on these stress panels.
The high-airtime power RMSE increases to15.82mW; stress power R² is only0.169–0.264.
Total/per-delivery energy are easier to recover from this generator and its
predeclared timing/load pattern. These results do not establish robust DECT
prediction. No choices were changed after seeing these weaknesses.

## Primary per-family selected-model errors

Each family has15 test rows (three durations × five seeds).

| Payload bytes | Interval ms | Power RMSE mW | Total RMSE mJ | Per-delivery RMSE uJ |
|---:|---:|---:|---:|---:|
| 16 | 75 | 1.2226 | 6.7733 | 243.9528 |
| 128 | 500 | 3.5756 | 41.8563 | 2276.8122 |
| 256 | 50 | 12.3212 | 101.0894 | 413.3850 |
| 256 | 100 | 2.8807 | 21.1940 | 423.4867 |
| 256 | 250 | 6.4890 | 40.9368 | 359.7508 |
| 512 | 500 | 5.1661 | 39.7182 | 414.2736 |

## Saved artifacts and integrity

- [Dataset audit](results/green-ops-week7-dataset-audit.json).
- [Frozen recipe](../tools/green_ops/recipes/week7-regression-v1.json).
- [Frozen selection](results/week7-regression-v1/training/selection.json) and [CV/validation report](results/week7-regression-v1/training/selection-report.json).
- [Held-out evaluation](results/week7-regression-v1/evaluation/evaluation.json) and [1,620 saved predictions](results/week7-regression-v1/evaluation/predictions.json).
- [Prediction CLI example](results/week7-regression-v1/prediction-example.json).

The training directory contains six inspectable JSON models (baseline/chosen
per target): exact feature order/profile, scaler means/scales, intercept and
coefficients, objective/solver/alpha, label unit, fit membership, seeds, source
scope, Python runtime (stdlib only), dataset/recipe/split hashes and contract
versions. No pickle or optional sklearn dependency is used. Prediction is
`intercept + sum(coef[j] * (X[j]-mean[j])/scale[j])` in the target unit.

Dataset SHA-256:
`e921297009bc1b12ca325cf13dfc16fbf4e4c5013bceb28fd1dbd02b18b9cf98`.
Recipe SHA-256:
`4a979b6cec4555c27d1813f33dc8481410e1ba2382dec2bb93b8366be32d1daf`.
Locked selection SHA-256:
`31e53f4e8f4317be71bc8fed6b0024f0985a1cc5e195f4c833d43ae62acf226b`.

The selection/models remain byte-identical to the pre-evaluation commit.
Final prediction compatibility checks retain the consumed manifest snapshot
digest and require the exact frozen recipe/full-slot offer policy/retry cap.
Targeted tests reproduce unsafe partial-offer/retry inputs and reject them.
Every real locked input already satisfied this policy in the dataset loader.
These checks changed no coefficients, scalers, hyperparameters or saved scores.

## Interpretation and Week8 readiness

The models approximate known synthetic accounting formulas. Total energy is
strongly duration-driven; per-delivery energy largely follows a known offer-rate
and delivery-denominator relationship. Learning these laws exercises regression
and grouping software, not Nordic current accuracy, hardware timing, physical
channel loss/latency or battery autonomy. Post-run delivery proxies were never
used. Supplier current values remain conditioned typical points; timings/loss/
envelopes are assumptions. The source audit/physical limitations from Week6 apply.

Week8 can begin software uncertainty/explainability work with these frozen
models. First predeclare new group-disjoint calibration and evaluation data:
validation has already selected models, and test/stress results are now observed.
Do not tune intervals or new choices on these results while calling them an
untouched test. Current stress envelopes are not probability distributions or
confidence intervals. Target-specific missingness and group dependencies must
be preserved. Any importance/attribution is model sensitivity, not physical
causality. No uncertainty calibration or explainability was implemented here.
Physical calibration and independent measured validation remain pending.


## Verification

Final full suite: **267 tests pass**, including **21 new Week7 tests**, with
ResourceWarning treated as errors. `git diff --check` passes. The stricter frozen-
recipe/workload guard passed for all270 locked inputs without repeating fitting
or scoring. Frozen selection/model hashes remain those committed before test.
The prediction CLI example exactly matches its saved held-out prediction.
V1, dataset v2, feature-contract3 and analytical artifact/table compatibility
remain intact. No optional libraries, calibration or explainability were added.

Final verified evaluation/compatibility milestone: `ebd9998`; frozen model
selection checkpoint: `8b18a39`. A documentation-only progress/handoff checkpoint
follows. No unchanged-suite rerun is required for that checkpoint.
