# Week9 — research-only budget gatekeeper and battery projection

Verified clean340a5b769338357b17ca9818d7c907e5f3c02485; branch
 green-ops/week9-gatekeeper. Read tracker, Week8 results/handoff, standing export
instructions, actual dataset/feature/model/calibration/explanation and safe-output
APIs. No applicable AGENTS.md found. Incoming284 verified tests; do not rerun an
unchanged baseline. No retraining, recalibration, evaluation tuning, GitHub Actions,
PR Markdown reporter, deployment, push or remote publication. Windows status
snapshot updates remain explicitly authorized and separate from Git publication.

## Predeclared semantics and contracts

Strict policy green_ops_budget.json version1, unknown keys/types/nonfinite numbers
rejected, canonical units mW/mJ/uJ and percent. Research-only scope; exact feature
contract3/raw_pre_run_v1, frozen model hashes and prediction context. Actual source
bundles replay via existing APIs, recompute predictions with frozen models and
calibration; never trust an editable prediction JSON alone. Hash exact consumed
policy/source/model/calibration/recipe/evidence bytes. Reference coverage and
attributions are pinned to archived Week8 artifacts and their hash receipt.

Statuses/exits: PASS0 every required criterion met in explicitly accepted scope;
FAIL2 a defined accepted criterion violated; ABSTAIN3 valid but unsupported or
insufficient evidence; ERROR1 malformed/incompatible artifact/processing failure.
Aggregate precedence ERROR > FAIL > ABSTAIN > PASS; FAIL/ABSTAIN both block CI.
Missing baseline is valid insufficient evidence. Wrong units/contracts/model,
artifact tampering, invalid numeric inputs and output collisions are ERROR.
Unsupported provenance, scope, unmatched workload/windows or unavailable interval
applicability abstain. Label source commit identities as metadata, not features.

For an upper budget T, accepted [L,U]: PASS if U<=T (equality passes), FAIL if
L>T (strict), otherwise ABSTAIN. Default evidence requires observed family
coverage>=0.95. Week8 nominal28/30 power,total and26/30 per-delivery fail that
requirement; default criteria abstain even with generous numerical budgets.
A demonstration override requires BOTH policy opt-in and explicit CLI flag;
output prominently states unvalidated research-only evidence, no95% guarantee.
Assumption-shift use additionally requires policy opt-in, and always carries
unvalidated distribution-shift status. No implicit fallback to point-only pass.

Regression compares compatible same-workload/windows/model/provenance/context.
Absolute allowance A: PASS if candidate.U<=baseline.L+A; FAIL if
candidate.L>baseline.U+A; else ABSTAIN. Relative allowance R percent uses
baseline.L*(1+R/100) and baseline.U*(1+R/100), requires positive baseline bounds.
Zero/missing baseline for relative comparison abstains; absolute differences
allow zero. Report point delta/percent diagnostically with finite checks.
These are logical comparisons of two marginal ranges, NOT a calibrated interval
for a difference or joint confidence claim. Fixed model + identical permitted
features produces identical predictions regardless of commit identity; gates
assess configuration-based estimates, not execution/code energy regressions.

Battery usable load-side energy mWh = capacity_mAh * nominal_voltage_V *
usable_fraction * conversion_efficiency. Apply these factors once. Capacity
fraction excludes conversion loss; powers must be load-side before conversion.
Projection hours=load_energy_mWh/mean_power_mW; years=hours/(24*year_days).
Require explicit year_days, positive capacity/voltage, fractions(0,1], target_years
configurable (five years only an engineering target, no regulatory claim).
Workload modes: continuous repetition of supplied run-average power (already
includes duty cycle; no second duty multiplier allowed), OR explicitly compatible
mutually exclusive component states whose time fractions sum1. Missing profile,
unconfirmed compatible states, zero/negative or unbounded physical power abstain.
Malformed fractions/double-counting fields ERROR. State powers are declared
analytical assumptions; same load boundary/conditions and complete cycle required.
Lifetime inverse range [E/Pupper,E/Plower]; lower-target equality passes, wholly
below fails, crossing abstains, only when required evidence is accepted. No
aging, self-discharge, environmental/temperature, load-dependent voltage or
capacity degradation model; explicitly report omitted effects. No hardware claim.

## Milestones

1. Commit this policy/semantics freeze and default strict example before code;
record coverage/shift limitations. Refresh tracker/handoff/Windows snapshot.
2. Implement pure comparison/battery calculations and strict policy/evidence/
report API+CLI tools/green_ops/green_ops_gatekeeper.py. Test independent units,
threshold equality/crossings, baselines, provenance/applicability, tampering,
nonfinite/overflow, all exits and publication rollback. Verify/commit/export.
3. Demonstrate PASS/FAIL/ABSTAIN/ERROR with explicitly labeled research fixtures
and unchanged frozen predictions. Predeclared illustrative power ceilings200
(pass override),100(fail override),150(crossing),200(default coverage abstain);
these are policy-test examples, not optimized/physical budgets. Use the same
lexicographically first nominal Week8 evaluation run as Week8 demo, no outcome
selection. Battery examples use transparent engineering assumptions. Reproduce
reports/exit codes; save strict JSON, docs and test evidence. Commit/export.
4. Final compatibility/full suite, tracker/handoff and Week10 readiness. No
additional modeling research or automation. Export before stopping/input.

Stage explicit paths, modes100644; staged checks/stat/summary before commits.
Current: semantics freeze. Next: implementation and targeted tests.
