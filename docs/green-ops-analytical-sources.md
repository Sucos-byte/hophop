# Analytical source audit — nRF9151 DECT NR+

Checked official Nordic pages on 17 November 2026. The
[revision history](https://docs.nordicsemi.com/r/bundle/ps_nrf9151/page/chapters/rev_history/nrf9151_rev_history.html)
identifies Product Specification revision **1.1, June 2025**. This audit uses the
HTML edition. Section names and symbols below identify the tables exactly;
the DECT table in this HTML edition has no displayed number. No PDF page or
numbered section is inferred from a distributor's older PDF.

| Source ID | Exact section/table locator | Used parameter |
|---|---|---|
| dect-tx | Current consumption → Electrical specification → DECT NR+ current consumption, unnumbered table, ITX_PL13_LOW_LATENCY | Typical 235 mA, power level 13 (19 dBm), minimum-latency operation |
| dect-rx | Same table, IRX_-90DBM_LOW_LATENCY | Typical 47 mA, received signal -90 dBm |
| dect-idle | Same table, IIDLE_LOW_LATENCY | Typical 37 mA, NR+ enabled awaiting an operation |

The [official DECT current table](https://docs.nordicsemi.com/r/bundle/ps_nrf9151/page/_tmp/alta.nrf9151/autodita/application.current/parameters.id_current_dect_nr.html)
labels these values for bands 1, 2, 9 and 22 under nominal conditions. Its
footnotes explain that minimum-latency operation leaves some slow-starting blocks
powered. These are typical scenario values, not maximum current guarantees.
The initial profile pins band 1 and this mode; it does not model other powers.

[Current consumption, Table 1: common conditions](https://docs.nordicsemi.com/r/bundle/ps_nrf9151/page/chapters/current_consumption/doc/frontpage.html)
sets 3.7 V, 25 C, sleeping application CPU, idle peripherals and no RAM retention.
The same table lists cache enabled and application HFCLK (HFINT source) and
LFCLK not running. These application-side conditions are not a claim that the
active DECT modem has no running clocks. This is the reference condition, not a
voltage/temperature response model.
The following LTE-specific conditions are not used. No LTE PSM/eDRX/RRC energy
or current values are imported into NR+ states.

## Assumptions and source gaps

No firmware-specific prepare/airtime/ACK/backoff durations, retransmission loss,
ACK-to-application acceptance mapping, or RTT calibration was established from
these sources. Those remain configurable assumptions with declared ranges.
A ±20% current sensitivity envelope is an engineering scenario assumption; it
is not a specification tolerance. No runtime source download is required.

The model uses exclusive scenario currents rather than summing separately
reported CPU/peripheral currents. Application work, board regulators, LEDs,
USB/debugging, temperature, retention, modem firmware effects and rail scope
need physical validation. The profile is a reference approximation, not a claim
that any existing hophop firmware operates in the specified low-latency state.

A future profile may use additional official data only after recording revision,
locator, conditions and units. If a page becomes inaccessible, retain this audit
and mark any unverified replacement as a source gap; do not replace it with LTE
figures. Manufacturer HTML can change: the shipped catalog pins audited facts
and its hash identifies the exact local catalog used, not an official signature.
