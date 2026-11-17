# Week10 — local PR Markdown reports and CI software verification

Remote follow-up: [authorized fork verification](green-ops-remote-verification.md)
now records a successful exact-SHA run and actionlint. This document below
preserves the original local-only Week10 milestone history.

Verified cleanb2b6c08; branch green-ops/week10-ci-reporting. No push, report
posting/upload, deployment or branch-protection change. This is local evidence
and a checked-in workflow definition, **not observed GitHub Actions execution**.
All study estimates remain analytical_simulation and research-only.

## Implemented and preserved behavior

Plan/trust boundary freeze8b65a64; reporter/status wrapper2d33514;
pinned workflow/local build evidencea866525. APIs and commands are documented
in [reporting/CI guide](green-ops-ci-reporting.md).

- Strict version1 decision+policy+trusted SHA validation, finite/type/field/unit/
  range/status/block/model/context/hash checks and battery/contribution accounting.
  Known attribution methods and baseline artifact identity are checked; unknown
  methods do not masquerade as compatible physical explanations.
- Deterministic local Markdown includes statuses/reasons, model and candidate/
  baseline labels, workloads/windows/context, estimates/ranges/budgets/units,
  regressions, battery assumptions/omissions, compatible top3 signed influences,
  provenance, failed observed coverage and artifact references. Missing explanations
  explicit; user strings/keys HTML/Markdown/link/control/bidi escaped.
- Renderer exit0 means successful rendering, including an ERROR report. The
  atomic JSON+Markdown gate wrapper preserves0/1/2/3; rendering/validation/output
  failure blocks1 and rolls back both owned outputs. Inputs/existing files are
  never overwritten; no GitHub posting interface exists.
- Exact defaultABSTAIN3 is tested by software-only smoke with no research override.
  Its success is explicitly NOT candidate approval. Unexpected gate statuses,
  overrides, inconsistent artifacts or nondeterministic bytes fail verification.
- Gate parser extraction shares existing arguments without changing decisions.
  All original frozen models, calibration, Week9 decisions and lock files remain
  unchanged. No retraining, recalibration, evaluation tuning or hardware action.

Hash integrity is checked against a trusted producer's digest; hashes do not
authenticate an attacker who controls both data and expected hashes. The local
wrapper regenerates decisions from verified source artifacts for approval paths,
instead of treating an edited Markdown/JSON file as evidence. No validated95%
coverage, physical causation or legal-compliance certification is claimed.

## Four-status Markdown demonstrations

Eight existing frozen Week9 decisions are rendered without changing their
source values, thresholds or statuses. The [reproducer](results/week10/reproduce.py)
and [hash receipt](results/week10/reproduction.json) record inputs/implementation.
Two final independent runs produced identical11 files (8 example Markdown,
fresh default JSON+Markdown, receipt). Earlier local render runs remain under
build; final validation-only tightening preserved all Markdown/decision bytes.

| Example | Decision / gate exit | Renderer exit |
|---|---|---:|
| [Research PASS](results/week10/pass_upper.md) | PASS0, explicit unvalidated override |0|
| [Budget FAIL](results/week10/fail_upper.md) | FAIL2 |0|
| [Interval crossing](results/week10/abstain_crossing.md) | ABSTAIN3 |0|
| [Default coverage](results/week10/default_coverage_abstain.md) | ABSTAIN3, no override |0|
| [Malformed units](results/week10/error_wrong_units.md) | ERROR1, provenance not established |0|
| [Battery shortfall](results/week10/battery_five_years_fail.md) | FAIL2 |0|
| [Missing workload](results/week10/battery_missing_workload_abstain.md) | ABSTAIN3 |0|
| [Same-feature regression](results/week10/same_features_regression.md) | Research PASS0, point change0%, not execution observability |0|

A [fresh default wrapper decision](results/week10/fresh-default-decision.json)
and [report](results/week10/fresh-default-report.md) retain exit3 and blocks_ci=true;
the wrapper never converts that to approval. The workflow's expected-ABSTAIN
software test independently verifies the blocking result before returning0.
There is no actual candidate-energy-approval job and no continue-on-error or
unconditional success masking candidate exits.

Underlying power148.0601303mW, range[134.7377232,161.3825374]mW; research ceilings
100/150/200mW retain their predeclared illustrative meanings. Nominal family
coverage remains28/30 power,28/30 total energy,26/30 per-delivery (all<95%).
High-airtime shifts23/30,23/30,24/30 have no calibrated guarantee. No new rows,
independent families or coverage evidence were created this week. At1000mAh,
3.6V,0.8usable,0.9efficiency the existing stationary-workload battery projection
remains about17.5h, not its configured5-year target. No duty/loss factors reapplied.

