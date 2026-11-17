# Proposed next sprint — evidence-capable diagnostic foundation

Design proposal only. This audit does not authorize implementing the sprint,
new model fitting, benchmark tuning or hardware actuation. Resolve acceptance
choices through the [requirements matrix](../green-ops-requirements-evidence-audit.md)
and implement the [post-run contract](../green-ops-observability-design.md)
without changing frozen artifacts. Ordered work is intentionally small: establish
trustworthy application observations first, leave unsupported deeper states null.

## Sprint objective / demonstrable exit

One opt-in bounded two-role diagnostic workload emits replayable, versioned
application operation/fragment/delivery observations with explicit clock/quality
records. Host fixtures prove bookkeeping and strict schema separation; firmware
builds prove integration only. No CPU-residency, PA-power, internal retry,
physical energy or latency-accuracy claim until the relevant backend/evidence is
available. If latency scope decision is pending, deliver operation/delivery
protocol tests and leave RTT feature/labels unaccepted; do not force a scope choice.

An implementation can be accepted as **laptop software milestone** independently
of later **hardware evidence milestone**. Never report the former as the latter.
Numeric hardware accuracy/jitter/overhead/detection thresholds below require
predeclaration after scope agreement and before evaluating data, not post hoc
selection to make a pilot pass.

## Ordered work and file/interface map

New paths below are proposed, not existing APIs. Preserve all existing file and
CLI semantics; no in-place edits of frozen engine/model/policy/recipe/results.

| Priority / task | Proposed files and interfaces | Meaningful laptop tests / acceptance | Evidence still requiring hardware |
|---|---|---|---|
| P0 Contract and source capability boundary | New `tools/green_ops/execution_observation.py`: `validate_capabilities(data)`, `observation_from_bytes(content, *, expected_profile, expected_run_id, expected_window_id)`, `derive_diagnostics(observation)`; docs `green-ops-observability-design.md` becomes implemented contract; new `tests/test_execution_observation.py` | Strict version/types/keys/units; absent vs zero/partial/unsupported; counters/snapshot subtraction; reset/saturation/wrap rejection; bounded checked clock conversion; source hash/path safety; reference/model/profile mismatch; deterministic roundtrip; synthetic origin remains synthetic. Unknown actual-state values stay null | Capability claims must map to real firmware/API evidence; no physical validity from validator |
| P0 Typed host-testable event bookkeeping | New `examples/src/green_ops_execution.rs`: proposed `OperationId`, `OperationEvent`, `WindowSnapshot`, fixed-capacity pending-operation and logical-ID tracker; pure methods `on_submit`, `on_accept`, `on_complete`, `snapshot` | Standalone Rust tests: duplicate/unknown completion, rejected submit, pending at boundary, operation/counter overflow, snapshot race sequencing, full ring/drop counter, events exactly start/end, multi-boot invalidation, no allocation/no_std ARM. No wall-time-to-CPU conversion | IRQ/executor integration correctness, event timing/overhead/drop behavior under load |
| P1 Versioned application protocol and two roles | New `examples/src/green_ops_probe_protocol.rs` and `examples/src/bin/green_ops_probe.rs`; update `examples/Cargo.toml`, `examples/laze.yml` only as needed for opt-in binary/feature. Protocol has version/session/sender/sequence and optional fragment index/count/declared lengths, explicit request/reply type | Pure parser rejects malformed lengths/version, truncated/overflow/oversize fragment sets, duplicate/overlapping fragments and unoffered IDs; bounded reassembly evicts with reason; sender offer once across retransmit; stale session rejection. Two-role host state-machine simulation with deterministic packet schedules is labelled simulation | Two real peers, range/channel/modem configuration and authenticated identity scope. Application protocol does not reveal modem-internal retries/fragments |
| P1 Application hooks and complete operation results | Instrument new workload around `DectPhy::tx/rx`; only if needed additive opt-in hooks in `hophop/src/nrfxlib_phy/{mod,rx}.rs`. Track submit/accepted/error/completed outcomes, bytes and raw clocks. Do not assume completion timestamp is RF start | Simulate immediate API failure, PHY terminal error, no-data RX, PDC decode error, timeout, dropped events, pending cancellation and early termination; feature-disabled behavior preserved. Stable operation IDs, unique terminal status. Compile new and old example with feature enabled/disabled | Confirm observed callbacks correspond to recorded operation IDs on target; do not perturb legacy shared queue/handle assumptions without separate tests. Current wrapper handles are fixed and expect sequential events |
| P1 Clock/window acquisition and safe snapshots | New application ring record includes boot/segment IDs, modem ticks, application clock mapping samples, start/end snapshot sequence, capture quality. Host import uses existing window/delivery validation via explicit adapter | Exact `[start,end)` test vectors, late completions, completion vs submit cohorts, mapping drift/rounding and unequal frequency; concurrent endpoint consistency, deferred drain/drop invalidation. Absolute-deadline100ms snapshot unit tests only after cadence semantics chosen | Board clock mapping, drift and boundary uncertainty, IRQ latency, GPIO/PPK2 alignment. One-second RX cannot itself yield100ms state residency. Document sampler starvation and actual jitter |
| P1 Saved observation importer | New `tools/green_ops/green_ops_import_execution.py`: `--raw-log --capabilities --run --window --output-dir`; new tests `test_execution_import.py`. New log event prefix/version rather than changing old GREEN_OPS parser meanings | Whole-source immutable byte snapshots/hashes; bounded inputs, malicious path/unknown event checks; event ledger reconciliation; no target/fault/oracle read; collision/symlink/partial-output rollback; deterministic import; explicit unavailable evidence; preserve old converters and frozen replay | Import at least one real complete and one rejected/incomplete session without hand-authoring measured evidence |
| P1 RTT state machine, scope-dependent | New `examples/src/green_ops_probe_rtt.rs` or protocol state-machine module; new `tools/green_ops/rtt_evidence.py` only after supervisor choice. Use initiator submit/accepted reply timestamps and versioned evidence, not old hardware RTT backfill | Host expected values: ticks conversion, correlated echo, duplicate/late/wrong session, missing reply -> null/censored; finite follow-up, wrap/reset, bounded pending table; no clock mixing. Future opt-in dataset loader extension separately tests old hardware RTT rejection and new evidence path | Confirm responder behavior and endpoint timing on two boards; independent timing/logic validation and capture uncertainty. No physical latency target/predictor acceptance from host simulation |
| P2 Transparent accounting comparator | New `tools/green_ops/state_accounting.py`, `tests/test_state_accounting.py`; `estimate_energy(observation, parameter_bytes, *, rail_id)` produces estimates/bounds with exact references, never modifies observations | Hand-calculated V×I×time cases, exclusive/joint state conservation, overlapping CPU/radio rejection unless incremental-current model declared, unknown residency, zero delivery/null, rail/voltage mismatch, overflow and double-duty/loss rejection. Compare new observed data only, not tune old benchmark | Validated state residency and matching rail currents needed; absent actual transitions -> unsupported accounting. Fit development parameters only; independent measured labels remain separate |
| P2 Capability backend feasibility spikes, no promised API | Audit OS executor/idle/ISR hooks and hardware counter sleep/frequency behavior; vendor modem attempt traces/config readback capabilities. Add individual backend only with source/version/conditions and tests | Record “unsupported” with evidence if unavailable. A mock readback or assumed counter is a fixture, not production capability. No fabricated methods added merely to satisfy a registry field | CPU trace/residency reference, RF or supported config-readback verification, modem attempt-level evidence, actual wake-transition validation. May require modem vendor/tool access |

