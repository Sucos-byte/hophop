# Week 7 review before Week 8

Reviewed9138511..a2aeb15 on green-ops/week7-ml-regression, clean at entry.
Read Week7 plan/frozen recipe, tracker, Week6 review, actual dataset/replay,
feature/artifact, numerical, workflow and CLI code/tests. No applicable AGENTS.md.
Corrections are local; no push/publish or held-out model selection.

## Findings and corrections

| Finding | Correction and evidence |
|---|---|
| R2 variance centered around a rounded large mean could be wrong. For truth `[1e16,1e16,1e16+2]` and constant predictions1e16, oldR2=0; independently calculated SSE4/SST(8/3) gives -0.5. | Power-of-two scaling and centered offsets retain small variance and avoid variance overflow. Targeted tests cover this, translation invariance, extreme opposite values and constant truth. |
| Internally valid model metadata could disagree with the exact recipe supplied for prediction (split membership, seeds, experiment, alpha). | Bind metadata/settings to recipe; tests reject rehashed split metadata and altered seeds/experiment. Frozen original artifacts still pass. |
| A rehashed selection report could claim a shortlist/winner inconsistent with its CV/validation scores. | Load verifies frozen candidates/settings, finite nonnegative selection RMSE, CV shortlist and validation winner/tie rules. Test rejects a contradictory rehashed shortlist. Also check exact labeled training-group membership. Hashes provide integrity, not signatures or proof against wholesale coordinated fabrication. |

Correction milestone6a35879. Full suite270 passes with ResourceWarning errors
(three new tests over267); independent one-column ridge/rank deficiency/constant
feature tests continue passing. Diff/staged checks pass. No coefficients,
preprocessing, alpha choices or source data were changed to improve scores.

## Isolation, preprocessing and selection

Frozen recipe hashes and source replay validate actual540 primary rows across
36 families,360/90/90 train/validation/test with24/6/6 families, plus180 stress
rows. Inventory/planner comparison rejects duplicate identities/realizations,
wrong groups, source edits and cross-family seed reuse. Group key is canonical
(payload bytes, interval ms, requested TX power), independent of seed/duration/
parameter variant. Durations and repetition streams stay together. Stress
variants deliberately share six test groups and streams; they provide sensitivity
panels, not additional independent families. Equal numeric predictions/X across
those panels are legitimate; duplicates across source run identities are not.
Seeds, IDs, groups and outcomes never enter X.

X is exactly four declared pre-run fields: payload bytes, interval ms, TX dBm,
window duration ms. TX is constant and coefficient0/scale1. The available
completed-artifact prediction interface validates capability, full-slot offers,
retry cap, source scope, exact recipe and manifest snapshot. This pilot does
not yet establish prospective hardware feature availability beyond that contract.

All fold scaling is fitted on that fold's labeled fitting records, not its
assessment records. Final scaling/baseline use labeled training rows only;
validation is never included in fitting. Independent replay checked216 means/
scales against statistics.fmean/pstdev and checked exact fit-run/group membership.
Existing tests forbid reading held-out target values during selection and forbid
fit calls during evaluation. Actual choices are identical on replay: ridge1
for power, ridge0.01 for total energy and per delivery. CV shortlists two ridge
settings plus baseline; validation RMSE/ties select. Commit8b18a39 froze exact
models before original held-out scoring. No refit on validation or held-out
retuning occurred; this review only replayed the frozen settings.

## Targets, numerics and artifacts

Separate targets use mW, mJ and uJ/delivered packet. Null labels are filtered
per target, preserved as null in predictions, and excluded from metric counts;
zero is never substituted. Invalid X fails even with a missing label. No real
locked panel has missing labels; dedicated tests cover absence/zero-delivery.
MAE, RMSE and training-mean predictions were independently recalculated from
saved predictions/source labels. Per-family metrics retain undefinedR2 for
constant truth, one label or no labels. Very negative familyR2 is reported,
not clipped or hidden.

Ridge solves the augmented regularized least-squares system by Householder QR,
with unpenalized intercept and population-standardized training X; no normal
equations. Positive frozen alphas handle collinear/constant features. Strict
finite JSON model roundtrip validates contracts, feature order, target units,
shape, scope, train-only membership and settings; no pickle/optional dependency.
Numerical overflow and unavailable/nonfinite inputs fail. Model metadata records
Python3.14.4, standard-library runtime and empty optional dependencies.

## Reproduction and replacement metrics

A new720-bundle materialization replayed states/energy from archived parameters,
assumptions and seeds. Dataset audit, all six model files, selection, CV/validation
report, evaluation report and all predictions reproduced byte-for-byte at the
original review entry. See `docs/results/week7-regression-v1/review/`:

- historical-reproduction.json: exact hashes,216 independent preprocessing checks,
  zero evaluation fit calls,720 sources and1620 unique prediction keys.
- reproduce_historical.py: replay with original a2aeb15 code/Python3.14.4 in a
  fresh checkout; output directory must not exist.
