# Local read-only dashboard implementation plan

Verified clean be90857; branch green-ops/dashboard-demo. Read instructions (no
AGENTS.md), tracker, requirements audit, project results, observability handoff,
actual Week7/8/9/12 artifact shapes and existing decision validator. No backend
execution controls, cloud/database, training, hardware or gate decisions run.

1. Freeze explicit display mapping and allowlisted artifact SHA-256 catalog.
   Read immutable snapshots, validate versions/provenance/bindings and expose
   missing/incompatible sections, never substitute hard-coded metrics.
2. Implement standard-library localhost-only HTTP server and paginated adapters;
   fixed static assets/resources, safe text rendering, strict paths/methods/Host.
3. Build accessible responsive overview/experiments/predictions/gates/fault views
   with persistent evidence labels, honest negative outcomes and useful filters.
4. Test adapters/malformed/missing/hash cases, status/provenance, pagination and
   HTTP file restrictions. Run browser desktop/narrow checks/screenshots if local
   tooling works. Document gaps and one-command/five-minute professor walkthrough.
5. Verify frozen sources/results/policies unchanged; update tracker/handoff/export
   and commit each verified milestone. No push/publication/deployment.

Metric/source mapping: docs/green-ops-dashboard.md (written before implementation).
Next backend task remains green-ops-observability-sprint.md; dashboard does not
implement actual-execution observation or fix unobservable hidden faults.

## Completion

Implementationbdd57c9; UI/browser correctionsedb0322.33pinned resources,5views,
15new meaningful tests, final368full-suite pass. Chromium desktop/narrow checks
and6local screenshots;9documentation links checked; frozen preflight/hashes pass
without scoring. One-command launch/five-minute demo and explicit UI/platform/
physical limitations documented. No backend execution/frozen changes/push.
Next backend remains observability contract/bookkeeping sprint.
