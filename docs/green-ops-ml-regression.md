# Deterministic energy regression workflow

This standard-library pilot consumes validated recorded analytical artifacts.
It is not a prospective hardware predictor or a calibrated physical model.
See [Week7 results](green-ops-week7-results.md) and the
[frozen plan](plans/green-ops-week7-plan.md). Dataset v1, dataset v2 fields,
feature-contract3 and the existing analytical/table commands remain compatible.

## Reproduce in a new directory

Run from the repository root. Each destination must be new; its parent must
exist. Source parsing/hashes and split membership are verified before fitting.
The recipe and all family/CV memberships are stored before outcomes are used.

```bash
mkdir build/green-ops-week7-repro
python3 tools/green_ops/green_ops_ml.py materialize \
  --recipe tools/green_ops/recipes/week7-regression-v1.json \
  --output-dir build/green-ops-week7-repro/dataset
python3 tools/green_ops/green_ops_ml.py train \
  --dataset build/green-ops-week7-repro/dataset \
  --output-dir build/green-ops-week7-repro/training
```

Record/commit selection.json and its model/selection-report hashes now, before
looking at held-out performance. The train command uses only training-family CV
and validation scoring. It does not produce test/stress scores. Then:

```bash
python3 tools/green_ops/green_ops_ml.py evaluate \
  --dataset build/green-ops-week7-repro/dataset \
  --training build/green-ops-week7-repro/training \
  --output-dir build/green-ops-week7-repro/evaluation
```

This command accepts only the frozen model inventory and matching data/recipe/
split digests. It does not fit, refit or select a model. It saves evaluation.json
and predictions.json, including chosen and baseline predictions, missing truth
as null, units, per-family errors and compatibility/digest metadata. Repeating
with identical inputs in the same recorded Python environment gives the same
bytes; no cross-runtime floating-point byte-identity guarantee is claimed.

The actual run is saved under ignored build/green-ops-week7; small model and
report snapshots are committed under docs/results/week7-regression-v1. The
canonical inventory digest binds all source CSV/manifest bytes, panel/split/
family/run identities and the recipe. Exported primary/stress CSV tables are
convenience copies; training loads and replay-validates the source bundles.
The actual 540 primary/180 stress design needed no correction.

## Models and targets

ml_pipeline.py exposes fit_regressor, predict_matrix, prepare_target, metrics,
evaluate_estimator, model_to_bytes, model_from_bytes and predict_record.
ml_workflow.py separates train_selection from locked_evaluation. The former
sorts records deterministically, fits fold-local preprocessing and applies the
frozen CV shortlist/validation choice. The latter never calls a fit function.

Training-mean baseline has zero coefficients. Ridge minimizes sum squared
residuals plus alpha*sum(squared standardized coefficients), with an unpenalized
intercept. X is centered and population-standardized on training labels only;
y is centered by its training mean. A Householder QR solve of the augmented
matrix [standardized X; sqrt(alpha)*I] avoids normal equations. Positive alpha
supports rank-deficient columns. Exact constant columns get scale1/coefficient0;
other nonfinite/degenerate numeric calculations fail rather than produce NaN.
There is no imputation, target-derived feature, post-run input or clipping.

Targets are trained/evaluated separately: mean power mW, total energy mJ and
energy-per-positive-delivery uJ. Null labels are excluded explicitly by target,
with counts/IDs recorded. Invalid X still fails for an unlabeled row. No labels
in train/validation or a frozen CV assessment fold cause a clear error; splits
are not moved to rescue a target. Evaluation keeps predictions for unlabeled
rows but excludes them from scores, with missing counts. Per-family reports
retain groups with no labels and null metrics rather than dropping the group.

R² is null for no labels, one label or constant truth, with a reason. Finite
negative R² and negative predictions remain visible. Reported metrics use raw
target units; per-family MAE/RMSE matter when within-family variance is tiny.
Sklearn is neither installed nor imported. Optional ensembles are outside this
pilot; a future adapter must be isolated and record its dependency versions.

## Prediction compatibility and safety

```bash
python3 tools/green_ops/green_ops_ml.py predict \
  --model docs/results/week7-regression-v1/training/target_total_energy_mj-chosen.json \
  --recipe tools/green_ops/recipes/week7-regression-v1.json \
  --artifact-dir PATH_TO_VALIDATED_ANALYTICAL_BUNDLE \
  --output build/new-prediction.json
```

The input directory must have dataset.csv/manifest.json and the archived source
bundle. Exact recipe bytes must match the trained model's recipe digest; the
full-slot offered-count policy and frozen retry cap are checked in addition to
parameter hashes, because those workload settings are absent from X. Prediction checks strict JSON model schema/contract versions, exact
feature order and profile, target/unit, finite coefficients/scales, analytical
provenance/source hashes, pre-run feature availability and recorded completion/
duration context. Primary mode requires the fixed primary parameter hash;
`--domain declared_stress` permits only the two predeclared stress hashes. This
is compatibility checking, not an accuracy, extrapolation or uncertainty gate.
Only extract_features' current pre-run columns enter the numerical predictor.
Do not invent completed execution for a future unexecuted firmware candidate.

The model schema is exact and versioned; it records training IDs/groups/splits,
seeds, runtime/dependencies, source scope, preprocessing/settings and hashes.
No pickle, dynamic imports or executable model payloads are used. JSON loaders
reject duplicate keys, unknown model/selection fields, bad scalar types and
nonfinite inputs. Digests prove byte identity, not trusted authorship. Treat
model provenance as an input trust boundary even though JSON is nonexecutable.

All commands return1 on invalid arguments/files/contracts or an existing output.
Fresh multi-file outputs roll back only files/directories created by that run;
existing inputs/destinations are not overwritten. Prediction uses the existing
single-file reservation/publisher. This protects ordinary failures, not a
multi-file crash transaction. Output directories cannot be nested into the
source dataset/training directory. External input/output aliases are rejected.

Week8 uncertainty calibration and explainability remain separate work. The
observed test/stress sets are not new untouched calibration data.

The public record prediction API requires
`predict_record(model, record, recipe_bytes=exact_frozen_recipe_bytes, domain=...)`.
A valid analytical bundle with partial offers or a changed retry cap is outside
the primary model's workload scope even when its current/timing hashes match.
The full dataset loader already enforced this policy before the real experiment;
final prediction guards only tighten new-input compatibility. Coefficients and
all saved scores remain unchanged. Per-delivery models are conditional on the
label being defined; a numeric forecast does not define a true target for a run
with zero deliveries. Missing truth stays null in saved predictions/metrics.
