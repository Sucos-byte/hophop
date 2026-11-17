# Green-Ops progress — 15 ECTS / 450-hour scope

## Revised four-phase roadmap

Scope: 15 ECTS / 450 hours, as reported by the project owner. This is a planning budget, not a record of hours already worked. Project weeks are work packages, not verified calendar weeks. Record actual effort separately; do not infer effort or overall completion from test counts.

```text
PHASE 1  Foundation and measurement contract
Week 1   Firmware telemetry                 [##########] Complete software scope
Week 2   Log pipeline + run metadata        [##########] Complete software scope
Week 3   Planner + loss simulation          [##########] Complete software scope
Week 4   Dataset builder + synthetic demo   [##########] Complete software scope
Week 5   Feature/window/table contracts     [####------] Software contracts, table CLI and demos complete; lab evidence pending

PHASE 2  Analytical data and learning
Week 6   Analytical reference generator     [##########] Reference software complete; physical validation pending
Week 7   Regression + grouped evaluation    [##########] Analytical software pilot complete; validation limits recorded
Week 8   Uncertainty + explainability       [----------] Planned; laptop executable

PHASE 3  Regression policy and CI
Week 9   Budgets + battery forecasting      [----------] Planned; laptop executable
Week 10  PR report + GitHub Actions         [----------] Planned; laptop executable

PHASE 4  Fault-injection benchmark
Week 11  Five fault families + baselines    [----------] Planned; laptop executable
Week 12  Benchmark + reproducibility report [----------] Planned; laptop executable

LAB      Physical calibration/validation   [----------] Parallel track; lab access required
Review   Draft PR #101                     [??????????] Current status unverified
```

### Budget and deliverables

| Phase | Planned hours | Deliverables and acceptance evidence |
|---|---:|---|
| 1, Weeks 1–5 | 130 | Existing foundation plus leakage-aware feature registry, bounded measurement windows, multi-run matrix, acquisition protocol; contract tests and migration report |
| 2, Weeks 6–8 | 150 | Sourced analytical parameter profiles; deterministic generator; stdlib regression baselines and optional sklearn ensembles; grouped validation, uncertainty and ablations; explainability report |
| 3, Weeks 9–10 | 95 | Policy gatekeeper; explicit battery assumptions; Markdown reports; Rust/Python/ARM CI and smoke evaluation; exit-code and artifact evidence |
| 4, Weeks 11–12 | 75 | Five deterministic fault families; compliant controls; detection/false-positive benchmark; reproducibility package and final report |
| Total | 450 | Includes design, implementation, experiments, documentation and reporting; actual hours still need logging |

Physical calibration and validation effort is included within these allocations (principally Phases 1/2/4), not an extra 450-hour requirement. Rebalance after actual effort and lab scheduling are known. Suggested Week 5 allocation: 45 hours within Phase 1; remaining allocations for prior weeks are planning allowances, not claimed effort.

### Execution architecture and safeguards

1. Software proceeds using synthetic and analytical fixtures through training, reporting and fault gates. Hardware runs later enter the same versioned table interface through the hophop adapter.
2. Provenance is strict: unmeasured targets stay null; analytical rows use synthetic/simulation/analytical_simulation; measured rows require hardware provenance and validated aligned measurements. Analytical accuracy and measured accuracy have separate reports.
3. Week 5 versions the dataset contract. Analytical data generation is Week 6; Week 5 accepts that provenance only with a validated analytical-model reference. Existing schemas do not silently acquire new meanings.
4. Prediction-time feature availability depends on task. A pre-run predictor uses configuration and declared workload. A post-run diagnostic predictor may use validated headless execution telemetry. Counter outcomes and energy-derived values cannot silently enter a pre-run model.
5. Group splits keep repetitions, shared configurations, device/session captures and fault variants from leaking between train and evaluation sets. Fit preprocessing only on training folds. Report insufficient groups rather than inventing cross-validation results.
6. Uncertainty work distinguishes a confidence interval for a metric from a prediction interval for a run. Use held-out group evaluation, calibrated intervals and empirical coverage reports; 95% is a nominal level, not guaranteed hardware coverage.
7. Explainability uses held-out permutation importance first, with optional model-specific contributions/SHAP later. Attributions indicate model sensitivity and do not establish physical root causes.
8. Battery forecasting uses explicit capacity, voltage, usable fraction, efficiency, workload duty cycle and aging/self-discharge assumptions. A five-year threshold is a configurable project policy. No EU compliance badge without an applicable instrument, scope and legal mapping.
9. Five faults: CPU busy-poll, TX power lock, bursty retry storm, beacon hyper-wakeup and fragmentation bloat. Faults modify workload/state traces before labels are computed. Evaluate all fixed energy-violating benchmark cases and compliant controls, including near-threshold cases. 100% detection is an acceptance target for this defined benchmark, not a general guarantee.
10. Nordic datasheet values need exact revision, section/table, voltage, temperature and mode. Unsupported DECT state timings or currents remain explicit assumptions/ranges, never borrowed silently from LTE values.

### Regulatory correction

