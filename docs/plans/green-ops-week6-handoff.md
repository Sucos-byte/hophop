# Week 6 current task / next step

Branch: green-ops/week6-analytical-reference. Entry baseline: 1726971.
Completed software milestones: e2e8030 source/plan, d9de639 core, 9f13f8f
artifacts/CLI/sensitivity, c17c95d workflow and final verification.

Current task: Week 6 software complete; final documentation-only checkpoint.
No implementation is pending in the approved scope. Next: physical calibration
and independent model validation, or a separately requested Week 7 continuation.
Verify actual Git status/HEAD before new work; do not infer hours or accuracy.

Evidence: 224 tests pass with ResourceWarning errors (27 new analytical tests).
Full diff check passes. /tmp/green-ops-week6-demo has two analytical rows built
through existing table CLI; hashes/provenance/seeds, exact state-time sums,
null default RTT and 18 sensitivity cases per run were checked.

Read green-ops-week6-plan.md, current progress tracker and
../green-ops-analytical-reference.md. Source audit: ../green-ops-analytical-sources.md.
Generator: tools/green_ops/analytical_reference.py. CLI:
green_ops_generate_analytical.py --parameters FILE --workload FILE
--assumptions FILE --output-dir NEW_DIR [--prediction-context FILE].
Use saved analytical-workload-a/b.json and analytical-context-pre/post.json.

All generated rows are synthetic/simulation/analytical_simulation, dataset v2,
feature contract 3. Official currents are mode/conditions-bound. Timings, loss,
uncertainty envelopes and optional RTT remain assumptions. No measured PPK2 or
physical capture was created; v1 behavior is preserved. No push or publish.
