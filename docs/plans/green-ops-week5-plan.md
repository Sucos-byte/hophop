# Week 5 — Measurement, feature and multi-run dataset contracts

Status: implementation plan prepared 17 November 2026. Target branch: `green-ops/week5-measurement-contract`. This plan implements Phase 1 closure and brings the multi-row table component forward from Phase 2. Standard library only this week; optional ML dependencies remain isolated for later weeks.

## Evidence and execution boundary

Confirmed baseline: 35ce7f3 on green-ops/week4-dataset-builder, clean working tree reported by the user. Week 4 CLI commit 16f42b5; completed documentation f331e11. Latest reported suite: 106 passing tests. Synthetic saved-log-to-row demonstration passed. The WSL repository could not be read from the assistant session, so signatures below are proposed NEW interfaces, and integration points must be checked against the current checkout before editing. Do not replace or remove user changes.

Week 4 is complete for its original software scope. Its existing decoded-packet fields and max-per-segment aggregation remain a legacy v1 contract, not evidence that measured runs are ready for training.

## Outcomes and task budget

| Task | Hours | Result |
|---|---:|---|
| 0 | 2 | Baseline, API inventory and version decision recorded |
| 1 | 7 | Exhaustive feature registry and prediction-context selection |
| 2 | 9 | Validated bounded window, counters and delivery evidence |
| 3 | 7 | PPK2 v2 alignment and dataset v2 builder integration |
| 4 | 9 | Homogeneous multi-run matrix and provenance filtering |
| 5 | 4 | Table CLI, reservation and manifest |
| 6 | 5 | Acquisition protocol, migration guide and demonstration |
| 7 | 2 | Full verification, review and progress checkpoint |
| Total | 45 | Planning estimate; log actual effort and adjust |

## Shared decisions before implementation

### Prediction contract

Two modes: `pre_run` and `post_run`. The first uses configuration and workload known before execution. The second may additionally use diagnostics captured during a specified headless run. CI must actually produce those diagnostics; absence is an error for a requested feature, not an invitation to fill zero. A simulation of a candidate is not equivalent to executing its firmware.

Requested configuration and observed hardware configuration are distinct. Firmware revision, run identity, seeds, repetitions and provenance are grouping/audit fields, not predictive features by default. Timestamp identifiers and future outcomes are excluded. Mean power multiplied by duration derives energy; neither energy nor any energy-derived value enters X. Post-run delivered counts influence an energy-per-delivery target denominator; treat this as a declared diagnostic model and ablate the count, not a prospective prediction claim.

### Versioning and compatibility

- Freeze existing `DATASET_FIELDS` and v1 behavior for current callers. Add `DATASET_FIELDS_V2` and explicit v2 APIs; no implicit promotion of v1 rows to trustworthy measurements.
- Keep current CLI v1 behavior unless `--dataset-version 2` is requested. Require `--measurement-window` for v2. Optional `--delivery-summary` supplies delivery evidence.
- PPK2 summary v1 continues to validate under its existing API. New bounded measured datasets require summary v2; reject v1 there with an actionable migration message.
- The new table builder requires a single selected dataset version. Week 5 implements v2 tables; v1 input is rejected with guidance to regenerate from source artifacts. Never coerce blanks to zero or concatenate different column meanings.
- New contracts return normalized copies, not mutated inputs. JSON loaders reject duplicate keys, NaN/Infinity, unknown keys, invalid UTF-8 and wrong scalar types. Boolean values are not numbers. Validate derived values for overflow/nonfiniteness too.

### Proposed dataset v2 fields

Retain all v1 fields except rename `rx_attempts` to `rx_operations`, `delivered_packets` to `rx_decoded_packets`, and the old `packet_delivery_ratio` to `rx_decode_per_operation_ratio`. This records the historical meanings explicitly. V2 adds a NEW `delivered_packets` for unique receiver delivery evidence and a NEW `packet_delivery_ratio` for unique deliveries divided by unique offered packets.

