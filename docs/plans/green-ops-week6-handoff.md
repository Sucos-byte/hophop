# Week 6 review current task / next step

Branch: green-ops/week6-analytical-reference. Review entry: clean 9ed6b96.
Baseline range: 1726971..9ed6b96. Read green-ops-week6-review.md (in progress)
and latest tracker before resuming. No applicable AGENTS.md found.

Current: correction milestone ready for commit; 45 focused tests pass, including
18 new review/design cases. New analytical_design.py plans full-slot workloads,
group-local seeds and stable traffic families, verifies archived bundle hashes
and replays state/packet data, and audits identifiability/grouping/readiness.
Generic integrator intermediate-overflow correction uses generator version1.0.1.
V1/dataset v2/feature-contract 3 and single-run interfaces remain compatible.

Next: commit verified milestone and immediately record actual hash. Then run a
larger primary fixed-parameter grid plus two separate timing-stress panels,
check group/seed isolation and table integration, finish review/design docs,
run final full suite after changes, and commit final checkpoint. Do not train,
push or publish. Source currents remain conditioned typical values; timing,
loss, envelopes and optional RTT are assumptions. Physical validation pending.

Correction milestone committed: f8c35bf. Current task is now multi-panel
acceptance, followed by final suite and final review/design report. No training.
