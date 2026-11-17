# Week 7 current task / next step

Branch green-ops/week7-ml-regression, clean entry9138511. Read Week7 plan and
frozen recipe tools/green_ops/recipes/week7-regression-v1.json before changing
anything. Current: recipe/splits/source hashes frozen; no fit has run.
Next: materialize/audit actual 540 primary +180 stress bundles, then ML core.
Incoming tests246. Existing feature contract3, datasetv2, v1 compatibility fixed.
Selection train/CV/validation and locked evaluation must remain separate stages.
No tuning after test/stress. No push/publish. Physical validity unestablished.

Freeze commit6c4662e. Current task: actual materialization/audit; no fit yet.

Dataset now materialized/replay-audited: build/green-ops-week7/dataset,720 bundles,
540 primary+180 stress,360/90/90 primary rows in24/6/6 families. Dataset digest
e921297009bc1b12ca325cf13dfc16fbf4e4c5013bceb28fd1dbd02b18b9cf98; audit in
 docs/results/green-ops-week7-dataset-audit.json. Dataset tests5 pass. Current:
commit verified data milestone. ml_pipeline.py and tests exist as uncommitted
numerical-core work;9 toy numerical/model tests pass, but no actual fitting or
held-out scoring has run. Next core commit and then workflow tests/selection.