Add `window_duration_ms`, `offered_packets`, `delivery_status`, `evaluation_group_id`, and `analytical_model_id`. `window_duration_ms` is the declared aligned observation duration (not inferred from sparse event timestamps). All fields, their ordering and exact types must be frozen in docs and tests before integration. V2 field order is v1 order with the three legacy replacements, followed by these additions and the new delivered_packets/packet_delivery_ratio. No duplicate field names.

`delivery_status`: `unavailable` or `validated`. Unavailable => offered_packets, delivered_packets and packet_delivery_ratio all null. Validated => nonnegative exact integers, delivered <= offered; ratio null for offered=0, otherwise delivered/offered. Energy per delivery is null without validated positive deliveries. RTT is null without correlated ping/reply evidence from a common clock; this week does not synthesize RTT from RX/TX timestamps.

Provenance combinations accepted for v2:

| source_kind | execution_kind | measurement_status | Target behavior |
|---|---|---|---|
| synthetic | synthetic | unmeasured | All targets null |
| synthetic | simulation | unmeasured | All targets null |
| hardware | hardware | unmeasured | Energy targets null; RTT only with validated evidence |
| synthetic | simulation | analytical_simulation | Finite model-generated targets; analytical model reference required |
| hardware | hardware | measured | Bounded aligned PPK2 v2 required for energy targets |

Analytical references contain model ID, version, configuration SHA-256 and assumptions-document SHA-256. The table verifies those values against the source manifest. Week 5 fixtures exercise the schema but are explicitly test data; the generator and technical source audit arrive Week 6. Do not accept a status string alone as evidence of analytical provenance.

## Task 0 — Baseline and branch

Read repository AGENTS.md and applicable instructions. Inspect current dataset builder, metadata, PPK2 summary, CLI, atomic publisher and tests. Confirm no incompatible new work has appeared. Record current full SHA and last suite result in the plan migration notes.

```bash
cd ~/projects/green-ops/hophop
git status --short --branch
git log -5 --oneline
git switch -c green-ops/week5-measurement-contract
python3 -W error::ResourceWarning -m unittest discover -s tools/green_ops/tests -v
```

If the branch already exists, inspect it and switch to it without recreating or resetting it. On Windows, launch Ubuntu explicitly using `wsl -d Ubuntu` before running these shell commands. Python-only Week 5 tasks do not need sourcing Cargo's environment.

## Task 1 — Feature registry

New files: `tools/green_ops/feature_contract.py`, `tools/green_ops/tests/test_feature_contract.py`, `docs/green-ops-feature-contract.md`.

Public constants and exact proposed signatures:

```python
METADATA_IDENTIFIERS: frozenset[str]
PREDICTION_TIME_FEATURES: frozenset[str]
TARGET_COLUMNS: frozenset[str]
PRE_RUN_FEATURES: tuple[str, ...]
POST_RUN_FEATURES: tuple[str, ...]

def validate_feature_partition(fields: tuple[str, ...], *, schema_version: int) -> None: ...
def select_feature_names(*, schema_version: int, prediction_mode: str,
                         available_fields: frozenset[str]) -> tuple[str, ...]: ...
def extract_features(row: dict, *, prediction_mode: str,
                     available_fields: frozenset[str]) -> dict: ...
```

The three sets form an exhaustive pairwise-disjoint partition of the chosen schema. TARGET_COLUMNS contains exactly mean power, total energy, energy per delivered packet, and ping_rtt_latency_ms. Partition tests cover legacy DATASET_FIELDS as well as v2 via a versioned registry; constants describe v2. Metadata includes identity/provenance, group/seed/repetition, delivery status, segment count and analytical model ID. Numeric diagnostic counters and ratios are post-run candidates, not pre-run features.

