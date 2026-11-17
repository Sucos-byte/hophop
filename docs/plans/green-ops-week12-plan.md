# Week 12 frozen benchmark execution plan

Baseline 673d203; branch green-ops/week12-benchmark-evaluation. No push or
publication. Repository progress is authoritative. Historical Week11 recipe and
receipt remain byte-unchanged; FROZEN_UNSCORED describes their creation, not the
subsequent consumption status recorded here and in the execution receipt.

1. Verify exact frozen dependency hashes, 1,920 case identities, 16 coarsened
parents, 8/8 parent splits (960 cases each), 48 streams and historical exclusions.
Commit this protocol before scoring.
2. Add execution/aggregation tooling and targeted tests without changing the
three frozen engine files, models, calibration, policy, severity or outcomes.
Commit verified tooling before generating any Week12 energy labels.
3. Execute both partitions with identical tooling, no intervening selection or
tuning. Record consumption when execution starts, including unsuccessful runs.
Independently execute again into a fresh directory; compare all artifact/report
hashes and deterministic outputs. Preserve infeasible/null outcomes.
4. Commit evidence, final report, project results/limitations and handoff.

Frozen outcomes: the existing workflow's 5% relative analytical oracle and
positive_fault_detection definition are authoritative. Report its unchanged
200mW absolute point diagnostic separately. ABSTAIN/ERROR blocks are never
positive detections. Controls include none and every severity-zero variant;
report their abstention blocks alongside false alarms. Inputs and observability
come from the existing adapter, never from energy labels.

Aggregation is descriptive: each case counts once; variants/repetitions are
dependent within parent. Give counts and explicit denominators for rates,
stratify split/fault/severity and parent. Feasible paired energy changes use
mJ, relative percent and average-power mW; null/infeasible pairs are excluded
with counts. Also report equal-parent mean effects. Only eight locked parents:
no population intervals, detection guarantee, significance or hardware claim.
No model/policy improvement based on either partition. Any protocol correctness
defect requires an explicit incident and impact assessment, not silent repair.

Raw replayable artifacts/reports may reside under ignored build/ paths;
committed case records, raw/compressed hash inventory, aggregates and reproduction
receipt support regeneration. Strict new-output-directory publication rolls back
partial files on errors. A separate durable consumption record survives rollback.
Executor success means completed software execution, never candidate approval.

Current task: frozen preflight and tooling. Next: tests and pre-scoring commit.

## Completion

Protocol e2a9fc7, pre-scoring tooling2f3559c, evidence4b2e75c. Frozen preflight
passes;1920cases run twice,3844files match and rational audits pass. Both splits
consumed. All1920ABSTAIN,0detections,552missed5%violations,576control blocks;
21infeasible labels remain null. Final353tests pass114.947s. No frozen changes,
tuning, current remote run or physical claims. Final reports/project follow-up
and deterministic archived hashes verified; task complete, no required user action.
