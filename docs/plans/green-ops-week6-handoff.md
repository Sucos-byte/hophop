# Week 6 current task / next step

Branch: green-ops/week6-analytical-reference. Entry baseline: 1726971.
Committed milestones: e2e8030 source/plan, d9de639 core, 9f13f8f artifacts/CLI/
sensitivity. Latest focused verification: 25 analytical tests; 34 with affected
dataset CLI/publisher tests. Incoming full suite baseline: 197 tests.

Current task: final documentation and two-run reproducible acceptance workflow.
Next: save two workload/context fixtures; execute analytical generation and
existing table CLI in a fresh /tmp directory, inspect hashes/provenance/null RTT,
run final full suite after code changes, review contracts/scientific limitations,
commit and immediately record hash/results here and in progress tracker.

APIs: analytical_reference.validate_model, validate_workload, integrate_states,
simulate_reference, sensitivity_analysis, generate_analytical_artifact (immutable
parameter/workload/assumption snapshots in; exact file-byte mapping out).
CLI: green_ops_generate_analytical.py --parameters FILE --workload FILE
--assumptions FILE --output-dir NEW_DIR [--prediction-context FILE].
Existing table CLI accepts generated dataset.csv + manifest.json pairs.

All generated rows: synthetic/simulation/analytical_simulation, dataset v2,
feature contract 3. No implicit capabilities or fake PPK2. RTT defaults null;
optional RTT and all durations/loss/uncertainty envelopes are assumptions.
Official current facts/conditions are in ../green-ops-analytical-sources.md.
Read plan before expanding scope. Physical calibration/accuracy and actual
hours remain pending/unreported. No push/publish. Verify Git status on resume.