Pre-run defaults: payload_size_bytes, interval_ms, tx_power_dbm, window_duration_ms. Simulation loss parameters are allowed only in an explicitly declared simulation capability profile; absence of known hardware channel parameters cannot be imputed from the requested loss preset. Duration means a planned fixed-duration workload for pre-run predictions. Reject early-terminated measured runs from that profile; use a separate post-run context for their actual duration.

Post-run extends pre-run with explicitly available numeric diagnostics. `available_fields` is a capability declaration, not just the CSV header. A selected missing/null field raises ValueError with its name. Categorical identifiers remain metadata initially; loss probabilities are numeric context when supported. The manifest's old feature_columns listing is replaced in v2 with registry-derived roles and prediction-mode-specific selected features.

RED cases: overlap; unclassified new field; extra unknown field; duplicate schema field; target request; unsupported mode; missing/null capability; no target or ID in extracted X; stable column ordering; bool numeric rejection; pre-run rejects outcome features; seed/group never enters X. GREEN: minimal registry and selectors. Commit: `Add versioned prediction feature contract`.

## Task 2 — Window and counter contract

New files: `tools/green_ops/measurement_window.py`, `tools/green_ops/tests/test_measurement_window.py`, `tools/green_ops/fixtures/measurement-window-synthetic.json`.

```python
def validate_measurement_window(data: dict, *, expected_run_id: str,
                                max_window_duration_ms: float = 3600000.0) -> dict: ...
def load_measurement_window(path: str | Path, *, expected_run_id: str,
                            max_window_duration_ms: float = 3600000.0) -> dict: ...
def compute_counter_deltas(window: dict) -> dict[str, int]: ...
def validate_delivery_summary(data: dict, *, expected_run_id: str,
                              expected_window_id: str) -> dict: ...
```

Window v1 exact keys: window_version=1, run_id, window_id (safe IDs), clock_id (nonempty ID), start_us/end_us (nonnegative integers, end>start), window_duration_ms (finite positive), segment_id (nonnegative integer), start_counters/end_counters (same four counter names as current telemetry), observed_segment_ids (nonempty integer list), alignment (object), evaluation_group_id (safe ID).

Duration must equal (end_us-start_us)/1000 to within 0.001 ms absolute rounding tolerance. Maximum duration must itself be finite positive; default one hour is a configurable software bound, not a radio specification. Counters must be exact integers in [0, 2**32-1]. Every delta must be nonnegative. Reject saturation at either endpoint because the increment count becomes ambiguous. Reject wrap/reset and multiple observed segments; do not salvage them with max/sum. Raw evidence must establish endpoint snapshots and continuity; a hand-authored summary cannot prove it.

Alignment keys: method (`synthetic_fixture`, `gpio`, `serial`), reference_artifact_sha256 (64 lowercase hex), start_marker_id/end_marker_id (nonempty distinct strings), uncertainty_ms (finite nonnegative). All use one defined clock domain or an explicitly documented mapping. For measured readiness, uncertainty must meet a separately configured maximum; the value is logged, not assumed zero.

Delivery summary v1 exact keys: summary_version=1, run_id, window_id, sender_id, receiver_id, offered_packet_ids, delivered_packet_ids, evidence_sha256. IDs are nonempty safe strings unique within their lists; delivered must be a subset of offered. Retransmissions preserve logical IDs; duplicates are deduplicated by the adapter before summary construction. IDs include session identity so resets cannot collide. Do not derive offered count from receive attempts. This summary is provisional application-delivery evidence; packet capture construction belongs to the adapter.

RED cases: exact duration; fractional-ms window; bounds; bool/NaN/inf; reversed endpoints; duration mismatch; reset; saturation; multiple segments; nonzero baseline subtraction; duplicate packet IDs; delivered not offered; wrong run/window; malformed hashes; no mutation. Fixture has synthetic alignment and is rejected as measured evidence later. Commit: `Add bounded measurement windows and delivery evidence`.

