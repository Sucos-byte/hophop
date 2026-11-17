# Green-Ops acquisition protocol

Hardware acquisition is pending. Passing summary-contract tests establishes
software behavior; neither GPIO-labeled test dictionaries nor manually authored
PPK2 summaries establish a physical capture. The Week 5 demo is synthetic.

## Setup record before powering the DUT

Record board model/revision/serial, firmware full commit and dirty state,
modem firmware version, SDK/toolchain and radio configuration. Record ambient
conditions, antenna, network/peer setup, device/session IDs, and evaluation
family. Unique group names alone do not establish independent experiments.

Record supply voltage at the measured rail, external supply model, PPK2 hardware
and software versions, selected source-meter or ampere-meter mode, sampling
settings/range, expected peaks, and calibration/zero procedure. Record USB,
debugger and LED states and whether their power is included. Declare whether
energy covers a specific SoC rail or the whole board. A rail measurement does
not automatically include GPIO supplies, regulators or peripherals.

Check exact board revision against the corresponding Nordic schematic and
current-measurement procedure. The
[nRF9151 DK hardware guide](https://docs.nordicsemi.com/r/bundle/ug_nrf9151_dk/)
is the entry point; the
[SMA DK procedure](https://docs.nordicsemi.com/r/bundle/ug_nrf9151_sma_dk/page/ug/nrf91_dk/measuring_current/hw_measure_ppk.html)
is a different board variant. Archive the applicable procedure revision and
annotated circuit before choosing isolation links or pin connections. This
protocol does not prescribe board pins without that identification.

Nordic's [ampere-meter procedure](https://docs.nordicsemi.com/r/bundle/ug_ppk2/page/ug/ppk/measure_current_ampere_meter.html)
requires an external DUT supply and recommends a lab supply for accuracy; its
example wiring is explicitly for an nRF9160 DK. Do not copy its connector
numbers to another board. In source mode the PPK2 supplies the DUT: avoid a
second supply driving that same isolated rail. In ampere mode ensure the
intended current path passes through the instrument rather than a parallel
supply path. Verify common ground and rail isolation before enabling power.

The [PPK2 connector reference](https://docs.nordicsemi.com/r/bundle/ug_ppk2/page/ug/ppk/ppk_user_guide_connectors.html)
identifies VIN for ampere mode, VOUT toward the DUT, ground, and the logic
port's VCC/GND/digital inputs. The
[official getting-started specifications](https://www.nordicsemi.com/Products/Development-hardware/Power-Profiler-Kit-2/GetStarted)
list 0.8–5 V supply support and up to 1 A capability with appropriate USB power;
these instrument limits do not establish the board's permissible rail voltage.
Digital-marker voltage limits must also be checked separately against that
reference and the board's GPIO domain. Sources checked 17 November 2026.
No DECT state current or timing values are assumed here.

## Bounded acquisition sequence

1. Predeclare fixed workload duration, settings, repetitions and grouping.
   Initial pilot proposal: at least five repetitions per configuration. Randomize
   configuration order with a recorded seed; estimate variability before
   choosing a final sample size. Keep failed runs and explicit rejection reasons.
2. Warm up and settle the board/instrument. Record the settling criterion and
   actual settling time. Verify supply, background activity and logging state.
3. Capture cumulative counter baseline and start marker in one device clock
   domain, or archive a quantified clock mapping. Bound the baseline-to-marker
   gap; it contributes to uncertainty. Start energy and packet accounting at
   the same defined boundary.
4. Execute the fixed workload headlessly; retain sender offers, receiver
   acceptance, device telemetry and instrument raw samples. Avoid debugger or
   host timing dependencies unless their effects are part of the experiment.
5. Emit the end marker and capture endpoint counters with the same documented
   boundary semantics and quantified gap. Use half-open intervals `[start,end)`
   for packets and energy integration. Archive elapsed duration and uncertainty.
6. Save raw traces, marker/clock mapping, counter endpoints, packet records,
   run metadata, firmware/modem versions and SHA-256 checksums. Archive the
   integration method, voltage, sample gaps/clipping, instrument settings and
   failure notes. Hashes identify bytes; they do not prove truthful acquisition.
7. Validate single-segment continuity, counter deltas, run/window IDs, physical
   alignment references, duration and power/energy consistency. Declare policy
   tolerances before acceptance; do not widen them only to rescue a failed run.

Serial host arrival timestamps alone do not locate device boundaries precisely.
A serial mapping requires measured latency/jitter and an uncertainty bound.
Measure GPIO-marker and logging overhead with controlled repetitions and record
whether reported total energy includes those contributions. Missing samples,
resets, saturation, multiple segments and unacceptable alignment invalidate a
bounded run; do not salvage it through per-segment maxima.

Subtract cumulative counter baselines. Any idle-energy subtraction must be a
separate reported quantity with its own protocol, alongside total energy.
Unknown or early-terminated workloads cannot support the fixed-duration pre-run
profile; use an explicit post-run context and retain the failed-run record.

## Delivery and RTT

Sender offers use session-qualified logical packet IDs; retransmissions retain
the logical ID. Receiver delivery means unique application acceptance in the
same session/window. Deduplicate in the evidence adapter before constructing a
summary. Late arrivals outside `[start,end)` are excluded from window delivery
and recorded separately. Do not substitute receive operations for offers or
radio decodes for application delivery.

RTT requires correlated ping/reply IDs measured on one clock or an independently
calibrated mapping. RX/TX timestamps alone are insufficient. The current dataset
builder leaves RTT null; future hardware RTT artifacts must archive correlated
evidence. No measured label should be filled merely from asserted metadata.

## Acceptance and evaluation boundary

The two synthetic demo runs must produce two rows with null targets. Analytical
contract fixtures must form a separate analytical-only table with a model ID,
version, configuration hash and assumptions-document hash. PPK2 tests exercise
simulated contracts only. Lab acceptance still needs actual raw captures,
board-specific wiring review, repeatability and independent evidence review.

Later evaluation groups must keep related session/device/repetition families
and fault variants together. Analytical model accuracy is separate from hardware
accuracy; synthetic demos provide no hardware calibration. Five years remains
an engineering battery policy target, with no universal EU mandate established.
