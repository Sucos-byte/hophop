# Requirements/evidence audit and observability handoff

Complete audit/design only on green-ops/observability-design from verified clean
b48c91d7cc08f21f0bee7f44074f224c3fa2b3f9. No applicable AGENTS.md found.
No source/model/policy/benchmark changes, new scoring, hardware execution, push,
publication, merge or deployment. Frozen studies and consumed records preserved.

Delivered:
- docs/green-ops-requirements-evidence-audit.md:16-row traceability matrix,
  available/original-missing authority inventory, source-based Week12 explanation,
  proposed acceptance criteria and supervisor decisions.
- docs/green-ops-observability-design.md: feasible/unsupported firmware observations,
  separate proposed execution_observation_version1/post_run_diagnostic_v1,
  clocks/missingness/overhead/provenance/leakage, RTT acquisition and explicit
  accounting baseline with overlap/double-counting guards.
- docs/plans/green-ops-observability-sprint.md: proposed small implementation order,
  files/interfaces/tests, laptop versus hardware evidence gates. Design, not built.
- docs/results/observability-design/source-audit.json:34inspected-source SHA-256
  snapshots (repository sources pinned to baseline; external files fingerprinted).
  verification.json records documentation/frozen-preservation checks.

Findings: unchanged intendedX=>unchanged frozen predictions; all1920ABSTAIN and
0positiveFAIL across552oracle violations.576control blocks do not prove selectivity.
Current telemetry observes RX calls/decoded packets/matching beacons/TX completion,
not actual CPU-active time, local RF power, modem retries, wake residency or unique
peer delivery. Async duration and scheduledTX timestamp cannot stand in for these.
Ping lacks a matched reply; latency.rs verifies firmware transition constants,
not RTT. Existing hardware RTT remains null. Original exact18-feature/100ms
specification, signed brief/rubric and actual effort log unavailable in searched
sources. No invented replacement requirements or academic completion assertion.

Verification: local document links/source snapshots and frozen dependency preflight
checked, no scoring. Latest software suite remains353passing/114.947s at source
2f3559c (Week12); unchanged code means no redundant full-suite rerun this task.
Historical hostedff801898 run is not remote verification of this branch.

Next proposed task: implement strict observations/capability validation and pure
Rust operation/logical-ID bookkeeping, then opt-in workload/importer. Do not begin
new training or reuse consumed evaluation outcomes for tuning. Actual CPU/radio
backends require source/API evidence and physical validation first.

Carry to supervisor before affected acceptance: latency(Acore predictor/BQoS-only/
Cexplicit deferment), exact18features/100ms semantics, second-adapter/optional-model
obligations, physical tolerances/study budget and academic rubric/effort record.
No immediate user decision/hardware action required for this completed design.
Repository tracker remains authoritative; Windows file is one-way snapshot.
