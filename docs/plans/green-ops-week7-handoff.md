# Week 7 current task / next step

Branch green-ops/week7-ml-regression; entry9138511. Recipe freeze6c4662e,
dataset13b6064, numerical coreea8fafd, tested workflow58cbe92. Pre-experiment
suite265 tests passes (19 new), ResourceWarning errors enabled.

Current: real train/CV/validation selection completed; commit exact models and
selection snapshots BEFORE evaluating held-out sets. Selection SHA-256:
31e53f4e8f4317be71bc8fed6b0024f0985a1cc5e195f4c833d43ae62acf226b.
Choices: mean-power ridge1.0; total-energy/per-delivery ridge0.01.
All real test/stress scores remain unobserved at this checkpoint.

Data: build/green-ops-week7/dataset (540 primary+180 stress,24/6/6 families).
Training: build/green-ops-week7/training, exact committed-copy destination
 docs/results/week7-regression-v1/training. Source/inventory digest:
e921297009bc1b12ca325cf13dfc16fbf4e4c5013bceb28fd1dbd02b18b9cf98.

Next AFTER selection commit: python3 tools/green_ops/green_ops_ml.py evaluate
--dataset build/green-ops-week7/dataset --training build/green-ops-week7/training
--output-dir build/green-ops-week7/evaluation. Do not refit/tune after inspecting
those results. Verify selection bytes/hashes remain unchanged. Then prediction
CLI example, save held-out reports/predictions, docs, final checks/checkpoint.
No push/publish. Analytical formula recovery is not hardware validation.
Week8 uncertainty/explainability remain out of scope. Verify Git status first.
