# Week 6 current task / next step

Branch: green-ops/week6-analytical-reference. Baseline: 1726971.
Committed: e2e8030 plan/source/profile; d9de639 analytical core.
Verification: 11 core tests pass; incoming full-suite evidence 197 tests.

Current task: one-at-a-time parameter sensitivity and explicit analytical
artifact API/CLI. Core is in tools/green_ops/analytical_reference.py; exact
schema/profile at models/nrf9151-dect-reference-v1.json. Existing table contract
requires exact manifest keys, analytical_reference and a delivery_summary hash
for validated counts. Use synthetic/simulation/analytical_simulation only.

Next: implement archived source snapshots, state/packet evidence, modeled
delivery summary, deterministic output and table integration tests; commit only
a verified milestone and immediately update tracker with actual hash. Then
workflow/demo, final suite and review. No fake PPK2; no push/publish. Official
currents are mode/conditions-bound; timings/loss/envelopes/RTT are assumptions.
End-of-window acceptance is late, outside [start,end). Verify status on resume.
