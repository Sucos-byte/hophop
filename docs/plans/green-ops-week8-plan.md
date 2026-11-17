# Week 8 — uncertainty, ablation and explainability

Verified clean00c19c2256eab73b8296db1f9da15e9852f401c9; created branch
green-ops/week8-uncertainty-explainability. Read applicable repository instructions
(none found), Week7 review/results/handoff/tracker, actual feature/data/model,
training, strict JSON and safe output APIs. Incoming270 tests; no baseline rerun.
No push/publish; all study data/results analytical_simulation.

## Freeze before outcomes

Recipe tools/green_ops/recipes/week8-uncertainty-v1.json pins source/assumption,
Week7 recipe/selection/model hashes, feature contract3, dataset2 and exact groups.
60 new semantic families:10 new payload levels ×6 new intervals, TX19dBm.
30 calibration /30 evaluation families; each3 durations ×5 repetitions =450rows.
900 nominal plus two450-row sensitivity panels on evaluation families only.
No shared parent configurations declared: fresh target-independent Cartesian
design. Same analytical generating law remains shared; physical independence
and exchangeability are not established. Exclude every known prior semantic
family, including all Week6/7 training/development/held-out/sensitivity tuples.
Lineage snapshot inventories all available previous study/demo workload.json and
dataset.csv under build,docs,/tmp/green-ops*, plus committed grid exclusions.
Unknown/missing key provenance is recorded and resolved before freeze.

Prediction intervals: per target one score per calibration family = maximum
absolute residual over its labeled15-row schedule. Raw target units; no learned
normalization. Fixed95% quantile rankceil((n+1)*19/20), no interpolation; reject
rank>n. For30 families rank30. Coverage concerns ALL labeled rows of a new
family, not independent rows or a confidence interval for a mean metric.
Null labels stay null; report excluded rows/families and coverage conditional
on availability. No-label families excluded; refuse insufficient finite quantile.
Intervals symmetric yhat±q, no clipping. No simultaneous three-target guarantee.
Evaluation shows row and family coverage, failures, widths; fixed nominal
thresholds applied unchanged to assumed-airtime1/10us shifts versus4 nominal.
No metric bootstrap confidence intervals in this study. No hardware guarantee.

Attributions: signed linear contribution beta_j*(x_j-training_mean_j)/scale_j;
baseline is original training intercept/means. Contributions sum to prediction
minus baseline, in target units. Top3 by absolute contribution, deterministic
ties. Held-out permutation on evaluation families only: within each duration,
shuffle entire family repetition blocks, fixed20 seeded repeats per feature;
also jointly shuffle payload+interval for correlated/interacting traffic axes.
Donors use same duration/repetition positions; no row-IID shuffling. Never
regenerate outcomes under permuted X. Numeric counterfactuals must belong to
frozen valid Cartesian support/full-slot policy; report/reject invalid combos.
Constant TX feature importance0. Show mean/SD/min/max and rank stability across
permutations (not a CI). Correlated features can share/mask credit; unconditional
permutation may break correlations and measures model sensitivity, not causation.

Ablations: drop each raw feature individually by zero masking, refit scaling/
ridge solely on original Week7 training labels with same target-selected alpha.
Keep four-position estimator schema with explicit retained-feature mask. Fit
before new calibration/evaluation scoring, freeze separate artifacts; never
replace Week7 model. Compare nominal evaluation MAE/RMSE with original; this is
predeclared diagnostic analysis, no hyperparameter search or interval tuning.

## Verified milestones

1. Freeze recipe, full prior-source lineage and this plan before generation or
analysis; verify counts, family/seed separation and source hashes. Commit.
2. Implement strict study dataset/replay API and materialize900+900 artifacts,
existing v2 tables; tests for plan/count/source/lineage/determinism/leakage.
Implement calibration quantiles/contracts and explanation/ablation primitives
with independent numerical tests. Commit verified code before real analysis.
3. Fit and commit ablation artifacts on original training only. Calibrate frozen
Week7 models using only450 nominal calibration rows; never read evaluation
labels. Commit strict calibration artifacts before locked evaluation.
4. Evaluate frozen calibration/models/ablations once on new nominal/sensitivity
families. Save predictions, family failures, widths, signed influences and
permutation stability. No selection/tuning. Strict versioned artifacts bind
model,dataset,recipe,feature/split hashes. Optional prediction CLI interval
extension preserves default output and rejects mismatches/unsafe output paths.
5. Reproduce outputs without tuning, run full suite/diff checks, document poor
coverage and exchangeability/synthetic limitations. Commit milestone, immediately
update tracker/handoff. Finish Week9 gatekeeper readiness; no physical evidence.

Use explicit staging, new files100644, staged check/stat/summary before commits.
Keep a current/next handoff. No inferred research hours; no optional dependencies.
