# Week 6 — sourced analytical reference generation

Approved scope: deterministic standard-library analytical reference generation,
versioned parameters/assumptions, state-time accounting, sensitivity and existing
v2 artifact/table integration. No training, push, publishing or hardware claims.

## Verified entry and compatibility

Entry HEAD: `1726971dd46b67c45e9e23aa0b50b91000dc64a3`, clean on
`green-ops/week5-measurement-contract`; created
`green-ops/week6-analytical-reference`. No applicable AGENTS.md found. Read current
progress, Week 5 review and actual dataset/table/feature-contract code. Incoming
suite evidence: 197 passing tests. Do not rerun unchanged baseline for counting.

Keep DATASET_FIELDS and v1 behavior frozen. Generated rows use dataset v2,
feature contract 3, synthetic/simulation/analytical_simulation only. Analytical
manifests must match the current exact manifest keys and model reference hashes.
Never construct measured PPK2 evidence. No implicit prediction capabilities.

## Milestones and acceptance

1. **Plan and source audit.** Pin official Nordic HTML document revision, section,
   table/symbol, operating conditions and units. Store a machine-readable source
   catalog with a versioned model profile and a separate assumptions document.
   Source gaps do not block generic accounting. Verify references before using
   numbers. Commit plan/audit and immediately record the hash in the tracker.
2. **Accounting and generator.** Add analytical_reference.py with strict,
   nonmutating model/workload validators and deterministic accounting. Exclusive
   idle/TX/RX states; microsecond timing; fixed observation interval. Explicit
   timing/loss/optional RTT assumptions with ranges. Reject oversubscribed slots
   before sampling; do not silently truncate or bias selection by success.
   Test independent unit/energy examples, conservation, zero traffic, retries,
   determinism, no global random state, wrong types/ranges and overflow. Commit
   verified core and immediately checkpoint tracker/handoff.
3. **Artifact CLI and sensitivity.** Add explicit analytical artifact API/CLI;
   archive model/configuration, assumptions, state/packet evidence, modeled
   delivery summary, sensitivity results and generated row/manifest. Preserve
   seed, groups, model/version and parameter/assumption digests through source
   manifest references. Reuse output reservation/rollback. Parse/hash identical
   source snapshots, validate artifacts before publication, reject aliases and
   existing destinations. One-at-a-time low/high scenarios for every nontrivial
   assumption range; record invalid scenarios without silently dropping them.
   Test strict loading, exact hashes, deterministic bytes, failures and real
   end-to-end table loading/filtering. Commit and checkpoint immediately.
4. **Workflow, review and final verification.** Document schema/formula,
   assumptions versus supported facts, source audit, two-run table commands,
   sensitivity interpretation and physical limitations. Run focused checks,
   acceptance demo and one full suite after final code changes. Review v1/
   feature-role compatibility and scientific claims. Commit, update tracker with
   actual hashes/test evidence and leave a concise resumption handoff.

No actual hours are inferred from milestones or tests. Stage explicit paths;
normal Python/JSON/Markdown modes 100644; inspect staged diff/check/stat/summary.

## Scientific design decisions

The initial source profile describes only nRF9151 minimum-latency DECT NR+,
nominal 3.7 V/25 C, band 1 and requested TX power 19 dBm, RX signal -90 dBm.
Other supported table bands may be described by the source but are not silently
extrapolated. Model state currents are exclusive scenario totals; do not add CPU,
peripheral or idle currents on top and double count. No deep-sleep curve,
voltage/temperature/TX-power scaling, firmware timing or board overhead is
inferred. A generic integrator can independently exercise arbitrary test states.

A packet occupies a declared fixed slot: idle preparation, TX, RX/ACK wait;
failed attempts may add idle backoff and retry. Idle fills all remaining time.
Local TX completion, ACK decode and logical delivery have different counts.
The loss and ACK-equivalence model is an explicit simplification, not a radio
channel validation. Offers at slot starts belong to [0,duration); every offered
packet has a full reserved slot. Reject incomplete slots instead of inventing
completion. Zero offered packets produces idle energy and null per-delivery.

Use a versioned SHA-256 counter-based Bernoulli sampler keyed by seed, packet
and attempt, giving deterministic common random draws for sensitivity scenarios.
No real random or wall-clock input. Optional RTT is a declared model calculation
for successful exchanges; default null. Retries/queuing assumptions are archived.

Use official typical currents as point estimates, with separately marked assumed
uncertainty ranges. Sensitivity changes are assumptions even when the baseline
is sourced. Ranges are scenario bounds, not manufacturer tolerances or confidence
intervals. Sensitivity results are not additional independent observations.

## Current task / next step

Current: source audit and versioned profile; generic implementation not started.
Next: commit verified audit/profile, then implement core with independent energy
oracles. See progress tracker for the latest actual commit and checks.
