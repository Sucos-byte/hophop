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
Week 7   Regression + grouped evaluation    [----------] Planned; laptop executable
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

Week 6 software and pre-training review are complete on
`green-ops/week6-analytical-reference`. Original checkpoint: `9ed6b96`; initial
review corrections: `f8c35bf`. Generator arithmetic patch: 1.0.1; v1/dataset v2/
feature-contract 3 remain compatible. Latest full suite: 246 passing tests,
ResourceWarning errors enabled (22 new review/design cases). Final review and
training design: `green-ops-week6-review.md`.

Audited acceptance: 96 primary rows plus 192 separate stress rows, 24 declared
families, source/state/packet/sensitivity replay verified. The two-row demo and
indiscriminately pooled parameter variants are not primary training designs.
Week 7 is ready for a fixed-scope grouped software pilot after freezing its
recipe/splits: proposed 540 primary rows / 36 families plus 180 held-out stress
rows. No fit, hardware accuracy or physical-validation readiness is claimed.
Current/next-step handoff: `green-ops-week6-handoff.md`. Actual hours unreported.

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
