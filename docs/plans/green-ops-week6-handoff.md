# Week 6 review current task / next step

Branch: green-ops/week6-analytical-reference. Review entry: clean 9ed6b96,
range 1726971..9ed6b96. Initial verified corrections: f8c35bf.
Current: final reviewed corrections/docs verified and ready for local commit.
Next: commit final milestone, immediately record its hash, then close this review.
Actual Week 7 training remains a separately requested continuation.

Final evidence: 246 tests pass (22 new review/design cases), ResourceWarning
errors enabled; git diff --check passes. Audited /tmp/green-ops-week6-review-panel:
96 primary + 192 separately scoped stress rows, 24 traffic families. Primary
table CLI succeeds; mixed hidden-coefficient panel correctly not primary-ready.
All source/state/packet/sensitivity replay checks pass; old 1.0.0 demo still loads.

Read green-ops-week6-review.md and current progress tracker. Proposed Week 7:
540 fixed-scope primary rows, 36 families, 24/6/6 train/validation/test families;
180 stress rows only for held-out test families. Freeze design/splits first.
No fitting or split optimization was performed. No physical/model accuracy claim.

New APIs: analytical_design.plan_workload_grid, load_design_record,
audit_reference_dataset. Keep full-slot offers/fixed parameters/retry cap for
current pre-run inputs; separate stress panels. Groups contain duration/seed/
repetition/model variants; seed draws are group-local. Coarsen groups for known
parent-related configurations that change family keys. Do not infer physical
independence from labels. Generator arithmetic patch1.0.1; existing v1/dataset v2/
feature-contract3 remain compatible. No push or publish. Verify Git status first.
