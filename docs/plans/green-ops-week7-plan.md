# Week 7 — deterministic regression and grouped evaluation

Authorized: standard-library energy regression, grouped evaluation and strict
inspectable artifacts/prediction CLI. No push/publish. Uncertainty calibration
and explainability remain Week 8; no optional ML dependencies are installed.

## Verified entry

Clean at 9138511334218d147f1128d04b893eac7458725e on the Week 6 branch;
created green-ops/week7-ml-regression. Read instructions, current tracker,
Week 6 review/design, analytical design loader, feature contract 3 and strict
artifact/table/publisher APIs. No applicable AGENTS.md found. Incoming suite:
246 passing tests. Do not rerun an unchanged baseline just for counting.

## Frozen experiment before fitting

Recipe: tools/green_ops/recipes/week7-regression-v1.json. Pin actual parameter
and assumption SHA-256, generator/sampler versions, axes, split membership,
seeds, CV folds, targets, feature order and selection rules in that JSON.

- Primary: six payload levels (16..512 bytes as in review), six intervals
  (50,75,100,150,250,500 ms), three durations (1000,5000,10000 ms), five group-local
  seeded repetitions: 540 rows / 36 families. Full-slot offers, retry cap 3,
  nominal loss 0.1, fixed sourced-current profile; no hidden parameter pooling.
- Split by a target-independent seeded hash of traffic family: 24 train,
  6 validation, 6 test (360/90/90 rows). Four fixed CV folds within 24 training
  families; each fold has 18 fit / 6 assessment families. No fold uses validation.
- Stress: assumed TX-per-byte 1 and 10 us, only the six test families, matching
  seeds/durations: 90 rows per panel, 180 total. Retain common draws within
  families; never put test-family counterparts in training/validation.
- X is exactly current pre-run order: payload_size_bytes, interval_ms,
  tx_power_dbm, window_duration_ms. No engineered columns this week. TX power
  is constant; zero-variance columns use scale 1. No target, ID, group, seed,
  model hash, post-run count, energy or reconstructed state statistic enters X.
- Targets separately: mean power (mW), total energy (mJ), energy per positive
  delivered packet (uJ). Null labels remain null, explicitly excluded per target.
  Missing/nonfinite/unavailable X fails even when that row's label is absent.
- Models: training-mean baseline; ridge linear regression on train-standardized
  X with centered y/intercept unpenalized. Objective sum squared residuals plus
  alpha*sum(beta^2), alphas (0.01,1,100). Stable augmented Householder QR; no
  normal equations. No prediction clipping. No requirement to beat baseline.
- Selection: report four-fold grouped CV for baseline/all ridge candidates;
  shortlist the two ridge settings with best pooled CV RMSE, plus baseline.
  Validation RMSE alone chooses final model. Exact ties favor baseline, then
  larger alpha. Final model stays fitted on training only; no train+val refit.
- Persist selection/model hashes before test/stress evaluation. Evaluation is
  a separate command, accepts only frozen models, never calls fit or selection.
  No tuning after seeing locked-set metrics, including if results are poor.

## Milestones and verification

1. **Freeze recipe and dataset.** Commit recipe/splits before fitting. Implement
   deterministic materialization/loading; verify exact counts, IDs, family/seed
   isolation, expected source hashes/provenance and current design replay audits.
   Generate all 720 bundles under ignored build/green-ops-week7. Archive inventory,
   CSV tables and canonical dataset digest independent of destination paths.
   Keep label summaries out of selection except train/validation scoring.
2. **Numerical core.** Implement ml_pipeline.py: preprocessing, mean/ridge,
   stable QR, per-target preparation, metrics/per-family errors, strict model
   serialization and prediction compatibility. Targeted independent solutions,
   rank-deficient/constant features, train-only scaling, missing/nonfinite data,
   negative predictions, undefined R2, determinism and round-trip tests. Commit
   verified core, update tracker/handoff immediately.
3. **Selection and prediction workflow.** Fixed grouped CV, validation selection,
   locked evaluation/prediction CLI, versioned inventory/JSON artifacts, frozen
   source/dataset/recipe/split/model hashes. Test split/seed/capability leakage,
   no fit during evaluation, tampering, strict JSON, publication rollback and
   repeatability using small fixtures before running the real experiment.
4. **Training selection checkpoint.** Run real training/CV/validation only.
   Persist and locally commit selected models/settings and selection digest.
   Do not inspect test/stress performance until this choice is frozen.
5. **Locked evaluation and handoff.** Evaluate frozen test/stress exactly once;
   save predictions, per-target units/counts/MAE/RMSE/R2 and per-family errors
   for chosen and baseline models. Run prediction CLI demonstration. Document
   poor results and synthetic-formula limitations honestly. Final full suite,
   diff check, verified local commits, immediate tracker/current-next handoff.

Use strict UTF-8 JSON (no pickle), reject duplicate/nonfinite/unknown keys and
wrong types, preserve exact archived bytes, and use existing output reservation
with rollback or owned temporary directories for fresh multi-file publication.
Model artifacts record Python/dependency versions (stdlib only), feature order,
scaling/coefficients/intercept, target/unit, training membership, scope, settings,
recipe/dataset/split hashes and contract versions. Prediction is for validated
recorded analytical artifacts under current availability/completion requirements;
no invented completed execution or claim of prospective hardware inference.

Stage explicit paths; new Python/JSON/Markdown files mode100644; staged
check/stat/summary/index modes before each local commit. Log evidence, not
inferred research hours. Saved outputs in build are local; small frozen models
and reports may be committed as inspectable reproducibility evidence.

## Current task / next step

All five software milestones verified. Recipe/splits freeze6c4662e; real dataset
13b6064; numerical coreea8fafd; pre-experiment tested workflow58cbe92; frozen
model choice8b18a39 committed before locked evaluation. Actual540+180 counts and
source replay pass. Full suite267 passes (21 new tests), ResourceWarning errors.

Real locked evaluation and saved1620 predictions complete; no refit/tuning after
scores. Results/docs include weak power stress performance honestly. Final
prediction compatibility adds recipe/full-slot/retry policy and consumed-snapshot
hash checks without changing frozen estimator state or saved scores. All270
locked inputs pass the guard. Current task: commit final results/compatibility
milestone completed as ebd9998; tracker/handoff updated. Next is a
separately requested Week8 calibration/explainability design; current held-out
sets are already observed, and physical validation remains pending.
