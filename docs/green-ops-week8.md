# Week8 analytical uncertainty and sensitivity workflow

All results are analytical_simulation. Week7 models/selection remain frozen;
this study fits interval thresholds and separate diagnostic ablations only.
Study version1 supports exactly the committed recipe bytes (SHA pinned in
week8_dataset.py). Any design change needs an explicit new recipe/version; no
silent mutation or expanding supported prediction scope.

## Data and provenance

The committed recipe and lineage inventory predate new study scoring. Semantic
family key is (payload bytes, interval ms, TX dBm), with all repetitions,
durations and parameter variants assigned to that family.60 new families use
new payload AND interval levels. Old train/validation/test/stress families are
all excluded, not only their IDs/seeds. Every prior available study/demo workload
and dataset source was scanned;3460 configured source files identify48 prior
families. Two v1 unmeasured parser fixtures have no configured feature values or
energy labels and cannot identify families; this is recorded explicitly. No
physical independence claim follows from this software lineage audit.

30calibration and30evaluation families each have15 rows (3 durations ×5 streams).
900 primary rows; two450-row evaluation-family sensitivity panels use assumed
airtime1/10us per byte versus4 nominal. Common random streams stay within family.
Source provenance remains synthetic/simulation/analytical_simulation. No modeled
RTT is treated as observed latency, and no PPK2 measurement evidence is created.
Versioned inventories validate exact recipe, workload, manifest, source parameter,
assumption and replay hashes; existing dataset-v2 tables remain compatible.

## Prediction intervals

The nonconformity score for each calibration family is the maximum absolute
residual over its15 labeled rows. For each target independently, use order
statisticceil((n+1)*19/20), no interpolation. n=30 givesrank30. n<19 cannot
produce a finite95% threshold and is rejected. Intervals are prediction±q in
mW/mJ/uJ, symmetric and unclipped. Negative lower bounds are allowed. No
calibration label influences model coefficients or feature preprocessing.

The intended coverage event is ALL labeled rows of a future family with the
same fixed duration/repetition schedule. It is not95% coverage for each of450
independent samples. Report both diagnostic row coverage and family coverage,
exact failures, null labels and widths. Null per-delivery labels never become0;
families without labels are excluded with reasons, and quantile sufficiency is
rechecked. Any coverage statement is conditional on this availability policy.
Three per-target95% procedures do not establish joint95% three-target coverage.

Split-conformal rank validity requires calibration and future family scores to
be exchangeable conditional on fixed model/design. Hash assignment avoids
outcome-based selection but does not prove exchangeability of a deterministic
grid. Grouping records does not remove common generating assumptions or source
bias. Applying the same q under assumed-airtime shifts is sensitivity testing,
not calibrated coverage under a new distribution. No evaluation outcome selects
q, score, width, feature, alpha or replacement model.

These are prediction intervals for new outcomes/families, not confidence
intervals for RMSE, mean coverage or other aggregate metrics. We report no
bootstrap confidence intervals;30 families is the relevant small sample size,
not450 rows.20 permutation SDs describe algorithm perturbations, not a metric CI.

## Explainability and ablation

The signed linear contribution is beta_j*(x_j-training_mean_j)/training_scale_j.
The reference prediction is the original training intercept. Baseline plus
contributions reconstructs prediction. Contributions have target units (mW,mJ,
uJ); raw feature units are bytes,ms,dBm,ms. Top3 rank absolute contributions with
feature-order ties. Global mean absolute contributions and per-record top3 are
saved; constant TX contributes0. Signs are relative to the training mean,
not evidence that increasing a feature physically causes that effect.

Permutation importance measures held-out nominal RMSE increase. For each fixed
seeded repeat, independently within each duration, a hash permutation maps
recipient families to donor families; all5 repetition positions move as a block.
One feature at a time is substituted; also jointly permute payload+interval.
No seed/ID/target/outcome enters X. Donor/recipient durations and repetition
positions align. All hybrid combinations must lie on the valid full Cartesian
study support and have at least one full-slot offer; otherwise reject. Such
hybrids may be unobserved in the evaluation subset and break feature dependence;
we do not regenerate labels or claim their causal counterfactual energy.

Correlated features can share/mask credit; joint permutation complements but
does not solve conditional importance. Importance can be negative. Report all
20 RMSE increases, mean/populationSD/range and top3/ranks across repeats; do not
select a favorable seed/repeat. These are sensitivities of the fitted formula.

Four predeclared leave-one-feature-out ridge models are fit only on original
Week7 training rows with original selected alpha. Zero-mask the omitted column
for fit and prediction; fit preprocessing anew on that training matrix. Artifacts
retain explicit dropped feature and original train-run membership. The complete
model/choices remain unchanged. Evaluation ablations are diagnostics, not a
feature search or a reason to replace the frozen model in this study.

## Reproduce and predict

Run from repository root; every destination must be new. Archive generated
source bundles locally under build; committed small models/calibration/reports
provide exact references. Dependencies are standard-library Python only.

```sh
python3 tools/green_ops/green_ops_week8.py materialize --recipe tools/green_ops/recipes/week8-uncertainty-v1.json --lineage docs/results/week8/lineage.json --output-dir build/green-ops-week8-data
python3 tools/green_ops/green_ops_week8.py ablations --dataset build/green-ops-week8-data --models docs/results/week7-regression-v1/training --original-recipe tools/green_ops/recipes/week7-regression-v1.json --original-dataset build/green-ops-week7/dataset --output-dir build/green-ops-week8-ablations
python3 tools/green_ops/green_ops_week8.py calibrate --dataset build/green-ops-week8-data --models docs/results/week7-regression-v1/training --original-recipe tools/green_ops/recipes/week7-regression-v1.json --ablations build/green-ops-week8-ablations/ablations.json --output-dir build/green-ops-week8-calibration
python3 tools/green_ops/green_ops_week8.py evaluate --dataset build/green-ops-week8-data --models docs/results/week7-regression-v1/training --original-recipe tools/green_ops/recipes/week7-regression-v1.json --ablations build/green-ops-week8-ablations/ablations.json --calibration build/green-ops-week8-calibration --output-dir build/green-ops-week8-evaluation
python3 -W error::ResourceWarning -m unittest discover -s tools/green_ops/tests
```

If original data is absent, regenerate with the existing Week7 materialize CLI
and exact committed Week7 recipe. The original loader replay-validates hashes.
Separate commits freeze fitted ablations and calibration before real evaluation.
Tests exercise mathematical invariants using the fixed study design without
printing performance scores or selecting any method. CLI output is exclusive;
partial publication rolls back owned outputs and never replaces input sources.

Existing green_ops_ml.py predict still emits its original version1 point result.
Add BOTH `--calibration TARGET-calibration.json --study-recipe FILE` to emit
version2 interval metadata. Other original flags remain required. The extension
checks calibration quantile, target, model hash, frozen recipe/split/lineage,
feature contract and fresh declared evaluation-family schedule; default behavior
and v1 dataset compatibility are preserved. Research prediction consumes a
validated completed analytical record; this is not an unqualified prospective
hardware predictor. Calibration dataset hashes remain auditable via the study
inventory; a single-record CLI cannot revalidate an unavailable entire dataset.
A whole-study evaluator checks that digest as well. Hashes detect accidental
inconsistency, not malicious wholesale coordinated artifact rewriting.

Explanation and ablation artifacts bind model hashes, original training dataset,
study dataset/recipe/split/lineage and feature contract. Readers validate schemas,
permutation statistics/ranks and contribution accounting/source membership. No
pickle, optional sklearn, network publishing or remote deployment is used.
