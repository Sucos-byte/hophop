# Local Markdown reporting and Green Ops CI software verification

Week10 adds a local Markdown renderer, an atomic gate/report wrapper and a
push/pull-request software-verification workflow. It does not post comments,
upload artifacts, approve physical energy behavior, deploy or change branch
protection. The authoritative decision remains strict Week9 JSON and exact
PASS0/ERROR1/FAIL2/ABSTAIN3 semantics. Both FAIL and ABSTAIN block an actual gate.

## Validate and render a decision

```sh
python3 tools/green_ops/green_ops_report.py --decision DECISION.json --decision-sha256 TRUSTED_SHA256 --policy POLICY.json --output NEW_REPORT.md
```

Inputs: strict version1 Week9 JSON, corresponding exact policy bytes, and a
SHA256 from a trusted producer/inventory. The renderer checks size limit4MiB,
strict duplicate/nonfinite-free JSON, exact field sets, version/status/exit/block
consistency, research/no-assurance flags, criterion membership/thresholds/units,
numeric ranges, model/feature/policy and frozen evidence hash bindings,
aggregate statuses/reasons, battery units/loss assumptions and attribution
accounting/target compatibility. ERROR uses its distinct shape and unestablished
provenance; its policy need not be valid (that can be the reported error).
Missing explanations remain explicitly missing.

Hashes establish integrity against the supplied trusted digest, not authenticity
against an attacker who replaces both data and expected hashes. The renderer is
not a physical-evidence verifier or an alternate decision engine. It does not
retrain/recalibrate. Fresh approval paths should use the wrapper below, which
replays source evidence and binds freshly produced decision bytes. A lone
renderer exit0 means rendering worked even for an ERROR decision; it is never
an energy-approval exit.

Rendered content includes candidate/baseline identity labels (not automatically
actual commits), model identities, workload/window/context/domain, criterion
values and marginal intervals/units/budgets/regression diagnostics, battery
capacity/voltage/fractions/year/workload assumptions and omitted effects,
compatible top3 signed model contributions, provenance, coverage and all artifact
reference hashes. All untrusted strings and keys are inert escaped table cells:
HTML/Markdown punctuation, links/mentions, newlines, controls and bidi. The
renderer creates no user-controlled URLs, raw HTML or dynamic fences.

Attributions are model influence relative to the training baseline, not proven
physical causes. Identical permitted features produce identical fixed-model
predictions regardless of commit labels. Marginal intervals do not form a
calibrated difference/joint confidence interval. Five years remains an engineering
policy target, not a legal-compliance certification. Analytical and unvalidated
research results, overrides and failed observed family coverage are prominent.

New outputs only: reserve before processing, reject aliases/collisions, publish
completed sibling temporaries and roll back owned outputs on failure. Previously
published or input files are never overwritten. No network posting API exists.

## Preserve approval exits with the wrapper

```sh
python3 tools/green_ops/green_ops_gate_report.py --policy tools/green_ops/policies/green_ops_budget.json --candidate docs/results/week9/source --output NEW_DECISION.json --markdown-output NEW_REPORT.md
```

All existing gate options are shared via its parser, with required Markdown
output added. The wrapper stages the real gate's decision, validates/hash-binds
and renders it, then publishes JSON+Markdown as a rollback group. It returns the
gate's exact0/1/2/3; report/validation/publication failure returns1 and blocks.
A published Markdown file can therefore accompany a blocking exit. Existing
destinations or outputs inside input source directories are rejected.

Current default evidence must return ABSTAIN3: nominal family coverage is28/30
power,28/30 total energy,26/30 per delivery, below95%. No default CI step enables
research override. Any future real approval job should invoke this wrapper as
an ordinary required command; never use continue-on-error, `|| true`, or convert
nonzero to green. No such real candidate-approval job is installed this week,
because these configuration estimates do not observe code-energy regressions.

## Software-only smoke and workflow scope

```sh
python3 tools/green_ops/green_ops_ci_smoke.py
```

The smoke invokes the default wrapper twice with no override, requires exact
ABSTAIN3/coverage reason/block flag, compares deterministic JSON and Markdown,
and returns0 only for **software verification**. Unexpected PASS/FAIL/ERROR,
missing output, changed override or nondeterministic bytes fail the smoke. Its
success is explicitly NOT candidate approval. This preserves the difference
between testing blocking behavior and hiding a failed candidate gate.

.github/workflows/green-ops-ci.yml runs on push and pull_request:

- ubuntu-24.04, contents:read only, no persisted checkout credentials, explicit
  timeouts. No secrets/event strings in shell, pull_request_target, comments,
  upload/publication, deployment or branch-protection modification.
- Rust1.99.1, exact toolchain installation/ARM target, same host workspace
  exclusions as test/05_cargotest.sh, with lock enforced/default+all features;
  standalone8 telemetry host tests and thumbv8m.main-none-eabihf no_std compile.
  The standalone ARM compile is not a full firmware link or hardware execution.
- Python3.14.4, full unittest suite with ResourceWarning errors and the clearly
  named expected-ABSTAIN software smoke. No optional runtime dependencies.

Reusable Rust script: `bash tools/green_ops/ci_rust_checks.sh`. It requires exact
rustc1.99.1. Local toolchain namedstable at that exact version can be selected with
GREEN_OPS_RUST_TOOLCHAIN=stable; CARGO_NET_OFFLINE=true uses existing cache. CI
installs named1.99.1 and fetches locked dependencies normally. No lock/dependency
updates are introduced. Existing buildtest.yml remains unchanged; new workflow
pinning/permissions do not retroactively alter that older workflow.

Third-party actions use verified full commit SHAs with release comments:

- checkoutv6.0.0:1af3b93b6815bc44a9784bd300feb67ff0d1eeb3, from
  [official release](https://github.com/actions/checkout/releases/tag/v6.0.0) and
  [commit](https://github.com/actions/checkout/commit/1af3b93b6815bc44a9784bd300feb67ff0d1eeb3).
- setup-pythonv6.0.0:e797f83bcb11b83ae66e0230d6156d7c80228e7c, from
  [official release](https://github.com/actions/setup-python/releases/tag/v6.0.0) and
  [commit](https://github.com/actions/setup-python/commit/e797f83bcb11b83ae66e0230d6156d7c80228e7c).

Verified via official pages2026-11-17, not assumed from floating tags. Node24
runner support is required; setup-python release specifies runner>=2.327.1.
Hosted runner Rust/Python download availability and dependency/registry access
remain external assumptions. No GitHub Actions execution has been observed.

## Local validation and Week11 boundary

Run exact Python tests, software smoke and reusable Rust checks from repository
root. Firmware setup is documented in docs/green-ops-telemetry.md and existing
laze/test scripts; profiling-enabled/disabled nrf9151-dk example builds require
Ariel imports/native tools and cached or reachable dependencies. These commands
compile only; never flash/run hardware. Initial shell network DNS failure is not
reported as a code failure or concealed; successful cached builds are distinct.

Optional local PyYAML parses the workflow with duplicate-key rejection and checks
triggers, pins, permissions, lack of overrides/untrusted interpolation/hidden exits.
This is a syntax/security contract check, not full actionlint or remote validation.
PyYAML is not an application/test installation requirement. actionlint is absent
locally; GitHub execution, runner compatibility and branch-policy integration
must be verified remotely in a later authorized push. No remote run is claimed.

Week11 can inject malformed/tampered reports/policies, missing context/models,
publication failures and unexpected exits without treating software smoke green
as energy approval. Physical validation, exchangeability and real code-energy
observability remain separate unsatisfied research limitations.
