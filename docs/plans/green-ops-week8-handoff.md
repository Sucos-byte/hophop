# Week8 current task / next step

Entry00c19c2 clean; branch green-ops/week8-uncertainty-explainability.
Current: pre-analysis plan/recipe/lineage freeze, no new labels generated.
Read week8 plan and tools/green_ops/recipes/week8-uncertainty-v1.json.
60 new families,30cal/30eval; prior3460 files/48families excluded. Week7 model
choices stay frozen. Methods: family-max raw residual95%,20 block permutations,
training-mean signed contributions, original-training-only fixed-alpha ablations.
Next: implement/test dataset/calibration/explanation/artifact APIs; commit verified
code, ablation fits before calibration, calibration before evaluation. No tuning,
no push/publish; all analytical_simulation, physical validation pending.

Freeze commit3e0dd39. Dataset ready build/green-ops-week8-data,1800 source replays
pass. First full suite284 passes; final rerun after stricter explanation summary
validation is underway (/tmp/green-ops-week8-final-tests.log). No real-study
scores inspected. Next commit verified code/data audit, then ablations/commit,
calibration/commit, locked evaluation. Original model hashes unchanged.

Final full suite284 passes (106.8s), including latest validators. Code/data
milestone ready to commit; real scoring stages still pending in prescribed order.

Methods/data committed6da8dba. Actual ablations running to
build/green-ops-week8-ablations (CLI replay then original-training-only fits).
Next archive/commit ablations.json; then calibrate/commit before evaluation.
