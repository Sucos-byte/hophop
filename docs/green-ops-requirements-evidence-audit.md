# Requirements and evidence audit — 17 November 2026

Entry: clean `b48c91d7cc08f21f0bee7f44074f224c3fa2b3f9`; branch
`green-ops/observability-design`. This is a source-based audit/design, not a new
experiment or completion claim. The [tracker](plans/green-ops-progress.md) is
authoritative; earlier progress bars/“complete” refer to individual software
packages. Their historical “planned” headings are not current evidence status.

## Requirement authority and unavailable originals

Available sources reviewed: [native handoff](plans/green-ops-native-handoff.md),
[Week5 plan](plans/green-ops-week5-plan.md) and review, Week6–12 plans/reviews/
handoffs, [project summary](green-ops-project-results.md), [Week12 results](green-ops-week12-results.md),
firmware sources and actual Python contracts/tests. The external planning root
`/mnt/c/Users/thite/Documents/Codex/2026-11-10/superpowers-plugin-superpowers-openai-curated-remote/`
contains `green-ops-week4-plan.md`, copies of the Week5 plan/native handoff,
`green-ops-interim-technical-report.md` and `green-ops-gap-audit.md`, all read.
The Windows assessment explicitly derives from the export, not independent code
inspection; its findings here are checked against repository interfaces. An
inventory with SHA-256 is in `docs/results/observability-design/source-audit.json`.

**Unavailable:** original signed project proposal/title-page specification,
supervisor-approved detailed requirements/rubric, original exact18-feature list,
original100ms timing/error tolerance specification, primary Week1–3 plans and an
actual student effort log were not found in repository docs or the inspected
external planning root/outputs. No exact filename for these missing originals
is established; do not invent one or infer their contents from later summaries.
The inspected source/package copies are secondary implementation history, not a
replacement signed brief. Search scope is local available planning sources,
not every student/cloud/archive location. The 18-feature/100ms ambition is
attested in telemetry/log-parser limitations and the Windows assessment; its
complete original definition/mandatory status is unresolved. The15ECTS/450hours
scope is owner-reported in the tracker, not independent academic certification.

The upstream [hophop vision](../doc/vision.md) explicitly describes aspirations,
including several backends. It is not evidence Green Ops already works on those
platforms. “Proposed acceptance” below is this audit's recommendation requiring
scope reconciliation; it does not silently replace original requirements.

## Traceability matrix

Evidence states: **software** means inspected implementation and recorded tests;
**analytical** means simulated experiment; **open** means objective not established;
**decision** means original authority/scope needs reconciliation. No row marked
software implies physical effectiveness. Test references identify actual files;
no new tests were added for this documentation-only task.