## Task 3 — Measured summary and dataset v2 integration

Modify: `ppk2_summary.py`, `dataset_builder.py`, `green_ops_build_dataset.py`, their three test modules. Add `tests/test_dataset_v2.py` and synthetic v2 fixtures. Share strict loaders where suitable; preserve existing imports.

```python
def validate_ppk2_summary_v2(data: dict, *, expected_run_id: str,
                            window: dict, duration_tolerance_ms: float = 1.0,
                            duration_tolerance_fraction: float = 0.001,
                            max_alignment_uncertainty_ms: float = 1.0) -> dict: ...
def build_dataset_row_v2(run_metadata: dict, telemetry_rows: list[dict], *,
                         measurement_window: dict, experiment: dict | None = None,
                         ppk2_summary: dict | None = None,
                         delivery_summary: dict | None = None) -> dict: ...
def build_dataset_row_v2_from_files(telemetry_csv: str | Path,
                                    run_metadata: str | Path, *,
                                    measurement_window: str | Path,
                                    experiment_plan: str | Path | None = None,
                                    ppk2_summary: str | Path | None = None,
                                    delivery_summary: str | Path | None = None) -> dict: ...
```

PPK2 v2 retains existing fields with summary_version=2 and adds window_id, window_duration_ms, voltage_v, raw_capture_sha256, alignment_reference_sha256. Match window/run IDs and alignment reference. Duration difference must be <= max(abs tolerance, fraction * window duration). Tolerances finite/nonnegative; fractions <=1. Require positive finite power/energy/voltage/duration. Check energy_mj = mean_power_mw * duration_ms / 1000 within documented integration/rounding tolerance (default relative 0.001, absolute 0.001 mJ; introduce explicit keyword parameters for both). This consistency rule requires both statistics to describe the same integrated window. Serial alignment may be accepted only with quantified uncertainty within policy; synthetic alignment is never measured evidence.

V2 uses endpoint deltas for diagnostics. Require telemetry rows to match run/source/segment, all observed counters between baseline and end snapshots, and nondecreasing observed values in source order. Endpoints and raw capture hashes provide the bounded interval; sparse events alone cannot establish it. Retain missing RTT; do not silently use asserted metadata RTT without evidence.

With no delivery summary, energy per delivered packet remains null even when energy is measured. With valid delivery evidence and positive deliveries, compute deterministic energy_mj*1000/delivered. Check overflow. Unknown plan settings remain null. V2 requires evaluation_group_id but does not infer scientifically independent groups merely from unique strings.

Add CLI flags: --dataset-version {1,2} (default 1), --measurement-window, --delivery-summary, --duration-tolerance-ms, --duration-tolerance-fraction, --max-alignment-uncertainty-ms. Reject v2-only flags with v1. Include all input hashes, contract versions, policy tolerances, role registry version and output hash in the v2 manifest. Reserve outputs and clean up on errors using existing publisher. Do not claim multi-file crash atomicity.

RED cases: v1 regression suite unchanged; correct measured v2; measured v1 summary rejected; duration boundary just inside/outside tolerance; mismatched IDs/alignment hashes; invalid tolerance; energy/power inconsistency; no delivery denominator => null; zero delivery => null; unique delivery denominator; invalid segment; unmeasured synthetic targets null; overflow; CLI errors produce no final artifacts. Commit: `Add aligned measurement dataset v2`.

## Task 4 — Multi-run table builder

New files: `tools/green_ops/dataset_table.py`, `tools/green_ops/tests/test_dataset_table.py`. Matrix stores complete v2 rows; model-specific X/y extraction is a later stage using the registry.

```python
def load_dataset_artifact(csv_path: str | Path, manifest_path: str | Path) -> dict: ...
def validate_dataset_row(row: dict, *, schema_version: int) -> dict: ...
def build_dataset_table(artifacts: list[dict], *, schema_version: int,
                        measurement_status: str,
                        required_targets: tuple[str, ...] = (),
                        missing_target_policy: str = "error") -> tuple[list[dict], dict]: ...
```

