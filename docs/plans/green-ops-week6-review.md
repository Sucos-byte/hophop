# Week 6 review before training — in progress

Entry: clean `green-ops/week6-analytical-reference` at `9ed6b96`; reviewed
`1726971..9ed6b96`, the actual generator/model, artifact/table contracts and tests.
No applicable AGENTS.md found. No push, publishing or training is authorized.

Official Nordic revision history, DECT NR+ current table and common conditions
were rechecked. The recorded PS 1.1 (June 2025), units and point values match.
Current applicability remains limited to the stated minimum-latency conditions;
all timing, independent loss, current envelopes and optional RTT remain assumptions.

Concrete corrections under verification:

- Numeric intermediate overflow/underflow in generic energy integration:
  evaluate the complete product at Decimal precision before float conversion;
  generator arithmetic patch version 1.0.1. Genuine nonfinite results still fail.
- Arbitrary offers/retry/model parameters can vary while current pre-run X is
  identical. A full-slot workload-grid policy and fixed-parameter readiness
  audit now expose this mismatch; general single-run APIs remain compatible.
- Caller group labels alone cannot prevent repeated/parameter/duration variants
  from leaking. The new design audit checks traffic families, group-local seeds,
  duplicate realizations and source/replay consistency before training readiness.
- Source hashes listed in a table manifest were not sufficient to validate the
  complete local analytical bundle for training. The design audit opens archived
  sources, verifies hashes and identities, and replays state/packet accounting.

45 focused tests pass, including 18 new review/design cases. A larger
multi-configuration acceptance panel, final full suite and final readiness/design
assessment follow. Current task: commit verified corrections; next: generate
and audit a fixed-parameter panel plus separate parameter-stress variants.