| ID / requirement and source | Implementation inspected | Tests / checks available | Experimental evidence | Remaining gap / state | Proposed acceptance criterion |
|---|---|---|---|---|---|
| R01 Energy regression detection; tracker safeguard9 / Week11–12 | [fault_workflow.py](../tools/green_ops/fault_workflow.py) `evaluate_artifact`, `permitted_features`; [gatekeeper](../tools/green_ops/green_ops_gatekeeper.py) | [test_fault_injection.py](../tools/green_ops/tests/test_fault_injection.py), [test_gatekeeper.py](../tools/green_ops/tests/test_gatekeeper.py), [test_benchmark_evaluation.py](../tools/green_ops/tests/test_benchmark_evaluation.py) test accounting/semantics, not effective detection | Locked0/271 positive detections; validation0/281; all1920ABSTAIN;576control blocks | **Open, benchmark acceptance unmet.** Same X/model cannot observe hidden faults; blocking is not detection | Predeclare independently measured paired energy truth/effect threshold, fresh parent groups and minimum detection plus maximum false-alarm/abstention rates with supervisor before collection. Report all denominators; meeting a defined finite benchmark is not universal100% detection |
| R02 Power/energy prediction and transparent baseline; Week6–7 | [analytical_reference.py](../tools/green_ops/analytical_reference.py), [ml_pipeline.py](../tools/green_ops/ml_pipeline.py): mean/ridge, train-only scaling, stable solver | [test_analytical_reference.py](../tools/green_ops/tests/test_analytical_reference.py), [test_ml_pipeline.py](../tools/green_ops/tests/test_ml_pipeline.py), [test_ml_workflow.py](../tools/green_ops/tests/test_ml_workflow.py) | Week7 held-out RMSE6.3664mW,51.185mJ,991.183µJ/delivery, generator law only | **Analytical software**, physical generalization open; direct state formula recovery is not learned physics | On fresh physical groups compare training mean, explicit state-accounting and any learned model with predeclared units/errors and uncertainty; report residuals and instrumentation cost |
| R03 Latency/RTT ambition; schema/Windows assessment, original title not independently available | [ping.rs](../examples/src/bin/ping.rs) sends timestamp beacon, [dataset_builder.py](../tools/green_ops/dataset_builder.py) null hardware RTT, [latency.rs](../hophop/src/nrfxlib_phy/latency.rs) firmware operation latency constants | [test_week5_review.py](../tools/green_ops/tests/test_week5_review.py), analytical optional RTT tests reject unsupported hardware labels; no request/reply timing tests | No measured RTT or evaluated physical latency predictor. Assumed RTT, where enabled, is not observed | **Open + supervisor decision** on core target/QoS-only/future scope | Agree estimand/endpoints/timeout/clock and add paired request/reply workload if retained. Verify matching/timeout paths on host, then independent timestamp validation on two boards; train/evaluate latency only after genuine labels |
| R04 Delivery and energy per unique delivered logical packet; Week5 | [measurement_window.py](../tools/green_ops/measurement_window.py) delivery evidence, datasetv2 joins; telemetry `tx_successes` is API completion | [test_measurement_evidence.py](../tools/green_ops/tests/test_measurement_evidence.py), [test_dataset_v2.py](../tools/green_ops/tests/test_dataset_v2.py) test unique IDs, references, null labels | Analytical packet outcomes; synthetic sender/receiver lists only | **Software**, no physical sender/receiver application-ID collection; v1 decoded RX/operation ratio is not delivery ratio | Match session/sender/sequence logical IDs across sender offers and receiver acceptance with independent logs and aligned windows; reject duplicates/unoffered IDs; zero delivery -> null energy/delivery, not0 |
| R05 Original18-feature ambition; telemetry documentation/Windows assessment | [feature_contract.py](../tools/green_ops/feature_contract.py) version3; datasetv2 raw pre-run profile has4 inputs: payload,interval,requestedTX,window | [test_feature_contract.py](../tools/green_ops/tests/test_feature_contract.py) exhaustive roles and availability | Four-feature analytical study, no verified18-feature acquisition | **Decision/open.** Metadata, aliases, targets and schema column count are not18 measured independent features | Recover/approve exact18-field list with units, timing, availability, observability and target role; capability matrix per adapter. Explicitly agree unsupported/deferred fields; never fabricate them |
| R06 Original100ms sampling ambition; telemetry/log-parser limitations | [green_ops_telemetry.rs](../examples/src/green_ops_telemetry.rs), [log_parser.py](../tools/green_ops/log_parser.py) event-triggered cumulative logs | Eight standalone Rust bookkeeping tests; [test_log_parser.py](../tools/green_ops/tests/test_log_parser.py) parses saved logs | No periodic100ms measured stream. Ping RX awaits a fixed approx1s operation | **Open**, sampler not implemented | Agree whether100ms is snapshot cadence or observation window and tolerance; monotonic scheduled snapshots with baseline/end and explicit misses. Demonstrate jitter/drop/overhead distribution on hardware; don't delay radio operations to pretend a timer met cadence |
| R07 Bounded windows/provenance and PPK2 alignment; Week5 | [measurement_window.py](../tools/green_ops/measurement_window.py), [ppk2_summary.py](../tools/green_ops/ppk2_summary.py), [dataset_table.py](../tools/green_ops/dataset_table.py) | [test_measurement_window.py](../tools/green_ops/tests/test_measurement_window.py), [test_ppk2_summary_v2_boundaries.py](../tools/green_ops/tests/test_ppk2_summary_v2_boundaries.py), [test_dataset_table.py](../tools/green_ops/tests/test_dataset_table.py) | Synthetic alignments and deterministic table demos | **Software**, hashes validate bytes, not acquisition authenticity/clock accuracy | Archive raw current/voltage samples and markers, measured clock mapping uncertainty, coverage/gaps/clipping checks and bounded same-window totals on the identified board/rail |
| R08 Sources/assumptions; Week6 | [versioned model](../tools/green_ops/models/nrf9151-dect-reference-v1.json), [source register](green-ops-analytical-sources.md); current integration and sensitivity | [test_analytical_artifacts.py](../tools/green_ops/tests/test_analytical_artifacts.py), [test_week6_review.py](../tools/green_ops/tests/test_week6_review.py) | Deterministic sourced-current/assumed-timing reference, not device validation | **Analytical**. DECT currents limited to exact conditions; CPU/lower-TX/timing/loss assumptions unsupported physically | Verify every estimated state/current parameter on appropriate physical configuration or label/range as assumption; no LTE substitution; calibrate on development only |
| R09 Grouping, reproducibility and uncertainty; Week7–8 | [ml_dataset.py](../tools/green_ops/ml_dataset.py), [uncertainty.py](../tools/green_ops/uncertainty.py), strict JSON model/calibration artifacts | [test_ml_dataset.py](../tools/green_ops/tests/test_ml_dataset.py), [test_week8.py](../tools/green_ops/tests/test_week8.py); Week12 independent ledger/hash audit | Nominal95% family coverage28/30,28/30,26/30; shifted23/30,23/30,24/30.3844files exactly replayed | **Analytical**, coverage below target; evaluated data consumed, no hardware exchangeability | Freeze new device/session/config-parent lineage, train/development/calibration/evaluation roles before labels. Predeclare coverage estimand and insufficient-evidence policy; evaluate fresh physical groups without tuning to observed coverage |
| R10 Adapter portability; tracker architecture/upstream vision | Run metadata adapter/profile IDs, strict file/table interfaces; hophop saved-log adapter and separate analytical source | [test_run_metadata.py](../tools/green_ops/tests/test_run_metadata.py), [test_dataset_cli.py](../tools/green_ops/tests/test_dataset_cli.py) | One firmware integration plus synthetic/analytical adapters; no second physical stack | **Extension points**, not demonstrated universality | Second independent real telemetry adapter passes common semantic conformance fixtures and physical same-window checks; document unsupported capabilities instead of field-name equivalence. Supervisor decides required second platform |
| R11 Optional model comparisons; tracker Phase2 / Week7 scope | Stdlib training-mean and ridge only; no installed/implemented optional sklearn ensemble adapter | [test_ml_pipeline.py](../tools/green_ops/tests/test_ml_pipeline.py), grouped CV/model-selection tests | Mean-vs-ridge reports available; no tree/ensemble performance evidence | **Optional/deferred per available plans**, original mandatory status unresolved | If required, isolate optional dependency/version lock and compare on development folds only, freeze before fresh evaluation; no score improvement guarantee, no consumed-test tuning |
| R12 Explainability and per-change diagnosis; Week8–10 | [explainability.py](../tools/green_ops/explainability.py), [green_ops_report.py](../tools/green_ops/green_ops_report.py) contributions/permutation/top3 | [test_week8.py](../tools/green_ops/tests/test_week8.py), [test_report.py](../tools/green_ops/tests/test_report.py) | Analytical signed influence/ablation results; duration-fixed permutation blind spot documented | **Model sensitivity**, no physical causal diagnosis or hidden-code-change observability; SHAP not delivered | Verify contribution sums/reference and stability, label correlation/scope. Demonstrate change attribution only when permitted observations change; physical root cause needs independently confirmed mechanism |
| R13 Gate/battery policy; Week9 | Strict [policy](../tools/green_ops/policies/green_ops_budget.json), [battery_projection.py](../tools/green_ops/battery_projection.py) and gate0/1/2/3 | [test_gatekeeper.py](../tools/green_ops/tests/test_gatekeeper.py) includes battery, bounds, status and provenance | Research demos of4statuses; default benchmark abstains | **Research software**, no actual energy approval or endurance assurance | Validated applicability/coverage and measured workload required for scoped approval; otherwise ABSTAIN. Capacity/rail/efficiency/duty loss terms explicit, aging omitted; five years engineering target, not universal EU mandate |
| R14 CI and reports; Week10 | [.github/workflows/green-ops-ci.yml](../.github/workflows/green-ops-ci.yml), [ci_rust_checks.sh](../tools/green_ops/ci_rust_checks.sh), Markdown wrapper; existing [buildtest.yml](../.github/workflows/buildtest.yml) remains separate | Local317 at Week10; final353 at2f3559c; wrapper exit/report tests; historical host/ARM builds | Exactff801898 fork push run44080696563 passed Rust host/standalone ARM and317Python+expected-ABSTAIN smoke | **Historical remote only.** No Week11/12/new-branch hosted run, fork-PR run, legacy workflow/full-board matrix verification; standalone ARM module is not full firmware link | With new authorization, test exact new SHA for push and fork-PR, inspect legacy build matrix/dependency setup and all job outcomes. Actual approval step must propagate FAIL/ABSTAIN/ERROR; smoke success is not approval |
| R15 Physical validation; acquisition protocol / roadmap lab track | [measurement-readiness protocol](green-ops-measurement-readiness.md), firmware feature toggle/build conventions | Host/no_std contracts, summary validation; no acquisition test substitutes for device data | **None performed** for synchronized physical power, RTT, fault/delivery regression detection or overhead | **Open, essential evidence gap** | Identified boards/rail/PPK2/firmware, safe setup, randomized on/off overhead pilot, synchronized paired physical captures, reproducible raw archives and predeclared quality/rejection/evaluation criteria |
| R16 Final academic delivery and effort; owner-reported15ECTS/450h | Plans, technical results and negative benchmark reports; secondary external interim technical report | Documentation/reproduction checks, no academic assessment | No final dissertation submission/demo acceptance, systematic source review sign-off, supervisor rubric reconciliation or actual effort log available | **Open + decision**. Agent runtime/package count ≠450student hours or degree acceptance | Supervisor-approved research question/scope, source review, defensible methods/negative findings, limitations, reproducibility appendix, final write-up/demo and actual dated student effort log; verify institutional requirements from originals |