Artifact return keys: row, manifest, csv_sha256, manifest_sha256. Require one row per source CSV, exact v2 header and types; parse empty cells as None only where allowed. Verify CSV hash against manifest and cross-check row run/provenance/version with manifest. Never evaluate text or load pickled artifacts. A digest establishes byte identity, not trusted authorship or truthful measurements.

Require one measurement_status selection per table: unmeasured, analytical_simulation or measured. Validate every source before filtering; invalid excluded sources still fail. Reject duplicate run IDs across inputs even if bytes match, conflicting provenance, mixed schema versions and empty selections. Record excluded IDs/counts/reasons. Deterministically sort accepted rows by run_id; reject duplicate artifact references. Preserve evaluation_group_id, adapter/profile IDs and analytical model ID for grouping. Mixed adapters are permitted only when schema and feature meanings agree; no automatic claim of cross-platform transfer.

Required targets must come from TARGET_COLUMNS. By default missing required targets fail; explicit `exclude` policy records each exclusion. Unmeasured audit tables use no required targets and retain null labels. Never include an unmeasured row in an energy-training selection. Analytical rows require validated manifest reference/model identity; do not fabricate hardware summaries to obtain energy values.

Manifest result keys: table_version=1, dataset_version=2, selection policy, row_count, sorted run_ids, sorted group_ids, source artifact hashes, included/excluded counts and reasons, feature_contract_version, target missing counts. CLI adds output CSV digest. No volatile timestamps in deterministic output.

RED cases: two valid rows; reverse input order identical result; version/header mismatch; duplicate run/conflicting row; hash tampering; inconsistent manifest; invalid numeric strings; blank target remains null; each provenance selection; analytical reference missing; zero rows; missing target error/exclude; no cross-provenance pooling; group IDs preserved; unsupported targets rejected. Commit: `Add provenance-filtered multi-run dataset tables`.

## Task 5 — Table CLI and output lifecycle

New files: `tools/green_ops/green_ops_build_table.py`, `tools/green_ops/tests/test_dataset_table_cli.py`.

```python
def main(argv: list[str] | None = None) -> int: ...
```

CLI: repeatable `--artifact DATASET_CSV MANIFEST_JSON`; required `--measurement-status`, `--table-output`, `--manifest-output`; `--dataset-version 2`; repeatable `--require-target`; `--missing-target-policy {error,exclude}` default error. Invalid arguments/files/contracts return 1; successful nonempty output returns 0 and prints accepted/excluded counts. Filtering is intentional and recorded, not hidden in exit status. Reserve two destinations with the existing publisher. Reject source/output aliasing, existing files, and colliding output paths before writing. Preserve source contents on all failures.

RED: subprocess success; null round-trip; invalid UTF-8; exact output hashes; existing destination; aliases; second-publication failure rollback; argument exit 1; deterministic output at distinct destinations. Keep focused tests meaningful; reuse existing atomic tests rather than duplicating every implementation branch. Commit: `Add dataset table command-line workflow`.

## Task 6 — Acquisition protocol and reproducible examples

New docs: `docs/green-ops-measurement-readiness.md`, `docs/green-ops-dataset-table.md`. Update `docs/green-ops-dataset-builder.md`. Add a standard-library demonstration runner or documented commands using a fresh output directory, with two distinct runs and explicit group IDs. Store synthetic source fixtures, not temporary generated artifacts.

Protocol must specify: exact board revision/firmware/modem version; supply voltage; PPK2 mode and measurement range; debug/USB/LED power contributions; whether board or SoC energy is measured; common ground and avoidance of multiple supplies. Exact connections and limits must be checked against current official Nordic DK and PPK2 documentation before prescribing wiring. Do not guess pin numbers or DECT-state currents.