## Local tests and build evidence

[Validation receipt](results/week10/local-validation.json) records tool versions,
commands and log hashes at the initial reporter milestone. Final validation-only
checks are covered by the317-test release suite and separate release receipt. Tests include all
statuses/exit propagation, Markdown/HTML/entity/link/control/bidi handling,
missing/incompatible attributions, unit/number/hash tampering, policy/model/
reference mismatch, deterministic output, aliases/collisions, rollback after a
second publication failure and renderer failure blocking an otherwise passing gate.

| Check | Local outcome and scope |
|---|---|
| Full Python unittest, ResourceWarning errors | Release317 passed (12 new,108.365s); initial316 evidence retained |
| Targeted reporter+gate tests |33 passed |
| Rust workspace host default |8 tests passed, excluded hophop/nrfxlib-sys-pretty as test/05 |
| Rust host all-features |8 tests passed, same exclusions; locked dependencies |
| Standalone telemetry host |8 tests passed, rustc -D warnings |
| ARM thumbv8m.main-none-eabihf |standalone telemetry no_std library compilation passed |
| nrf9151-dk hophop-examples |profiling enabled AND disabled cached release builds passed; no flash/run |
| Script syntax |bash -n passed |
| Workflow YAML |PyYAML parse, duplicate-key rejection and local security contract checks passed |
| actionlint |unavailable locally; not claimed |
| GitHub Actions |not executed; remote verification required |

Rust actual version1.99.1, Python3.14.4. Local Rust toolchain is namedstable at
those exact bits; CI installs named1.99.1. Shell Git/registry DNS was unavailable:
normal firmware attempt failed to resolve index.crates.io, then both cache-only
builds succeeded. Existing unused ESP dependency-patch warnings remain unchanged;
no Cargo.lock, vendor code or dependency updates made. Full all-board/app test/07
matrix was not run; standalone ARM compilation is not full firmware validation.
Optional PyYAML is local tooling, not a new runtime/standard-library dependency.

## Workflow and remaining external verification

.github/workflows/green-ops-ci.yml runs push/pull_request on ubuntu-24.04,
contents:read only, persist-credentials:false, explicit timeouts. Rust1.99.1 and
Python3.14.4 pinned. All third-party actions are full40-character verified SHAs
with version comments. Official release/commit sources are linked in the guide;
checkoutv6.0.0 and setup-pythonv6.0.0 pins were checked via official GitHub pages.
Shell remote-tag checks failed DNS, not silently treated as verification.

No secrets, pull_request_target, direct event-to-shell interpolation, comments,
uploads, deployment or branch-protection edits. Existing buildtest.yml is
unchanged; these hardening statements concern only the newly added workflow.
The [YAML/security receipt](results/week10/workflow-validation.json) is not a
claim of complete actionlint semantics or remote approval.

Still required on a future authorized remote run: actual Actions schema/runtime
validation, Node24-capable runner (setup-python requires>=2.327.1), exact toolchain/
Python release availability, dependency fetches from a clean hosted runner,
fork-PR read-only behavior and real check-name integration. No branch-protection
changes have been made. Existing legacy workflow still runs independently.

## Reproduce and Week11 fault-injection readiness

From repository root, with a new output directory:

```sh
python3 docs/results/week10/reproduce.py build/green-ops-week10-fresh
python3 tools/green_ops/green_ops_ci_smoke.py
python3 -W error::ResourceWarning -m unittest discover -s tools/green_ops/tests
GREEN_OPS_RUST_TOOLCHAIN=stable CARGO_NET_OFFLINE=true bash tools/green_ops/ci_rust_checks.sh
```

The last command assumes an installed matchingstable1.99.1 plus cached locked
host dependencies/ARM target; otherwise use installed named1.99.1 as documented.
Neither it nor any demonstrated firmware command flashes or operates a radio.

Ready for Week11 fault injection across report/policy/hash tampering, missing
inputs/models/context/attributions, incompatible workload/units/provenance,
coverage failures, unexpected exits and partial publication. Keep decision
JSON authoritative; preserveERROR1/FAIL2/ABSTAIN3 as blocking. Test software smoke
independently from actual approval and never enable overrides to force CI green.

Physical accuracy, exchangeability, validated95% intervals and true code-energy
observability remain unsupported. Shared analytical formulas and consumed study
sets are not new physical evidence. Week11 should not turn fault tests into
model tuning or silently reset calibration/evaluation consumption. No push,
remote publication, deployment or hardware action occurred; Windows local export
is refreshed separately as requested and the repository tracker is authoritative.
