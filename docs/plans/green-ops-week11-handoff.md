# Week11 current task / next step

Branch green-ops/week11-fault-injection; clean baseline46b1b9c. Freeze d0d6331,
implementation24b746a. Current: Week11 complete, final dev/frozen-proposal evidence
committed00a4466; no implementation pending. Release341 tests pass (24 new,111.869s), full replay/independent
85-file development output determinism verified. Read docs/green-ops-fault-injection.md,
docs/green-ops-week11-results.md and Week11 plan.

Five core mechanisms change state/workload before energy: CPU busy-poll, actual
TX lock with unchanged request, bursty retry storm, beacon hyper-wakeup and
fragment bloat. All assumptions/ranges/lineage explicit; new artifact v1 does not
masquerade as reference v2. Infeasible schedules rejected before fault integration,
labels null. Targets never inflated. Frozen models/calibration/policies unchanged.

40 dev cases/1parent/2streams:28active hidden faults leave intended4X/predictions
unchanged; all40gates ABSTAIN3/would block, positives0.11oracle>5% violations
undetected;2fragment cases also exceed200mW.12compliant controls blocked too;
0FAIL false alarms is not claimed selectivity. Offline simulations already ran;
no physical execution blocked. Full artifacts/reports/sensitivity docs/results/week11.

Week12 tools/green_ops/recipes/week12-fault-benchmark-v1.json FROZEN_UNSCORED;
freeze receipt docs/results/week11/week12-freeze.json.16newparents,8validation/
8locked,1920uniquecases/48streams,109historical/dev parent exclusions. No energy,
predictions or scores generated for Week12. All related fault/power/seed/duration
variants stay together. Next separately authorized Week12 scoring/implementation,
never optimize against locked outcomes. Keep oracle labels separate from actual
production point checks and accepted gate alarms; ABSTAIN/ERROR are not positives.

No current-task push/publication/merge/deploy; earlier remoteff801898 verification
is historical only. No physical/Nordic unsupported source/95% assurance claims.
Refresh atomic Windows status after milestones/input/before stopping per export
policy; tracker authoritative. No user/hardware action required now.

Verified code/accounting24b746a; final development/freeze evidence00a4466.
Subsequent checkpoint documentation only; no remote run for Week11.