Acquisition sequence: warm up and settle; capture counter baseline; emit start marker; run fixed workload; emit end marker and capture counters; archive raw traces, telemetry and checksums; record actual duration and marker uncertainty; validate continuity and summary integration. Define endpoint inclusion (half-open [start,end)) consistently across packets and energy. Measure GPIO marker overhead and logging effects; record whether results include them. Serial host arrival time is insufficient for exact device-window alignment without a quantified mapping.

Delivery uses sender-offered logical packet IDs and unique receiver acceptance for the same window/session; document late arrivals and exclude or separately report them. RTT requires correlated ping/reply IDs and one clock or a calibrated mapping. Baseline subtraction applies to cumulative counters; any idle-energy subtraction must be reported separately from total measured energy.

Repeatability: predeclare repetitions (initial pilot proposal: at least five per configuration), randomize configuration order with logged seed, record environmental/network conditions, keep raw results and failed runs with reasons, and estimate variability before deciding final sample size. Group session/device/repetition families appropriately in later model evaluation.

Acceptance demo: two synthetic v2 runs -> two table rows with null energy; separate labeled analytical contract fixtures -> analytical-only table; simulated measured-contract tests -> test evidence only, never a claimed hardware capture. Document that lab execution is still pending. Commit: `Document measurement protocol and dataset table workflow`.

## Task 7 — Verification and handoff

Use red/green tests task by task, then one final full suite. A test import error is an initial scaffold failure; before declaring a behavior implemented, ensure assertions actually execute. No repeated full-suite runs for unchanged documentation.

```bash
python3 -m unittest discover -s tools/green_ops/tests -p 'test_feature_contract.py' -v
python3 -m unittest discover -s tools/green_ops/tests -p 'test_measurement_window.py' -v
python3 -m unittest discover -s tools/green_ops/tests -p 'test_dataset_v2.py' -v
python3 -m unittest discover -s tools/green_ops/tests -p 'test_dataset_table*.py' -v
python3 -W error::ResourceWarning -m unittest discover -s tools/green_ops/tests -v
git diff --check
git status --short --branch
```

Stage explicit task paths only. Before each commit: `chmod 644` on new Python/JSON/Markdown files, `git diff --cached --check`, `git diff --cached --stat`, and `git diff --cached --summary`. Confirm new index modes with `git ls-files -s` for those paths. Do not commit caches or build artifacts. Do not amend historical commits solely to hide migration history.

Final checklist: current baseline preserved; registry exhaustive/disjoint; availability/leakage rules enforced; bounded measured windows and alignment validated; delivery denominator evidence enforced; legacy migration documented; multi-row table strict and deterministic; provenance filters explicit; rollback covered; reproducible examples; all applicable checks pass; changes committed locally; tracker records actual hashes/test results and hours. Hardware completion remains a separate evidence milestone.

## Phase 2 handoff

Week 6 analytical_reference.py will produce v2 analytical artifacts through an explicit new API, not by passing invented PPK2 summaries into measured APIs. Model manifests record sources, assumptions, ranges, parameter version, seed and state-time integration. Keep independent generator/held-out scenarios to avoid demonstrating only recovery of a trivial training formula. Use analytic energy checks as oracles; RTT/retry assumptions remain declared until validated.

Week 7 starts with stdlib constant/linear baselines; add an optional sklearn tree ensemble adapter after stable interfaces. Fit imputation/scaling on train folds only. Evaluate per target with explicit missing-label filters, group-level splits and MAE/RMSE/R²; report undefined R² for constant truth. Week 8 adds calibrated prediction intervals, group-bootstrap metric intervals, ablations and attribution. Later gatekeeper decisions include model/contract/provenance compatibility and uncertainty policy.

Five years is a configurable battery-design policy, not a verified universal EU autonomy mandate. See official references in green-ops-progress.md. Benchmark detection targets apply to specified injected cases and thresholds; also report false positives and inconclusive predictions.
