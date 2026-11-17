# Dashboard handoff

Complete local read-only dashboard on green-ops/dashboard-demo. Verified clean
entrybe90857; initial implementationbdd57c9, verified UI/browser correction
milestoneedb0322. Final documentation/verification-only checkpoint follows.
No push/publication/deployment/merge, backend execution or hardware actions.

Launch from repository root:
`python3 tools/green_ops/dashboard.py`
Open http://127.0.0.1:8765; Ctrl+C stops. No package install/cloud/database.
Five-minute professor walkthrough: docs/green-ops-dashboard.md.

Five views: Overview architecture/evidence/gaps; Experiments with configuration/
parent/split/window/hash and pagination; Predictions with mean/ridge comparison,
units/errors/intervals and distinct row/family coverage/assumption shift; validated
saved Gate decisions4statuses/reasons/budgets/regression/battery; Fault benchmark
with zero positive detections, oracle violations/blocks/controls/observability.
Persistent analytical/measured-not-established/unmeasured labels; no fake live
telemetry, measured trace or device status.33 pinned allowlisted artifact/document
resources. Hash/schema mismatch -> explicit unavailable section, no demo metrics.

Standard-library server binds127.0.0.1 only, fixed routes/resources, GET/HEAD only,
no arbitrary project file serving/symlinks, safe DOM text, CSP and Host/Origin
checks. Per-request input/pagination bounds; snapshots loaded at startup only.
New source schemas need deliberate adapter/catalog review, not blind hash refresh.
No models/results/policies/consumed-data records or frozen engines altered.

Verification: final368Python tests pass with ResourceWarning errors,15new dashboard
tests. JavaScript syntax passes; frozen dependency preflight passes without
scoring. Chromium159 checks all5views desktop1440x1000/narrow390x844, keyboard
navigation, filtering/pagination, missing data/XSS inert text, precise regression/
battery units,0external requests/console errors/page overflow. Six screenshots
and exact source/image fingerprints: docs/results/dashboard-demo. Visual inspection
covers desktop overview/interval/fault views and narrow overview; all layouts also
have automated overflow checks. No browser service left running after checks.

Limitations: saved analytical evidence only, historical source checkpointbe90857
is separately labelled from dashboard commit; no new predictions/decisions/live
measurements. Only Linux Chromium browser checked, no screen-reader/full a11y
or Firefox/Safari/Windows browser/forwarding/native server validation. Existing
remote evidence remainsff801898 only, not this branch. No new hardware claims.

Next BACKEND task remains docs/plans/green-ops-observability-sprint.md:
strict versioned execution_observation/capability validation and pure Rust
operation/logical-ID bookkeeping; then opt-in workload/importer. Keep post-run
profile separate from frozen pre-run model. CPU residency/local TX readback/
modem retry observations require actual supporting APIs/trace and physical proof;
no oracle or fault identity enters production X. Latency scope and original
18features/100ms/academic obligations remain supervisor decisions before affected
acceptance. This dashboard does not complete or tune that research/backend work.
No immediate required user/hardware action for the completed demo.
