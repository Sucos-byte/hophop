# Week10 — deterministic local Markdown reporting and CI software verification

Verified cleanb2b6c086305049272642e5ca6c372e3fb5b43f2a; branch
green-ops/week10-ci-reporting. Read tracker, Week9 handoff/results, strict gate,
budget/battery/evidence/output APIs, existing buildtest workflow, test/03,05,07
scripts, Cargo manifests/lock, telemetry and firmware setup docs. No applicable
AGENTS.md found. Incoming305 Python tests; no unchanged baseline rerun. No push,
remote publication/comments/uploads, deployment or branch-protection changes.
Standing Windows local snapshot updates remain separately authorized.

## Predeclared report validation and trust boundary

Implement standard-library green_ops_report.py: validated Week9 version1 decision
JSON + exact expected SHA256 + corresponding policy bytes. Validate strict JSON,
status/exit/blocks consistency, research/no-assurance flags, criterion status
aggregation, units/ranges/numbers, policy hash/threshold/model bindings, required
context and digest syntax. ERROR form has its own strict schema and unestablished
provenance. Hash integrity is not signature/authentication: supplied expected
hash must come from a trusted decision producer/inventory. Fresh gate/report
wrapper recomputes authoritative decisions instead of accepting edited results.

Render deterministic local Markdown: all statuses/reasons, candidate/baseline
revision labels, model hashes, comparable workload/windows/context/domain,
values/intervals/thresholds/units/regression diagnostics, battery assumptions/
projection/omissions, compatible top3 signed model contributions, provenance,
observed coverage failures and artifact hashes/references. Missing attributions
explicit; no invented explanation. Escape every untrusted string/key as table
text (HTML/Markdown delimiters, links, newlines, controls/bidi); never construct
an untrusted URL or raw HTML/fence. Engineering-policy language, research-only
and unvalidated overrides prominent, never legal/compliance assurance.

Output reserve/new destinations only, alias/collision rejection, rollback on
processing/publication failures. A renderer's0 means software rendering success,
not energy approval. A separate gate/report wrapper preserves0/1/2/3; rendering
failure returns1 and blocks regardless of gate outcome. Publish JSON/Markdown
as a reserved rollback group. Expected-ABSTAIN smoke verifies exact3/no override,
reason, JSON and deterministic Markdown; returns0 only as SOFTWARE VERIFICATION.
No research override in CI default smoke and no candidate approval implied.

## CI scope and reproducibility

New .github/workflows/green-ops-ci.yml on push/pull_request, ubuntu-24.04,
contents:read only, checkout persist-credentials:false, timeouts, no secrets,
no pull_request_target/untrusted event text in shell, no artifact upload/comment,
no continue-on-error or unconditional success. Existing workflow unchanged.
Two jobs: Rust host/standalone ARM telemetry checks and full Python/smoke.

Reuse test/05 host workspace exclusions (hophop/nrfxlib-sys-pretty cannot host-test)
with --locked default and all-features; include standalone rustc telemetry tests
and thumbv8m.main-none-eabihf no_std wrapper compilation. Pin Rust1.99.1 as actual
installed/existing workflow version and Python3.14.4 as study/runtime version.
Rustup exact-version installation uses runner's rustup; no extra Rust action.
Firmware applications require Ariel/laze/imports/native prerequisites; standalone
ARM check is not a full firmware link/build or hardware execution. Attempt
applicable local builds and document unavailable/dependency gaps honestly.

Actions verified via official release -> full commit pages on2026-11-17:
checkoutv6.0.0 =1af3b93b6815bc44a9784bd300feb67ff0d1eeb3;
setup-pythonv6.0.0 =e797f83bcb11b83ae66e0230d6156d7c80228e7c.
Sources: https://github.com/actions/checkout/releases/tag/v6.0.0 and
https://github.com/actions/setup-python/releases/tag/v6.0.0 (linked commit pages).
Node24 runner support required (setup-python states runner>=2.327.1).
Shell git remote access currently DNS-blocked; browser verified official pins.
No claim of remote Actions execution. Record validator availability; static
contract checks complement but do not replace actionlint/GitHub execution.

## Milestones

1. Commit plan/trust/status/CI scope freeze. Tracker/handoff and Windows export.
2. Implement strict reporter, gate/status propagation wrapper and deterministic
expected-ABSTAIN smoke with targeted tests: all statuses, escaping, missing
attributions, units, hashes/tampering, deterministic bytes, collisions/rollback,
all exits and report-failure propagation. Full suite; commit/export.
3. Add workflow and reusable build script matching existing conventions, verified
SHA/version comments. Run local default/all-feature Rust, standalone8 telemetry
host tests, ARM no_std compile, Python, smoke and available workflow validation.
Attempt profiling-enabled/disabled firmware build where setup permits. Do not
hide unavailable checks or alter dependencies to force a green result.
4. Render saved four-status/eight-case Week9 examples locally, repeat for exact
bytes; save receipts/docs/results/readiness. Commit/export verified milestones.
Finish with remote-run prerequisites and Week11 fault-injection readiness.

Stage explicit paths/modes100644; staged check/stat/summary; no second agent.
Current: freeze. Next: implementation and meaningful tests.

## Completion evidence

Plan8b65a64, reporter2d33514, workflowa866525. Final317 Python tests/33 targeted
checks pass; independent eight-status examples/fresh default pair reproduce exact
bytes. Release receipt records final validation guards and input/code hashes.
Rust hostdefault8/allfeatures8/telemetry8 + standalone ARMno_std pass locally;
cached nrf9151-dk example profiling-on/off builds pass. Optional YAML/security
and Bash syntax checks pass; actionlint/GitHub execution unavailable, clean-runner
fetch/compatibility still required. No source locks, old workflow, model/calibration
or decisions changed. Current final evidence commit/export, next separately
requested Week11 fault injection. No posting, push, deploy or protection edits.
