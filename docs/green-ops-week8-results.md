# Week8 — frozen analytical uncertainty and model sensitivity results

All results are **analytical_simulation**. These are software diagnostics of the
same analytical generator, not hardware coverage or physical energy validation.
Week7 models and selection remain unchanged. Nominal family coverage falls below
95% for every target; no intervals, features or model choices were adjusted.

## Freeze and reproducibility evidence

Clean entry00c19c2; branch green-ops/week8-uncertainty-explainability.
Pre-analysis recipe/lineage/methods committed3e0dd39. Verified APIs/data6da8dba;
original-training-only ablations3e491f9; calibration thresholds4d66d51 committed
before the real evaluation command. Automated integration tests previously
exercised invariants without exposing performance scores or selecting methods.

Dataset900 nominal rows from60 new semantic families:450rows/30calibration and
450rows/30evaluation;900 additional sensitivity rows reuse evaluation families.
Prior3460 configured sources/48families excluded, plus recorded resolution of
two unconfigured unmeasured parser demos. No new-seed-only independence claim.
Every1800 source bundle replays states/energy under archived parameters and
assumptions. A second independent1800-bundle generation produced byte-identical
inventories/audits/source snapshots and all six table files.

DatasetSHA d4a3c8a0ecbaf774274aa33ccd334bdf991180863212a14e5cae47e8b163545e;
recipeSHA547c93bf038eb9a064571f3d1d46f28fb071e1f76106673ec537e597d3cb20fa.
Original selectionSHA31e53f4e8f4317be71bc8fed6b0024f0985a1cc5e195f4c833d43ae62acf226b
is unchanged. Repeated ablation fits, calibration and evaluation reproduce exact
saved bytes. [Reproduction receipt](results/week8/reproduction.json) records
hashes,Python3.14.4/stdlib runtime and independent bounds/coverage/RMSE checks;
evaluation fit calls0. No optional dependencies or publishing.

## Prediction intervals and failures

Per target, one calibration score per family: max absolute residual over15
labeled rows.95% order statisticrankceil(31×19/20)=30, no interpolation. Thus
widths are constant per target and contain no evaluation-based adaptation.
Coverage event: **all labeled rows in one new family with the same schedule**.
The450 rows are not450 independent calibration samples. No null labels occurred
in this realization; missing-label/excluded-family handling is tested separately.

| Target | Unit | Half-width q | Full width |
|---|---|---:|---:|
| Mean power |mW|13.3224|26.6448|
| Total energy |mJ|177.3732|354.7464|
| Energy per delivery |uJ|6977.1561|13954.3121|

| Panel | Target | Covered families /30 | Family coverage | Row coverage /450 |
|---|---|---:|---:|---:|
| Nominal |Power|28|93.33%|98.89%|
| Nominal |Total energy|28|93.33%|98.22%|
| Nominal |Per delivery|26|86.67%|99.11%|
| Airtime-low |Power|26|86.67%|87.78%|
| Airtime-low |Total energy|30|100%|100%|
| Airtime-low |Per delivery|30|100%|100%|
| Airtime-high |Power|23|76.67%|78.89%|
| Airtime-high |Total energy|23|76.67%|89.78%|
| Airtime-high |Per delivery|24|80.00%|94.67%|

All panels use the same committed nominal q. Airtime1/10us per byte are explicit
assumption shifts from4 nominal, not measured current/timing variation. They
reuse30 evaluation families/random streams; do not count them as60 more groups.
High row coverage does not rescue failed familywise coverage. Full failed-family
IDs and failed run IDs per target/panel appear in
[evaluation.json](results/week8/evaluation/evaluation.json).

Split-conformal validity would require exchangeable family scores conditional
on the fixed model/design. Hash assignment is outcome-independent but cannot
establish exchangeability for deterministic configurations or fix shared model
bias. Thirty families also give coarse realized rates. These observed failures
are retained without widening q or trying another score. Stress results have
no distribution-shift coverage guarantee. Three target-wise95% procedures do
not imply simultaneous95% coverage. This is prediction uncertainty, not a
confidence interval for mean power, RMSE or aggregate coverage; no metric CIs
or row-level bootstrap are reported.

Point RMSE (same frozen Week7 models, no refit):

| Panel | Power mW | Total mJ | Per delivery uJ |
|---|---:|---:|---:|
| Nominal |5.7813|48.5603|2027.3085|
| Airtime-low |7.9969|49.9187|1899.8033|
| Airtime-high |15.6429|117.9744|2848.6485|

Saved4050 interval records =3panels ×3targets ×450rows. There are1350 source
runs but only30 evaluation families reused across panels. This study's calibration
and evaluation sets are now consumed for future design decisions.

## Signed contributions and permutation importance

Reference is each model's original training means and intercept. Signed terms
beta×(x-mean)/scale have target units, sum with the intercept to prediction and
are stored for every nominal evaluation row. Top3 by global mean absolute term:

