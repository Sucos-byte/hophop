# Week7 current task / next step

Branch green-ops/week7-ml-regression; entry9138511. Milestones:6c4662e recipe
freeze,13b6064 data,ea8fafd core,58cbe92 pre-experiment workflow,8b18a39 selected
models BEFORE any real held-out score. Current: final results/compatibility
milestone verified and ready for commit; next immediately record its hash.

Full suite267 passes (21 new tests), ResourceWarning errors; git diff --check.
540 primary/36 families,24/6/6 train/validation/test, plus180 stress rows.
Selection31e53f4e8f4317be71bc8fed6b0024f0985a1cc5e195f4c833d43ae62acf226b
and all model hashes remain unchanged after test. No refit/tuning. Test RMSE
6.3664mW,51.1850mJ,991.1826uJ; stress powerR2 weak0.169–0.264. Saved1620
held-out baseline/chosen predictions and per-family metrics. No real label
missingness in these panels, but target-null handling is explicitly tested.

Read ../green-ops-week7-results.md, ../green-ops-ml-regression.md and Week7 plan.
Outputs build/green-ops-week7; committed model/report copies docs/results/
week7-regression-v1. Compatibility guards require recipe bytes for prediction
(--recipe FILE) and full-slot offers/retry cap, plus original manifest digest.
These tighten new-input checks only; all270 locked inputs pass; no scores changed.

No Week7 implementation remains after final commit. Next separately requested
Week8: predeclare new group-disjoint calibration/evaluation data before interval
or attribution choices. Existing validation selected models; existing test/
stress are already observed. No uncertainty/explainability implemented here.
All results analytical_simulation; not physical accuracy or battery evidence.
No push/publish, no inferred research hours. Verify Git status before resuming.
