# Green-Ops native execution handoff

User authorizes direct implementation, debugging, appropriate tests, documentation, progress updates and local commits for the approved Week 5 plan. Work task by task autonomously; ask only for required missing information or permissions. Do not push or publish without authorization. Read repository instructions first. The user wants to focus on physical lab tasks and decisions instead of copying implementation blocks.

## Confirmed baseline

- Repo: /home/thite/projects/green-ops/hophop
- Branch: green-ops/week5-measurement-contract
- Latest commit: 25b1aaa Add bounded PPK2 summary v2 validation
- Working tree reported clean by user.
- Latest full suite: 153 tests passed with ResourceWarning treated as errors.
- Prior Week 5 commits: ef0470f v1 prediction feature contract; c97ec4e bounded measurement windows and delivery evidence.
- Week 4 baseline: 35ce7f3, following f331e11 documentation and 16f42b5 dataset CLI.

## First actions

Verify actual HEAD/status and applicable AGENTS.md instructions. Inspect existing code and tests; do not rely on this handoff over actual source. Read green-ops-week5-plan.md and green-ops-progress.md copied alongside this file. Update tracker with 25b1aaa and 153 tests if necessary. Do not rerun a full unchanged suite merely to rediscover already confirmed results unless environment differences warrant it.

Continue Week 5 Task 3: versioned dataset v2 schema, feature registry v2, aligned measurement integration, strict v2 artifact file loading and CLI integration. Tasks 1 and 2 have partial/foundational completion; v2 registry coverage is still required. Then implement multi-run table and CLI, acquisition protocol and demos per the plan. Keep v1 APIs and CLI behavior compatible. Use meaningful TDD cases and focused checks, then a final full suite for changed integration. Set normal Python/JSON/Markdown modes 100644 and commit explicit paths locally.

## Key scientific contracts

V1 delivered_packets counts decoded receptions; its packet_delivery_ratio divides decoded receptions by receive attempts. These are not end-to-end delivery evidence. V2 must distinguish these legacy meanings from unique sender-offered/receiver-delivered packet IDs.

Window deltas subtract nonzero endpoint baselines. Reject reset, saturation and multiple segments. PPK2 v2 revalidates windows and matches run/window/alignment hashes, duration and declared uncertainty; checks energy_mj = mean_power_mw * duration_ms / 1000. Tolerances are policy settings. Raw evidence authenticity and clock alignment require separate verification. Existing compute_counter_deltas and PPK2 v2 currently use default one-hour window limit; reconcile configurable policy across callers before claiming arbitrary-duration support.

Synthetic fixtures and manually constructed GPIO/PPK2 summaries are test data. They are not physical measurements. Unmeasured targets remain null. Later analytical rows use synthetic/simulation/analytical_simulation with explicit model references. No invented PPK2 summaries to label analytical data as measured.

Keep prediction inputs and targets disjoint, distinguish pre-run configuration from post-run telemetry, and control group leakage in later training. Energy-derived labels must never enter X. No universal five-year EU battery autonomy mandate has been established; five years is an engineering policy target. Software ML/CI/fault benchmarks can proceed before lab calibration. Accuracy against an analytical model does not establish hardware accuracy.

## Communication

Explain changes and impact plainly; announce confirmed milestones, update the progress tracker with actual hashes/test counts, and distinguish software progress from physical evidence. User prefers GPT-6.1 Sol Medium for routine implementation, High for validation/schema/design work when available. Do not ask the user to paste routine coding commands when native execution works. Ask for help only when required. Avoid claiming measured hours, overall completion percentages or hardware results without evidence.


## Native continuation completed — 17 November 2026

The original baseline/next-action sections above are historical. Week 5 software
Tasks 0–7 are now implemented and locally committed:

- `822679f`: aligned dataset v2, strict file API/CLI, feature registry v2.
- `c037dd8`: strict artifacts and provenance-filtered deterministic tables.
- `f119f2d`: table CLI and reserved output lifecycle.
- `637afb0`: official-source acquisition protocol, migration guide and demo.
- `e064cfa`: final contract hardening; 182 tests pass with ResourceWarning errors.

The acceptance demo at `/tmp/green-ops-week5-demo` produced two synthetic
unmeasured rows with null labels and a separate two-row analytical contract-test
table. No physical capture or calibrated model exists from this execution.
Reproduce using `python3 tools/green_ops/demo_dataset_v2.py NEW_DIRECTORY`.
Next planned software is Week 6's explicitly sourced analytical generator;
do not mistake the fixed Week 5 contract fixtures for that generator. Lab
acquisition and actual effort logging remain pending. No push or publish was
performed. Verify actual Git status before any later continuation.
