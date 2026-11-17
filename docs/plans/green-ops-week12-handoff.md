# Week 12 handoff

Complete: frozen benchmark executed and reported. Branch
`green-ops/week12-benchmark-evaluation`; baseline673d203 was clean. Protocol
commit e2a9fc7; verified pre-scoring tooling2f3559c; results4b2e75c.
Final documentation-only checkpoint follows. No push/publication/merge/deploy.

1920unique cases,16new coarsened parents,48streams,960validation/960locked
(8parents each),109historical parent exclusions. All frozen engine/model/
calibration/policy/recipe hashes verified and unchanged. BOTH partitions consumed;
FROZEN_UNSCORED in old recipe/receipt remains historical, not current data status.
Do not tune or restore freshness using new seeds.

Locked:949complete,11infeasible,0invalid,271relative5%oracle violations.
Validation:950complete,10infeasible,0invalid,281violations. All1920ABSTAIN3/block,
0positiveFAIL,552missed violations,576compliant-control abstention blocks;
0FAIL false alarms does not establish selectivity. Absolute200mW analytical
point violations29locked/32validation. Every pair has unchanged X/predictions;
no fault is observable in the frozen pre-run context. No calibration transfer.

Two independent process executions reproduce3844files exactly. Each audit checks
3819complete state ledgers+21null infeasible outcomes with independent rational
energy/units/time/oracle arithmetic. Final full suite353 passes,114.947s,
ResourceWarning errors, scoring source2f3559c unchanged. Archived data/receipt
hashes and deterministic Markdown regeneration verified. No Week12 remote run
or physical validation. Historical remoteff801898 verification is separate.

Evidence: docs/results/week12/{execution,preflight,manifest,aggregate,reproduction,
local-verification}.json and cases.jsonl. Detailed docs/green-ops-week12-results.md;
project summary/priorities docs/green-ops-project-results.md. Raw replayable files
remain in ignored build/green-ops-week12-a/b. Reproduce with:
`python3 docs/results/week12/reproduce.py /tmp/green-ops-week12-replay-new`.
New directory required; about80MB. Executor0 means software completed, not approval.

Next proposed work (requires a new task, no current blocker/user action):
actual-state TX/CPU/retry/beacon/fragment/delivery telemetry, separate post-run
feature contract, synchronized PPK2 validation, then a predeclared genuinely
fresh physical parent-disjoint study. Keep current negative benchmark intact.
Do not optimize frozen model/policy against consumed outcomes or claim hardware
coverage/detection, model causal proof, battery certification or physical RTT.