The cited EU phone/tablet ecodesign regulation does not establish a universal five-year battery autonomy requirement for this project. It contains product-specific endurance and support requirements. Keep five years as an engineering budget policy pending applicability review.
Sources checked 17 November 2026: [European Commission overview](https://energy-efficient-products.ec.europa.eu/product-list/smartphones-and-tablets_en), [Regulation (EU) 2023/1670](https://eur-lex.europa.eu/eli/reg/2023/1670/oj/eng).

### Current handoff

Week7 analytical regression pilot is complete on green-ops/week7-ml-regression.
Entry9138511; recipe freeze6c4662e; data13b6064; coreea8fafd; workflow58cbe92;
frozen real selection8b18a39 BEFORE locked test/stress scoring. Full suite267
passes (21 new Week7 tests), ResourceWarning errors enabled. Results:
../green-ops-week7-results.md; workflow: ../green-ops-ml-regression.md.

540 primary rows /36 families,24/6/6 split, plus180 separate stress rows.
Test RMSE:6.3664mW power,51.1850mJ total energy,991.1826uJ per delivery;
power stress R2 only0.169–0.264. Models/selection stayed unchanged after test.
All results analytical_simulation, not hardware accuracy. Week8 may begin
software uncertainty/explainability only after a new independent calibration/
evaluation design; current validation/test/stress are already consumed.
Current/next step: green-ops-week7-handoff.md. Actual hours remain unreported.

The historical status below records completed evidence. Its hardware-dependent model-training wording is superseded by the revised software/lab separation above.

Updated: 17 November 2026. Based on commits and command results confirmed in this chat.
Percentages refer to the agreed software deliverables for each project week, not calendar time or total research completion.

```text
Week 1  Firmware telemetry                [##########] 100%
Week 2  Log pipeline + run metadata       [##########] 100%
Week 3  Planner + channel-loss simulation [##########] 100%
Week 4  Dataset builder + workflow guide  [##########] 100%
Lab     Measurement readiness            [----------] Next
HW      Radio + PPK2 data collection      [----------] Awaiting lab access
Model   Training and evaluation          [----------] Software planned using analytical data
Review  Draft PR #101                     [??????????] Current status unverified
```

## Latest milestone

PPK2 v2 checkpoint: 25b1aaa committed and clean working tree reported; full suite 153 passing tests. Bounded energy/power/duration consistency and alignment-policy validation are implemented, including tolerance boundaries. Dataset v2 integration remains next. User requests native autonomous coding; current Windows session execution check returned Wsl/E_ACCESSDENIED. Native WSL handoff instructions saved in green-ops-native-handoff.md.

Week 5 checkpoint: bounded measurement windows, explicit baseline subtraction, strict JSON loading and unique logical packet delivery evidence committed as c97ec4e. User confirmed a clean branch and 100644 modes. Latest full suite: 137 passing tests. V1 feature contract previously committed as ef0470f (120 tests at that checkpoint). Saved synthetic window fixture validation was part of the guided handoff; no physical measurement is claimed. Progress bar blocks indicate completed increments, not an hours-based percentage.

The synthetic saved-log-to-dataset workflow passed end to end. It produced one unmeasured row, two counter segments, expected counters, and empty energy targets. The latest reported full suite passed 106 tests.

## Confirmed milestones

| Stage | Result | Evidence |
|---|---|---|
| Week 1 | Optional firmware telemetry and embedded build | cd229c1; eight telemetry unit tests reported passing |
| Week 2 | Validated saved-log pipeline and run metadata | 0817338; c92a92f |
| Week 3 | Deterministic planner and Gilbert–Elliott scenarios | e7a1d27; 15f2ec0; 60 tests reported passing |
| Week 4 Task 1 | Strict PPK2 summary validation | 9e97e9c |
| Week 4 Task 2 | Segment-safe counter aggregation | 4a60635 |
| Week 4 Task 3 | Energy dataset rows | 32d50a3 |
| Week 4 Task 4 | Validated artifact joining | 149cefc |
| Week 4 Task 5 | Dataset CLI and output reservation/rollback | 16f42b5; 106 tests reported passing |
| Week 4 documentation | Workflow guide completed | f331e11, following initial 8d9f64a |
| Week 4 demonstration | Reusable synthetic metadata and successful pipeline | 35ce7f3; clean Week 4 branch confirmed by user |

## Pipeline

```text
Experiment plan + run metadata + telemetry events
                      + optional PPK2 summary
                                  |
                                  v
                  Validated dataset row + manifest
                                  |
                                  v
             Measurement review and dataset acceptance
                                  |
                                  v
                    Model training and evaluation
```

## Next milestone: measurement readiness

- Define run start/end and the energy capture interval.
- Establish counter baselines and handle captures starting mid-run.
- Define packet delivery using sender/receiver evidence; receive attempts are not transmitted packet counts.
- Align energy measurements with the packet-count interval.
- Document instrument setup, voltage, calibration, and repeatability.
- Decide which features exist at prediction time to prevent target leakage.

## Interpretation limits

Week 4 software completion does not establish hardware integration, measurement validity, or training readiness. Current delivered_packets counts decoded receive packets. Current packet_delivery_ratio divides decoded packets by receive attempts. Neither establishes end-to-end delivery. Plan settings describe requested settings rather than independently verified radio configuration. Simulation and synthetic fixtures remain explicitly labeled. Energy labels require real measurements covering the same interval as the packet counts.

## Update routine

Update this file when a milestone is confirmed in the chat. Record the commit, check results, remaining limitations, and next step. Announce milestone completion in the response. Remote review status requires a fresh check; do not infer it from the historical screenshot.


## Native execution checkpoint — dataset v2

Verified branch `green-ops/week5-measurement-contract`, HEAD `25b1aaa`;
only the supplied `docs/plans/` files were untracked at entry. No applicable
AGENTS.md found. Baseline suite was 153 passing tests (provided evidence).
Implemented explicit dataset v2 row/file APIs, strict joins and bounded
counter observations, unique delivery denominators, propagated duration policy,
v2 registry coverage, CLI flags and hashed manifest. V1 regression behavior is
preserved. Full suite: 165 tests passing with ResourceWarning as errors;
`git diff --check` passes. No hardware measurements were performed.
Next: strict dataset artifact validator and provenance-filtered multi-run table.
Actual research hours have not been supplied and are not inferred.

Dataset v2 committed as `822679f` (165 passing tests). Task 4 implemented:
strict typed CSV/manifest loading, CSV digest and identity checks, analytical
reference checks, deterministic provenance filtering, target missing policies,
null preservation and duplicate rejection. Eight focused table tests pass.
The table validates summary contracts and byte identity, not physical truth.
Next: table CLI and atomic output integration.

Task 4 committed as `c037dd8`. Task 5 table CLI implemented with explicit
provenance selection, repeatable source pairs, deterministic output digest,
source/output alias checks and two-output reservation/rollback. Five focused
CLI tests pass, including a simulated second-publication failure. No physical
or analytical model accuracy is claimed. Next: protocol and runnable demos.

Task 5 committed as `f119f2d`. Task 6 acceptance demo passed at
`/tmp/green-ops-week5-demo`: two distinct synthetic runs/groups with null energy
and RTT, plus two separate analytical contract-test runs/groups. Added saved
source fixtures, fresh-directory runner, migration/table guide and acquisition
protocol with official Nordic sources checked 17 November 2026. Board revision,
wiring review and all physical acquisition remain pending; no board pin mapping
or DECT current values were guessed. Incoming full baseline SHA:
`25b1aaab3ead347de94fa66f0e662b9500ea86a4`. Latest full suite at this checkpoint:
178 passing tests. Final validation review added strict numeric-token, manifest
selection and integer-energy overflow checks; 16 focused table/CLI tests pass.
Final full suite and local verification commit follow.


## Week 5 final software verification

Task 6 committed as `637afb0`. Final review tightened nondecimal CSV token
rejection, unknown/selected-feature manifest checks, integer-energy overflow,
measured row consistency against declared duration policies, and non-object
PPK2 errors. Full suite: **182 tests passing**, ResourceWarning as errors;
`git diff --check` passed. Demo sources/artifacts remained explicitly synthetic
or analytical contract-test evidence. Tasks 0–7 are complete for software scope;
no push/publish performed. Research hours and physical calibration remain
unreported/pending, rather than inferred from test counts.


Final validation changes committed as `e064cfa`; 182 passing tests. The native
handoff now records completed Week 5 milestones and separates the next planned
Week 6 generator from the fixed analytical contract fixtures. Documentation-only
checkpoint follows; no unchanged-suite rerun is required.

## Week 5 independent code review checkpoint

Reviewed `25b1aaa..eb6e936` against the approved plan and reproduced concrete
failures before corrections. Fixed implicit capability/pre-run duration leakage,
missing delivery-summary provenance, opaque-hash-only hardware RTT acceptance,
parse/hash file rereads, integer numeric-target precision loss, malformed CSV
acceptance, and unchecked policies on excluded nonmeasured sources.

Feature contract version is now **3** (dataset v2 and v1 APIs/field order stay
unchanged). Older v2 manifests must be regenerated with explicit prediction
context; omitted context declares no prediction capabilities. Recorded early-
terminated runs cannot select pre-run profiles. Hardware RTT stays null pending
a correlated-evidence validator. Full details: `green-ops-week5-review.md`.

Verification: **197 tests pass**, including 15 new targeted review tests, with
ResourceWarning errors enabled. `git diff --check` passes. The two-row synthetic
and separate two-row analytical contract-test demos pass in
`/tmp/green-ops-week5-review-demo`. No hardware evidence or accuracy is claimed.
Week 6 is ready for implementation of the sourced analytical generator;
calibrated hardware accuracy and scientifically validated training remain
pending. No actual effort hours inferred; no push or publish.

Review corrections committed locally as `18a9589` (`Fix Week 5 evidence,
prediction context and artifact integrity gaps`). Working tree verified clean
at that checkpoint; full-range diff check from `25b1aaa` passes. The final
tracker-only commit does not change the verified code or require another suite
run. No push/publish performed.

## Week 6 started — source/plan milestone

Verified clean entry at `1726971dd46b67c45e9e23aa0b50b91000dc64a3` and
created `green-ops/week6-analytical-reference`. Read instructions/current APIs
and Week 5 review; no applicable AGENTS.md. Plan saved in
`green-ops-week6-plan.md`. Official Nordic HTML revision history and DECT current
sections are accessible: PS 1.1 (June 2025), minimum-latency typical TX/RX/idle
currents under pinned conditions. Exact audit: `../green-ops-analytical-sources.md`.
No LTE current substituted. Timings, loss, optional RTT and uncertainty ranges
remain assumptions. Current task: versioned profile/core validation. Next step:
implement exclusive state-time accounting with independent energy oracles.
Incoming suite evidence remains 197 tests; no unchanged full-suite rerun.

Milestone 1 committed as `e2e8030`. Verified JSON parse and equality of all three
current values with the audited source catalog. Current task: strict model/
workload validation and core simulation. Next: independent energy/conservation
and invalid-input tests, then the core commit. See `green-ops-week6-handoff.md`.

Week 6 core milestone verified: analytical_reference.py has strict nonmutating
versioned model/workload validation, an explicit SHA-256 seeded loss sampler,
exclusive microsecond state traces, energy integration and optional assumed RTT.
Eleven focused tests execute and pass: independent charge/energy oracles,
conservation, zero/no/total loss, deterministic seeds, invalid inputs and source
conditions, overflow, and exact half-open end acceptance. Acceptance at end is
recorded as late and excluded from delivery. No measured evidence constructed.
Current task: commit verified core. Next: sensitivity + compatible analytical
artifacts/CLI and source-snapshot/hash/table integration tests.

Core committed as `d9de639`; 11 focused tests pass. Current task: sensitivity
and analytical artifact/API/CLI integration. Next: archive parameter/assumption
hashes and modeled packet evidence, validate via existing table APIs, then
commit that verified milestone. Incoming 197-test baseline remains preserved.

Week 6 artifact/sensitivity milestone verified: explicit analytical artifact API
and fresh-directory CLI archive exact source snapshots, model/parameter identity,
configuration and assumption hashes, seeds/groups, state and modeled packet
accounting, delivery summaries and one-at-a-time sensitivity. Existing strict
artifact/table APIs accept the generated bundles; no fake PPK2 is accepted.
Every nontrivial parameter range is exercised, with invalid schedules retained.

Verification: 25 analytical tests pass; including affected dataset CLI/publisher
checks gives 34 focused passing tests with ResourceWarning errors. Added numeric
overflow and safe-mean edge cases. Legacy publisher defaults remain unchanged;
exact-text publication is opt-in for source snapshots. Current task: commit this
verified milestone. Next: reproducible two-run workflow, documentation, final
full suite and scientific/compatibility review.

Artifact/sensitivity milestone committed as `9f13f8f`. Current task: final
workflow/demo/documentation and verification. Next: execute two distinct saved
workloads through generation and table CLI; run the full changed suite once,
review scientific claims and leave a committed handoff. 34 focused checks pass.


## Week 6 final verification milestone

Implemented deterministic standard-library reference generation with audited
Nordic DECT NR+ point currents, versioned parameters/source catalog/assumptions,
seeded modeled delivery, exact exclusive state time, energy integration, optional
assumed RTT, sensitivity, snapshot hashes and current artifact/table contracts.
Source audit documents full reference conditions and omitted overheads. No LTE
currents or fake measured PPK2 evidence were used. Current model is deliberately
limited to the specified minimum-latency reference conditions.

Acceptance workflow at `/tmp/green-ops-week6-demo` generated reference-001 and
reference-002, then an analytical-only two-row table. Verified per-input hashes,
seeds/groups, exact 1000000 us state sums, null default RTT and 18 sensitivity
cases per run. Independent TX-current sensitivity oracle passes. Final review
also handles zero-duration states without spurious numeric overflow.

Full suite: **224 passing tests**, including **27 new analytical tests**, with
ResourceWarning errors. Full diff check passes. Existing v1 APIs/CLI defaults,
dataset v2 fields and feature-contract 3 behavior remain intact. No publication,
training result, hardware accuracy or actual research hours claimed.
Current task: commit this verified final milestone. Next: immediately record
its actual hash and leave a completed/resumable Week 6 handoff. Future Week 7
training is separately planned; real calibration and independent evaluation
remain pending. Workflow: `../green-ops-analytical-reference.md`.


Final Week 6 software milestone committed as `c17c95d`; the verified code has
224 passing tests. All four plan milestones are complete for software scope.
Current task: final progress/resumption checkpoint (documentation only).
Next: physical calibration/independent model validation, or a separately
requested Week 7 implementation. No unchanged-suite rerun, push or publish.

## Week 6 pre-training review — correction milestone

Verified clean entry at `9ed6b96`, reviewed actual `1726971..HEAD` changes and
rechecked official Nordic revision/current/common-condition pages; sourced point
currents remain valid only under their pinned conditions. No LTE values used.

Found hidden pre-run workload/model variation, unchecked group/seed relationships,
missing full archived-source/replay audit before training, and intermediate
numeric overflow/underflow. Added analytical_design.py with a deterministic
full-slot grid, group-local seed derivation and conservative pre-training audit.
Related duration/repetition/parameter variants stay together; duplicated
realizations and cross-group shared seeds fail. Parameter-stress panels cannot
silently qualify as fixed-parameter primary data. General row/table/v1 APIs and
feature contract 3 remain unchanged. Generator arithmetic patch: 1.0.1.

45 focused tests pass, including 18 new review/design tests. Current task:
commit verified correction milestone. Next: larger fixed-parameter and stress
panel acceptance, final suite, review report and Week 7 dataset design. No
training/hardware results claimed. See green-ops-week6-review.md.

Review correction milestone committed as `f8c35bf`. Current task: multi-panel
acceptance and final documentation. Next: generate/audit 24 traffic families
with duration/repetition variants and separate model-stress panels, then final
suite and Week 7 readiness/design report. 45 focused checks pass.


## Week 6 review — final verification and readiness

Final review additionally guards caller-decimal-context independence, numeric-
spelling duplicate realizations, empty assumption documents and coherently
rehashed but incorrect sensitivity reports. Full suite: **246 tests pass**,
including **22 new review/design tests**, with ResourceWarning treated as errors.
`git diff --check` passes. No existing v1/dataset/table/feature contracts changed.

Executed and replay-audited 288 bundles under
`/tmp/green-ops-week6-review-panel`: 96 fixed-parameter primary rows (24 families,
48 pre-run configurations, 48 group-local random streams) and two 96-row timing-
stress panels sharing the same families. Primary table CLI accepts all 96 rows.
Combined panels correctly fail fixed-parameter primary readiness because hidden
coefficients differ. Original two-row demo remains compatible but fails the
full-slot offer-count policy. Results are synthetic software evidence only.

`green-ops-week6-review.md` records rechecked Nordic sources, all findings,
limitations and a proposed 540-primary / 36-family Week 7 design with frozen
24/6/6-family train/validation/test splits and 180 separate held-out stress rows.
Related duration/repetition/model variants and shared random draws stay within
groups; unknown parent lineage still needs explicit design declarations.
Current task: commit final verified review. Next: immediately record actual hash
and leave a resumable handoff; actual Week 7 fitting remains unperformed.
No push or publish; physical calibration and actual effort logging still pending.

Final reviewed corrections/report committed as `ba268d8` (initial correction
milestone `f8c35bf`). Verified code: 246 passing tests; 22 new review/design
cases; all 288 acceptance bundles replay-audited. Current task: completed review,
final documentation-only resumption checkpoint. Next: separately requested
Week 7 grouped software pilot, beginning with frozen dataset recipe/splits and
per-target audit. Physical validation remains pending. No push or publish.

## Week 7 started — frozen experiment

Verified clean baseline `9138511334218d147f1128d04b893eac7458725e`; created
`green-ops/week7-ml-regression`. Read actual APIs/instructions and Week 6 review;
no applicable AGENTS.md. Plan: green-ops-week7-plan.md. Frozen recipe at
tools/green_ops/recipes/week7-regression-v1.json records source hashes, exact
540+180 design, pre-run features/targets, 24/6/6 family splits, four training CV
folds, seeds and selection rules before any fit. Static count/isolation planning
assertions pass. Current: recipe/source freeze. Next: actual materialization and
audit, then standard-library numerical core. No training or held-out evaluation
yet. Incoming suite evidence: 246 passing tests; actual hours unreported.

Experiment freeze committed as `6c4662e`, before any fitting. Current task:
materialize/audit the frozen dataset. Next: commit actual count/hash/isolation
evidence, then numerical core and toy-data workflow tests. Test/stress scores
remain unobserved.

## Week 7 dataset milestone verified

Materialized/replay-audited all720 bundles at build/green-ops-week7/dataset:
540 primary rows (360/90/90 across24/6/6 families), 180 stress rows only in the
six test families. IDs, full-slot schedule, source hashes/provenance, pre-run
capabilities, family/CV membership and group-local seeds checked. Separate
primary and two stress CSV/manifest tables saved. Dataset SHA-256:
e921297009bc1b12ca325cf13dfc16fbf4e4c5013bceb28fd1dbd02b18b9cf98.
Recipe SHA-256:4a979b6cec4555c27d1813f33dc8481410e1ba2382dec2bb93b8366be32d1daf.
Audit archived at docs/results/green-ops-week7-dataset-audit.json. Five targeted
dataset tests pass. No design correction was necessary. No real-experiment
fitting or held-out scoring occurred. Current: commit data milestone. Next:
verified numerical core (toy tests only), then selection/evaluation workflow.

Data milestone committed as `13b6064`. Numerical core now verified on toy cases:
9 tests pass for independent ridge/mean solutions, rank deficiency/constant
features, train-only preprocessing, determinism, finite-input validation,
undefined R2, missing labels, strict JSON/model compatibility, source scope and
pre-run availability. Householder augmented QR avoids normal equations; models
retain negative predictions rather than clipping. Current: commit verified core.
Next: grouped CV/validation selection and locked evaluator/CLI using toy data
before the real experiment. Test/stress performance remains unobserved.

Core milestone committed as `ea8fafd`. Selection/evaluation/prediction workflow
now verified on toy data: guarded test/stress labels are never accessed during
selection; CV preprocessing uses fit groups only; locked scoring never refits;
serialization/hash checks, source scope, CLI prediction, output safety and
rollback pass. Full pre-experiment suite: **265 tests pass** (19 new Week7 tests),
ResourceWarning errors enabled; git diff --check passes. No real experiment
fit or held-out performance inspection yet. Current: commit verified workflow.
Next: train/CV/validation only, locally commit frozen choices/models, then locked
one-pass test/stress evaluation without tuning/refitting.

Workflow committed as `58cbe92` after265 passing tests. Starting the real
train/CV/validation-only stage now. Recipe, folds, raw feature profile and
candidate settings remain those frozen before fitting. Next checkpoint must
commit selection/models before any real test/stress score is inspected.

## Week 7 real selection checkpoint — before held-out scores

Real training/grouped CV/validation stage completed under frozen recipe. Choices:
mean power ridge alpha1.0; total energy ridge alpha0.01; per-delivery energy
ridge alpha0.01. No test or stress performance inspected. Exact selection digest:
31e53f4e8f4317be71bc8fed6b0024f0985a1cc5e195f4c833d43ae62acf226b.
All six baseline/chosen model hashes and selection-report hash verified; exact
snapshots copied to docs/results/week7-regression-v1/training. Selected models
remain fitted only on training labels (no train+validation refit). Current:
commit this choice before held-out evaluation. Next: locked evaluator once,
saved predictions/metrics, then documentation with honest results. No tuning.

Frozen real selection/models committed as `8b18a39`, before any real held-out
score was inspected. Selection digest31e53f4e8f4317be71bc8fed6b0024f0985a1cc5e195f4c833d43ae62acf226b.
Current: locked test/stress evaluation once with these exact model hashes.
Next: save/report predictions and metrics without refitting or tuning.


## Week7 final locked evaluation and verification

Frozen selection8b18a39 was evaluated once on90 test rows /6 families and two
90-row stress panels /same6 families. All three selected ridge models beat the
training-mean baseline on this analytical test; modest power testR2=0.6316 and
weak stressR2=0.1688/0.2641 are reported without retuning. Saved1620 baseline/
chosen held-out predictions, per-family errors and full units/counts/baseline
comparisons at docs/results/week7-regression-v1/evaluation. No missing energy
labels occurred in these real held-out panels; explicit missing-label exclusion
and null truth handling are independently tested. No clipping or refit.

Final compatibility review fixes only input/output provenance: retain the exact
consumed manifest snapshot digest, and require exact frozen recipe bytes plus
full-slot offers/frozen retry cap for prediction. These settings are absent
from X. Targeted tests reproduce/reject incompatible partial offers/retry caps.
Every real locked input already passed identical policy in dataset validation;
all270 passed the tightened guard. No estimator/scaler/settings/saved score
changed. Exact pre-test selection digest and all model hashes remain unchanged:
31e53f4e8f4317be71bc8fed6b0024f0985a1cc5e195f4c833d43ae62acf226b.

Final full suite267 passes (21 new Week7 tests), ResourceWarning errors enabled;
git diff --check passes. Workflow and results docs saved. Current: commit final
verified results/compatibility milestone and immediately record actual hash.
Next: Week8 separately requested work with new group-disjoint calibration and
assessment data; no uncertainty or explainability implementation performed.
Physical calibration remains pending; no actual effort hours, push or publish.

Final Week7 evaluation/results and prediction-compatibility milestone committed
as `ebd9998`. Frozen real choices/models remain byte-identical to pre-test
`8b18a39`; no held-out tuning/refit. Verified code267 tests passes (21 new),
ResourceWarning errors enabled. Current: completed Week7 software pilot, final
documentation-only resumption checkpoint. Next: separately requested Week8 work
with a new predeclared group-disjoint calibration/evaluation design. Existing
validation/test/stress are consumed; no calibrated uncertainty or physical
accuracy claimed. No push/publish; actual research hours unreported.

## Week7 review — verified correctness milestone

Review entry clean a2aeb15 on green-ops/week7-ml-regression; scope9138511..HEAD.
Fresh materialization/replay reproduced all720 sources, six models, selection,
reports and1620 predictions byte-for-byte. Independent checks verified216
preprocessing statistics, baseline means, labels, counts and MAE/RMSE. No
held-out fitting/tuning. Historical reproduction receipt/script retained under
docs/results/week7-regression-v1/review.

Fixed rounded-large-mean R2 variance (independent example expected -0.5,
previously0), with power-of-two scaling/offset centering and extreme-value tests.
New evaluation/selection reports explicitly use metrics_version2; old reports
remain readable. Also reject recipe-inconsistent model metadata and selection
reports contradicting frozen CV shortlist/validation winner, with targeted tests.
Full suite270 passes, ResourceWarning errors; follow-up report-version targeted
suite7 passes. Current: commit verified code/reproduction milestone. Next:
finish corrected report audit, Week7 review and fresh Week8 family design.
Original choices, model bytes and saved predictions remain frozen.

Verified review correctness milestone committed locally as6a35879. Full suite270
passes after report-version changes. Corrected replay confirms zero evaluation
fit calls; model bytes, choices,1620 predictions and all MAE/RMSE unchanged.
Only16 per-family R2 fields change at floating-point rounding scale in this
actual experiment; aggregate R2 unchanged. Original reports remain intact.
Current: archive corrected metrics/receipt and final review. Next: complete
fresh Week8 group design and documentation-only verification/commit.

## Week7 review completion

Final review saved docs/plans/green-ops-week7-review.md with code/API findings,
independent reproduction evidence, exact1620 breakdown and Week8 readiness.
Two corrected replays produce byte-identical reports/receipts. Archived metric2
reports explicitly replace historical R2 only; historical models/reports remain
untouched. Dataset/recipe/selection digests match; no held-out tuning/refit.
270 tests pass; strict JSON/archive checks and git diff --check pass.

Week8 proposal (no labels generated):60 new semantic traffic families using new
payload/interval levels,30calibration/30assessment,450rows each. Exact proposed
memberships recorded in review/week8-design-proposal.json. Checked zero overlap
against48 documented Week6/7 families and group-local streams. Before generation,
audit all prior/demo/parent lineage and freeze source/method/coverage policies;
new seeds alone are insufficient. Familywise calibration uses30 units, not450.
Same generating law remains a physical-validation limitation.
Current: commit final review/evidence milestone. Next: separately authorized
Week8 implementation after final lineage/recipe freeze. No push/publish.

Final review/evidence milestone committed locally asadcd44f (correction6a35879).
Current: Week7 review complete,270 passing tests; exact reproduction and fresh
Week8 proposal archived. Next: separately authorized Week8 work with final
lineage audit and recipe freeze before fresh calibration/assessment outcomes.
No push/publish; original selection/models/predictions unchanged.

## Week8 entry and pre-analysis freeze

Verified clean00c19c2; branch green-ops/week8-uncertainty-explainability created.
Read Week7 review/results/handoff/tracker and actual model/data/contract APIs.
Plan and recipe freeze60 new families,30calibration/30evaluation,900 nominal
plus900 evaluation-family sensitivity rows. Prior inventory3460 source files,
48 excluded families; zero semantic overlap. Two unkeyed v1 parser demos have
no configured workload or energy labels, explicitly resolved in lineage snapshot.
Frozen raw family-max absolute residual95% rank rule,20 block permutations,
signed training-mean contributions and four fixed-alpha leave-one-feature-out
ablations. No new outcomes generated/scored. Week7 models/selection unchanged.
Current: commit pre-analysis freeze. Next: implement/test strict study APIs and
numerical methods, then fit ablations/calibration before evaluation. No push.

Pre-analysis freeze committed3e0dd39. Implemented separate Week8 dataset replay,
family-max quantile calibration, signed contributions/block permutation and
original-training-only ablations. Optional prediction interval flags preserve
default v1 output. Current: targeted tests including full source replay and
leakage guards; no real-study calibration/evaluation analysis run yet. Next:
fix verified test failures, commit code, then materialize and fit frozen ablations.

Week8 dataset materialized/replay-audited1800 bundles:450 nominal calibration,
450 nominal evaluation and900 sensitivity rows,30+30 disjoint groups. Existing
v2 table hashes match; no model fitting or evaluation scores inspected in data
milestone. First full suite284 passes (14 new tests); strict explanation summary
checks subsequently tightened, final same-suite verification underway. Tests
exercise fixed-study invariants/determinism without printing performance scores
or selecting methods. Current: final code verification; next: commit dataset/
methods then fit real ablations, commit, then calibrate/commit before evaluation.

Final full suite284 passes after strict contribution-summary checks (14 new),
ResourceWarning errors enabled; diff check passes. Numerical independent expected
values, rank boundaries, no-label/insufficient families, source tampering,
serialization, model/split/source mismatches, block permutation, contribution
accounting, no-fit evaluation and both leakage boundaries tested. Current:
commit verified methods/dataset milestone. Next: real fixed-alpha ablation fits
on original training only, commit, then calibrate/commit before locked scoring.

Verified methods/dataset milestone committed6da8dba. Current: actual ablation
command replay-validates Week8 and original Week7 sources, then fits only old
training labels with selected alpha; no new-data label fitting. Next: freeze
its artifact locally, then actual calibration threshold stage and commit.

Actual diagnostic ablations complete:12 fits (4 omissions ×3 targets),360 old
training labels each; alpha1 power/.01 energy targets, exact original run IDs.
Artifact archived docs/results/week8/ablations/ablations.json, binds original
and study dataset/recipe/model/split hashes. No calibration/evaluation label
used for any fit. Current: commit immutable ablation artifact. Next: nominal
calibration-family scores only, freeze/commit thresholds before real evaluation.

Ablation artifact committed3e491f9 before actual calibration. Current: calibration
command reads only450 nominal calibration labels; no evaluation target access.
Next: archive/commit three thresholds and hash inventory, then locked evaluation.

Calibration complete using450 rows/30 nominal calibration families per target,
no null labels/excluded families in this realization. Finite95% rank30 family
max scores; strict three calibration artifacts and inventory archived. No
threshold/method selection. Current: commit frozen calibration artifacts before
actual locked evaluation. Next: nominal+assumption-shift coverage, explanations
and predeclared ablation diagnostics without fitting or threshold changes.

Calibration committed4d66d51 before actual evaluation. Fixed half-widths:
13.322407099mW,177.373200203mJ,6977.156057690uJ. Current: locked actual
nominal/sensitivity scoring with these exact thresholds, original models and
committed diagnostic ablations. No fit/selection/recalibration in evaluator.
Next: archive results, independent replay/accounting, honest interpretation.

Locked results available, unchanged thresholds/models: nominal family coverage
28/30 power,28/30 total energy,26/30 per-delivery (93.3%,93.3%,86.7%); all below
nominal95%. High-airtime shifts23/30,23/30,24/30; no interval adjustment.
Saved4050 interval predictions (1350 runs ×3 targets; only30 evaluation families,
reused in stress). Explainability/ablation results retain policy blind spot:
within-duration permutation cannot vary duration, so zero importance there is
unidentifiable, not irrelevant; signed contributions/ablation expose strong
energy duration dependence. Current: independent replay and honest results docs.
Next: commit final report/evidence and gatekeeper-readiness handoff, no tuning.

Independent replay verifies exact ablation/calibration/evaluation bytes,4050
unique interval predictions and independent bounds/coverage/failure/RMSE checks;
second1800-bundle generation matches inventory/audit/sources/tables exactly.
Final compatibility review pins this independently reproduced release dataset
digest for single-record interval prediction, preventing an otherwise well-formed
calibration from claiming a different dataset. Added CLI/default-binding rejection
checks. This changes only provenance acceptance, no source/model/threshold/score
or saved output. Current: affected final-suite and exact replay verification.
Next: verified local final results/provenance commit and Week9 handoff.

Final interval compatibility additionally binds the exact declared seed/run
schedule, preventing extra realizations from silently expanding the15-row
family event. Default point API remains unchanged. Targeted test mutates a seed
and rejects the interval; release suite/replay underway. All saved1800 workloads
already satisfy this identity; no threshold, attribution policy or score changes.

## Week8 completed results and release verification

Release full suite284 passes (108.5s), ResourceWarning errors enabled; includes
both final metadata guards. Exact replay after guards preserves every archived
ablation/calibration/evaluation/prediction byte; independent regeneration receipt
and strict finite/duplicate-free JSON checks pass. All six Week7 model hashes
and selection digest unchanged. No evaluation tuning or numeric correction.
Results docs/green-ops-week8-results.md retain poor family coverage and duration
permutation blind spot. End-to-end CLI example and4050 interval records saved.
Current: commit final verified results/compatibility milestone. Next: separately
authorized Week9 research-only gatekeeper; physical/hardware95% assurance gate
not satisfied. All calibration/evaluation/stress now consumed. No push/publish,
no hardware actuation, no inferred research hours.

Final verified Week8 results/compatibility milestone committed541bda5.
Current: Week8 complete,284 tests and exact replay pass; all results remain
analytical_simulation and original Week7 models/selection unchanged. Next:
separately authorized Week9 research gatekeeper, with explicit coverage failure,
provenance/scope/abstention rules and no hardware assurance claim. No push/publish.

## Windows planning-chat status export setup

Read external green-ops-status-export-instructions.md. Recorded standing refresh
policy in docs/plans/green-ops-status-export.md and Week8 handoff: after verified
milestones/local commits, before user input, before stopping. Export is one-way,
UTF-8 temporary sibling followed by atomic replacement. Tracker stays authoritative;
no background agent, polling or remote notification. Current Week8 complete at
c78705f, clean before these documentation edits; tested source unchanged (284
release tests, code committed541bda5). Current: commit setup docs then publish
fresh exact branch/HEAD/status snapshot. Next: separately authorized Week9 work;
no completed coding task restarted and no unchanged-code tests repeated.

## Week9 entry and policy-semantics freeze

Verified clean340a5b7; created green-ops/week9-gatekeeper. Read authoritative
tracker, Week8 results/handoff, actual APIs and standing Windows export rules.
Plan/default policy freeze statuses/exits, interval boundaries, logical marginal
regression comparison (no calibrated difference claim), default coverage abstention,
two-part explicit research override, compatible workloads and battery units/loss
accounting. Observed nominal family coverage28/30,28/30,26/30 inadequate95%;
assumption shifts have no coverage guarantee. No retraining/recalibration/tuning.
Current: commit plan/default policy; next implementation/tests. Latest verified
source remains284 Week8 tests (541bda5); new policy/docs only, not code verified yet.

Semantics/default policy committed060a7fc; Windows snapshot refreshed atomically.
Implemented strict policy/evidence adapter, PASS0/ERROR1/FAIL2/ABSTAIN3 engine,
logical marginal comparisons and explicit battery energy/loss accounting.20
new targeted tests pass (0.4s), including allowance one-ULP excess protection,
all exits, coverage/shift overrides, contexts, hashes/tampering and publication
rollback. Current: full suite underway, no frozen model/calibration changes.
Next: verified implementation commit/export, then reproducible research demos.

Week9 implementation verified: full suite304 passes (20 new,107.0s),
ResourceWarning errors enabled; diff check clean. Strict source replay/frozen
hash evidence, conservative uncertainty/status rules, explicit loss/duty battery
projection, all exit codes and rollback tested. No old source/model/calibration
modified. Current: commit implementation and refresh Windows snapshot. Next:
execute/reproduce8 labeled policy demonstrations and document Week10 readiness.

Implementation committedbbc187c; Windows snapshot refreshed atomically. Initial
8 labeled research demos pass expected exits using unchanged same frozen source:
PASS0 generous explicit override,FAIL2 strict ceiling,ABSTAIN3 crossing/default
coverage/missing workload,ERROR1 invalid units; battery5-year target fails and
same-feature regression reports0% (not code observability). Current: enrich
report audit fields with resolved workload/context/domain and explicit no-hardware
assurance flags; rules/predictions unchanged. Next targeted/full report checks,
final reproducible demos/docs and milestone commit/export.

Final report audit fields verified by21 targeted tests; final full suite underway.
Two independent8-case demonstration runs are byte-identical across source,
policies, reports and summary; final snapshots archived docs/results/week9.
Default coverage abstains; research-only generous budget passes, strict budget
fails, crossing abstains, invalid units errors. Battery1000mAh/3.6V/.8usable/
.9efficiency, continuous148.06013mW =>0.00199708years (range.00183222-.00219454),
configured5years fails; no workload abstains. Same features +different commit
labels yield0% point regression, explicitly not execution observability.
Current: final suite/strict JSON/hash checks; next verified results commit/export,
Week10 readiness handoff. No tuning, physical measurement or deployment.

## Week9 final verification and readiness

Release full suite305 passes (21 new,108.867s), ResourceWarning errors enabled;
strict JSON, report-hash/exit/block flags, frozen six model/selection and
calibration hashes verified; git diff --check passes. Independent demos byte-
identical. Results/docs/API contract and reproducible fixtures saved; no source,
model, calibration or evaluated-set tuning. Default-policy coverage abstention,
explicit research overrides, battery shortfall and commit-only non-observability
reported honestly. Current: commit verified final evidence and refresh Windows
snapshot. Next: separately authorized Week10 CI/full PR reporter, preserving
0/1/2/3 and blocking FAIL/ABSTAIN/reporting errors. No Actions/PR Markdown,
physical measurement, deployment, push or remote publication in Week9.

Final verified Week9 results/report-audit milestone committedd60a1eb; Windows
snapshot refreshed after the commit. Current: Week9 complete,305 release tests
and independent exact demos pass; tested code isd60a1eb. No pending implementation.
Next separately authorized Week10 CI/full PR Markdown reporter, preserving strict
status exits and research/evidence limitations. No push, remote publication,
deployment or hardware action. Final handoff-only checkpoint follows; export it
before stopping. Repository tracker remains authoritative.

## Week10 entry and reporting/CI plan freeze

Verified cleanb2b6c08; created green-ops/week10-ci-reporting. Read tracker,
Week9 evidence/APIs, workflows/manifests/test scripts and firmware setup docs.
Plan freezes strict SHA/policy/schema report validation, safe escaped Markdown,
status-preserving wrapper and software-only expected-default-ABSTAIN smoke.
No approval semantics hidden by CI success. Inspectable actual toolchains
Rust1.99.1/Python3.14.4; offline host default test passed using existing exclusions.
Third-party pins verified from official GitHub release/commit pages; shell Git
network DNS unavailable. Current: commit plan; next implementation/tests, workflow
and local validation. No source/models/calibration edits, push or remote posting.

Plan freeze8b65a64 committed; Windows snapshot refreshed. Implemented strict
hash/policy-bound Markdown validator/renderer, atomic JSON+Markdown gate wrapper,
software-only expected-default-ABSTAIN smoke.32 targeted reporter+gate tests pass
(11 new), including all statuses, escaping, missing attributions, units/hashes,
collisions/rollback and exact gate exits; renderer failure blocks1. Current:
full Python suite underway; next verified code commit/export and workflow/builds.
Only gate parser extraction refactor; decision semantics/models/calibration unchanged.

Reporter/wrapper release full Python suite316 passes (11 new,108.6s), ResourceWarning
errors enabled. Software smoke verifies exact defaultABSTAIN3/no override and
byte determinism; no candidate approval. Reusable Rust host/default+all-features,
8 telemetry tests and ARM no_std compile pass locally with installedstable=1.99.1.
Workflow YAML parse/duplicate/security-contract checks pass (optional localPyYAML);
actionlint absent, no remote execution. Firmware enabled normal attempt DNS-failed;
cache-only retry passed. Disabled cached build underway. Current: commit verified
reporter code then workflow/build milestone; next eight-status rendering evidence.