## Why Week12 is negative: actual interface chain

`feature_contract.PRE_RUN_FEATURES` at contract3 has exactly
`payload_size_bytes, interval_ms, tx_power_dbm, window_duration_ms`.
`fault_workflow.permitted_features(intent)` reads only that intended dictionary.
`resolved_evidence` calls the same frozen `predict_matrix` with that X for baseline
and injected behavior. The fault engine changes the execution ledger before
energy integration; it never changes intended X. TX lock can change actual power
while keeping the requested14dBm unchanged. No model sees CPU/retry/fragment/
wakeup activity. Equal inputs to the same deterministic model give equal outputs;
new commit identifiers do not change this.

The adapter explicitly returns no interval and reason
`new_fault_engine_scope_without_calibration`; existing calibration is not copied
into the new scope. Default policy restrictions and failed historical family
coverage cannot justify a pass. `gate_exit` preserves ABSTAIN3/block. Positive
detection requires the existing conjunction FAIL + oracle violation + observability;
it is false for every case. Offline oracle truth is independent diagnostic
accounting, not available execution telemetry or a policy override.

The [committed case records](results/week12/cases.jsonl) and aggregate show0input
changes,0prediction changes,0positive detections; all1920ABSTAIN including576
compliant controls. There are552known >5% violations,271locked/281validation,
all without positive detection.21infeasible cases retain null labels; their
blocking is not detection either. Only8locked parent groups exist. None of these
records, hashes, frozen models/calibration/policies or consumed-data identities
is modified by this audit. Design does not relabel consumed groups as fresh.

## Decisions to carry to supervisor

1. Confirm energy detection estimand (pre-run configuration estimate versus
post-run execution diagnosis) and acceptable missed-fault/false-alarm/abstention
trade-off. Current pre-run claim must remain narrower than hidden-code detection.
2. Resolve latency: core measured/predicted target, measured QoS gate only, or
explicitly scoped extension. Record signed scope decision; do not silently remove
latency from title/objectives. Any retained RTT requires a new request/reply workload.
3. Recover original18features/100ms definition and decide second-platform/ensemble
obligations and academic deliverables. No substitute list asserted here.
4. Agree a feasible physical study and actual effort/lab budget before accepting
any academic completeness claim. These decisions need not block this audit/design;
they gate the affected implementation/experiment acceptance.

Next design: [post-run observations](green-ops-observability-design.md) and
[prioritized sprint](plans/green-ops-observability-sprint.md).