| Target | First influence | Second | Third |
|---|---|---|---|
| Power mW |Interval4.8631|Payload4.5908|Duration0.0401|
| Total mJ |Duration465.9793|Interval25.8607|Payload24.6732|
| Per delivery uJ |Interval15890.7372|Payload534.6828|Duration174.0957|

Per-record signs and top3 vary with position relative to training means; the
machine artifact retains all of them. Constant TX contributes0. Raw feature
units are bytes,ms,dBm,ms; contribution values are energy/power units above.

Held-out permutation uses20 fixed hash permutations of whole family repetition
blocks within each duration. RMSE increases, mean ±populationSD across repeats:

| Target | Interval | Payload | Joint payload+interval |
|---|---:|---:|---:|
| Power mW |5.1180 ±0.4749|3.1068 ±0.3830|7.1249 ±0.5758|
| Total mJ |21.0381 ±2.6462|12.7013 ±2.1510|30.8308 ±2.7855|
| Per delivery uJ |25961.8271 ±1450.6730|152.3214 ±38.1622|26292.5749 ±1646.4909|

Interval ranks1 and payload2 in all20 repeats for all targets. Raw third rank
is a zero tie, assigned to TX by feature order. **Duration is held fixed by this
permutation policy and is not identifiable by it**; its recorded0 is not evidence
of irrelevance. TX is actually constant in this scope. The duration contribution
and ablation for total energy demonstrate this blind spot; we do not modify
permutation policy after observing evaluation outcomes.20-repeat SD/ranges/ranks
are perturbation stability, not sample confidence or physical certainty.

Joint substitution complements the single-feature view but is not conditional
importance or interaction identification. Feature dependencies can mask/share
credit; hybrid X may break correlations or combine support points not present
in the assessment subset. Every hybrid remains on the frozen Cartesian workload
support with a full-slot schedule. Outcomes are not regenerated for hybrids;
importance measures fitted-model sensitivity, never physical causation.
[explanations.json](results/week8/evaluation/explanations.json) contains exact
method/seed, all repeats/ranks/ranges, signed rows, units and source/model hashes.

## Predeclared ablations

Each omission was refit using360 original Week7 training labels, selected
alpha1(power)/0.01(energy targets), train-only scaling and no parameter search.
Feature masking is explicit in [frozen artifacts](results/week8/ablations/ablations.json).
No fresh calibration/evaluation labels entered fitting; no frozen model was replaced.

Nominal RMSE (parentheses: increase relative to frozen model):

| Removed feature | Power mW | Total mJ | Per delivery uJ |
|---|---:|---:|---:|
| Payload |7.1749 (+1.3935)|54.0537 (+5.4934)|2267.4303 (+240.1218)|
| Interval |9.5340 (+3.7527)|63.2306 (+14.6703)|21154.4891 (+19127.1807)|
| TX |5.7813 (+0)|48.5603 (+0)|2027.3085 (+0)|
| Duration |5.7833 (+0.0019)|554.2993 (+505.7390)|2109.6458 (+82.3373)|

These are diagnostics of how this model recovers generator formulas. They do
not select a new feature set, revise an interval or demonstrate radio causation.

## Reproduction, tests and Week9 gatekeeper readiness

[Workflow/API documentation](green-ops-week8.md) has end-to-end commands.
[Reproduction script](results/week8/reproduce.py) verifies saved exact bytes,
frozen settings, interval arithmetic, coverage/failures and RMSE independently.
[Prediction example](results/week8/prediction-example.json) uses the
lexicographically first nominal evaluation run, power target, with its exact
[CLI command](results/week8/prediction-demo-command.json); no outcome-based choice.
Default point CLI behavior stays version1; explicit interval flags produce
version2 with compatibility hashes. Outputs reserve new destinations and do
not overwrite inputs or previously saved outputs.

284 tests pass (14 new), ResourceWarning errors enabled. Coverage includes
finite-sample rank boundaries, insufficient/no-label families, state/source and
v2 table replay, semantic/seed separation, calibration/ablation/evaluation leakage
guards, artifact mismatches, serialization, deterministic block permutations,
independent contribution accounting and safe default/extended CLI output. Exact
study rerun passed. Final compatibility checks pin the independently regenerated
release dataset digest and exact evaluation seed/run schedule; altered claims
are rejected without changing any saved interval or score.

Ready to build a **research-only gatekeeper** with explicit model/feature/source/
calibration compatibility, provenance and abstention checks. It should surface
scope shifts and missing inputs, expose failed nominal family coverage, and
avoid claiming calibrated95% hardware assurance or automatically acting on
these intervals. The current intervals fail the nominal familywise target;
this is a blocking limitation for an assurance/physical deployment claim.

Any new interval method/model tuning must use these now-consumed sets as
known development data and reserve genuinely new parent-disjoint final data.
Hardware measurements with aligned power/delivery windows, source-appropriate
currents/timings/loss validation, and separate physical calibration/evaluation
remain required. Gatekeeper decision policy/safety thresholds need their own
predeclared validation; this week implements no hardware actuation or deployment.