- reproduce_corrected.py: current-code replay against validated dataset. Verifies
  original model bytes/choices and unchanged predictions; independently checks
  aggregate/per-family R2 from centered-offset sums of squares. It never replaces
  or deploys the audit-only training replay models/selection.
- evaluation-metrics-v2.json and selection-report-metrics-v2.json: replacement
  metric reports, explicitly version2. Original `training/` and `evaluation/`
  files are retained unchanged as history. Original selection remains authoritative.
- correction-receipt.json:16 changed evaluationR2 paths with old/new values,
  original prediction/selection hashes, zero fitting during evaluation.

Only16 per-family R2 values change, at rounding scale for this dataset; aggregate
R2, all MAE/RMSE, model bytes, selected settings and predictions are unchanged.
Historical R2 reporting is superseded by metric-v2 reports, including the
separately archived training/CV report. Its validation/CV RMSE choices did not
change. No performance claims are improved by the correction.

DatasetSHA e921297009bc1b12ca325cf13dfc16fbf4e4c5013bceb28fd1dbd02b18b9cf98;
recipeSHA4a979b6cec4555c27d1813f33dc8481410e1ba2382dec2bb93b8366be32d1daf;
original selectionSHA31e53f4e8f4317be71bc8fed6b0024f0985a1cc5e195f4c833d43ae62acf226b.
These match replayed source inventory, exact recipe bytes and saved models.

To reproduce current corrected reports from repository root (fresh destinations):

```sh
python3 tools/green_ops/green_ops_ml.py materialize --recipe tools/green_ops/recipes/week7-regression-v1.json --output-dir build/week7-review-fresh
python3 docs/results/week7-regression-v1/review/reproduce_corrected.py build/week7-review-fresh build/week7-review-corrected
python3 -W error::ResourceWarning -m unittest discover -s tools/green_ops/tests
```

## Why 1,620 predictions

| Split/panel | Underlying rows | Targets | Model roles | Prediction records |
|---|---:|---:|---:|---:|
| Test nominal |90|3|2|540|
| Stress airtime-low |90|3|2|540|
| Stress airtime-high |90|3|2|540|
| Total |270|3|2|1620|

Each target/role/panel cell has90 records. Roles are training-mean baseline and
chosen ridge (poweralpha1, total/per-deliveryalpha0.01). There are270 underlying
runs but only6 held-out traffic families, reused across the stress panels.
The1620 count is neither sample independence nor1620 distinct observations.

Test chosen RMSE remains6.366407mW,51.185016mJ,991.182631uJ, versus baseline
10.490793mW,556.463555mJ,27864.939348uJ. Power testR2=0.631611 and stressR2
0.168827/0.264121 remain modest. These are analytical_simulation results: learning
the generating formulas does not validate physical radio energy, battery life,
loss/RTT assumptions or deployment transfer.

## Week 8 readiness and fresh design

Ready for a separately frozen software calibration/explanation study, with
physical validation still pending. Existing validation, test and stress are
consumed. Do not reuse them as fresh calibration/assessment; new repetitions or
master seeds on their configurations do not create new groups.

Proposed target-independent design is saved as week8-design-proposal.json:
10 new payload levels24,48,80,96,160,192,320,384,448,480 bytes ×6 new intervals
60,90,120,180,300,450ms, fixed sourced TX19dBm =60 new traffic families. None
intersects the48-family union of documented Week6/Week7 grids. Five repetitions
and three durations1000/5000/10000ms give900 nominal rows. Hash-ranked split
(seed2026111809, exact memberships saved):30 calibration/450rows and30 final
assessment/450rows. Proposed master seed2026111808 yields300 unique group-local
streams; verified no collision with documented prior-grid streams. No Week8
labels generated in this review.

Before generation, inventory all prior/demo workloads and declared parent lineage,
recompute semantic keys rather than trusting group labels, reject any overlap,
and freeze final recipe/source/assumption/contract/model hashes. If new tuples
are variants of an old parent, assign that parent one coarser group and redesign
the split. Do not silently grandfather such overlap. Actual source provenance
and disjointness must be revalidated at Week8 entry, including any intervening data.

Freeze model, scoring/normalization rule, coverage levels, missing-label policy
and explanation method using consumed development data before fresh outcomes.
Fit only calibration thresholds on calibration families; reserve assessment
until everything is frozen. For example, one predeclared maximum residual score
per family across durations/repetitions gives30 calibration units, not450.
Per-target95% split-conformal rankceil((30+1)*0.95)=30 is finite when all30
families have labels; fewer than19 labeled groups cannot support finite95%
rank coverage without another policy. Specify absent-delivery-label handling
before generation. Three separate95% intervals do not promise joint95% coverage.
Do not select scoring methods on these same calibration labels; reserve further
families if selection is needed. Optional sensitivity panels inherit assessment
family groups and are consumed together, never counted as independent units.

New tuples establish disjoint recorded groups, not an independent physical law.
Shared analytical assumptions and deterministic grids do not prove exchangeability;
state any conformal coverage assumptions explicitly. Fixed family maxima across
15 rows are a familywise target, distinct from individual-row coverage. No
hardware calibration, observed latency or measured PPK2 evidence is available.