Files such as `tools/green_ops/feature_contract.py`, `ml_pipeline.py`,
`fault_{injection,workflow,benchmark}.py`, old dataset schemas and Week7–12
artifacts are compatibility boundaries, not targets for a silent new profile.
Any later model support uses a separately versioned diagnostic model loader;
freeze its exact feature subset, parameters, scope and source lineage before
fitting. Existing pre-run gate policies remain unchanged.

## Verification sequence and exit evidence

1. Commit contract/capability decisions and failing tests for the new protocol,
then small verified milestones for Rust bookkeeping, Python import and opt-in
integration. Synthetic fixture header must identify its actual origin.
2. On laptop: `python3 -W error::ResourceWarning -m unittest discover -s tools/green_ops/tests`;
standalone `rustc --edition=2024 -D warnings --test` for each pure module;
standalone ARM `thumbv8m.main-none-eabihf` no_std wrapper; existing
`bash tools/green_ops/ci_rust_checks.sh`. Reuse pinned toolchain conventions.
3. Build existing/new firmware examples via actual laze conventions, starting
`laze build -g -b nrf9151-dk -a hophop-examples -s green-ops-profile -D LOG=info`
and disabled counterpart, adapted only after inspecting the new binary/module
selection. Existing `test/07_app-build.sh` enumerates three boards/four applications;
its full matrix/dependencies are separate checks, not implied by standalone ARM
compilation. Builds do not flash or run devices. Record unavailable tooling.
4. Compare untouched frozen dependency hashes/preflight and Git diff; no scoring
needed for a documentation or telemetry-only compatibility change. Verify old
CLI/input rejection/output rollback semantics. Do not use consumed energy scores
to choose observations, severity or policy thresholds.
5. If later authorized, verify exact new SHA remotely for push and fork-PR;
current task authorizes neither. Keep default expected-ABSTAIN smoke explicitly
software-only and preserve all gate exit statuses. No PR comments/deployments.

Laptop exit evidence: archived commands/tool versions, test/build outcomes,
source/contract/capability hashes, one complete synthetic import and explicit
unsupported fields, one interrupted/drop-invalid import, old schemas/models
unchanged. It must be possible to determine which call produced each nonnull
observation without reading oracle labels or fault metadata.

Hardware exit evidence (later milestone): identify DUT/peer/PPK2/rail/firmware,
follow [acquisition protocol](../green-ops-measurement-readiness.md), collect
randomized instrumentation-enabled/disabled captures, demonstrate clock alignment
and actual operation/peer-ID reconciliation, publish raw evidence locally with
quality exclusions and uncertainty. Agree threshold tolerances before captures.
Report overhead including buffers/timers/logging, sample drop/starvation, effect
on intended workload and observed reset/saturation cases. PPK2 alone does not
validate TX radiated power, CPU residency or unique receiver delivery.

## Study after instrumentation (not part of this sprint)

Predeclare physical development/calibration/evaluation by device/session and
configuration parents, with all paired baselines/fault variants/repetitions kept
together. Verify overlap against every consumed analytical/physical group;
shared analytical laws are acknowledged even with new configurations. Pilot
variance determines defensible sample size; do not claim8groups suffice for
population coverage. Add independent ground-truth mechanism checks before
counting positives. Compare accounting, training mean and any learned diagnostic
using only features actually captured and available post-run. Report all missing
labels, infeasibility, false alarms, abstention blocks and misses.

Scope decisions before this study: latency A/B/C, exact original feature/cadence
requirements, required second adapter/optional models, physical rail and actual
readback/trace access, numeric accuracy/overhead/jitter/detection trade-offs,
academic rubric and remaining student effort/lab budget. Preserve current
negative results regardless of these decisions. No sprint exit is a claim of
final academic completion or physical firmware regression effectiveness.
