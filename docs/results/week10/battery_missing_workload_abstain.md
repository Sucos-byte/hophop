# Green Ops engineering-policy report

**ABSTAIN — exit 3; BLOCKS.**

**RESEARCH ONLY. No hardware assurance or legal-compliance certification.**

**ANALYTICAL SIMULATION; unvalidated evidence**

**EXPLICIT UNVALIDATED RESEARCH OVERRIDE — no validated 95% coverage.**

| Field | Value |
|---|---|
| Reason codes | \[&quot;battery\_workload\_profile\_missing&quot;\] |
| Provenance | analytical\_simulation |
| Decision SHA256 | 97194933ec335295fdd9a3bc6285665637597a1e9585558ea62523740dd7d0a5 |
| Candidate identity label | research\-candidate\-label\-not\-an\-observable\-feature |
| Baseline identity label | Not provided |

## Policy, model and comparable context

| Field | Value |
|---|---|
| Policy | RESEARCH\-FIXTURE\-battery\_missing\_workload\_abstain |
| Policy SHA256 | 0bd646eeda49ee8fb9d57a2472f02fe773f1ea19a4ec5be7e403125c8199d885 |
| Evidence label | UNVALIDATED RESEARCH\-ONLY OVERRIDE; NO VALIDATED 95% COVERAGE OR HARDWARE ASSURANCE |
| Override requested / used | \[true, true\] |
| Feature contract/profile | \[3, &quot;raw\_pre\_run\_v1&quot;\] |
| Comparison scope | configuration\_estimates\_only |

### Model identities

| Field | Value |
|---|---|
| target\_energy\_per\_delivered\_packet\_uj | 95e90fee96268d211d6e4dc4c26ead7166a1440d52fc9a832f386e10b332c64a |
| target\_mean\_power\_mw | 0605d0c3c95cdac6b8fb2941308e21875355e3c5f7dcc6aa922b9590c0dc606b |
| target\_total\_energy\_mj | a45c065e435a92e6592635da1bdea505e8b95a32a5699fd32477d0a23852f1d4 |

### Workload and windows

| Field | Value |
|---|---|
| baseline | Not provided |
| candidate\.adapter | analytical\-reference\-v1 |
| candidate\.assumptions\_sha256 | 3ba5877e065aeb16ebb450e19580928824e19933e1536d6e8e52ddd4854ed694 |
| candidate\.feature\_profile\_id | dect\-reference\-v1 |
| candidate\.interval\_ms | 180 |
| candidate\.max\_attempts | 3 |
| candidate\.offered\_packets | 27 |
| candidate\.parameters\_sha256 | 8773204c3d7b175b3c84effa2098468e728ccf1a7db26c6e582fe1e8012d4f55 |
| candidate\.payload\_size\_bytes | 80 |
| candidate\.seed | 13313103955936235453 |
| candidate\.tx\_power\_dbm | 19 |
| candidate\.window\_duration\_ms | 5000 |

### Prediction context

| Field | Value |
|---|---|
| baseline | Not provided |
| candidate\.available\_fields | \[&quot;interval\_ms&quot;, &quot;payload\_size\_bytes&quot;, &quot;tx\_power\_dbm&quot;, &quot;window\_duration\_ms&quot;\] |
| candidate\.completed\_as\_planned | true |
| candidate\.planned\_window\_duration\_ms | 5000 |

### Domains

| Field | Value |
|---|---|
| baseline | Not provided |
| candidate | primary |

## Required criteria

| Field | Value |
|---|---|
| baseline | Not provided |
| candidate | Not provided |
| comparison\_method | inverse\_power\_bounds\_engineering\_projection\_not\_confidence\_interval |
| id | battery |
| kind | battery\_minimum\_years |
| reason\_code | battery\_workload\_profile\_missing |
| status | ABSTAIN |
| target | target\_mean\_power\_mw |
| threshold | 5 |
| unit | years |

## Battery assumptions and projection

| Field | Value |
|---|---|
| assumptions | \[&quot;constant nominal voltage/capacity&quot;, &quot;usable fraction excludes conversion loss&quot;, &quot;efficiency applied once to energy&quot;, &quot;load\-side power excludes conversion loss&quot;, &quot;stationary repeating workload&quot;, &quot;engineering target, no compliance certification&quot;\] |
| available | false |
| capacity\_mah | 1000 |
| conversion\_efficiency | 0\.9 |
| hours\_per\_year | 8766\.0 |
| load\_energy\_mwh | 2592\.0 |
| omitted\_effects | \[&quot;aging&quot;, &quot;self\_discharge&quot;, &quot;temperature\_and\_environment&quot;, &quot;load\_dependent\_capacity\_and\_voltage&quot;, &quot;battery\_replacement\_and\_transients&quot;\] |
| reason\_code | battery\_workload\_profile\_missing |
| target\_years | 5 |
| usable\_fraction | 0\.8 |
| voltage\_v | 3\.6 |
| workload\_profile | Not provided |
| year\_days | 365\.25 |

Five years is a configurable engineering-policy target, not a certification. Run-average duty is not applied twice.

## Top-three compatible model attributions

Signed influence relative to the model training baseline, in target units. Model influence is not proven physical root cause.

### Candidate

| Field | Value |
|---|---|
| Target | target\_energy\_per\_delivered\_packet\_uj |
| Unit | uJ |
| Method | compatible\_archived\_week8\_signed\_model\_contribution |
| Training baseline | 26849\.634557536836 |
| Prediction | 26054\.921228715903 |
| interval\_ms | \-596\.9686602917885 |
| payload\_size\_bytes | \-216\.39777979793485 |
| window\_duration\_ms | 18\.65311126879153 |

| Field | Value |
|---|---|
| Target | target\_mean\_power\_mw |
| Unit | mW |
| Method | compatible\_archived\_week8\_signed\_model\_contribution |
| Training baseline | 149\.73973432666668 |
| Prediction | 148\.06013026336225 |
| payload\_size\_bytes | \-1\.8580012580576046 |
| interval\_ms | 0\.18269107659322908 |
| window\_duration\_ms | \-0\.0042938818400618355 |

| Field | Value |
|---|---|
| Target | target\_total\_energy\_mj |
| Unit | mJ |
| Method | compatible\_archived\_week8\_signed\_model\_contribution |
| Training baseline | 798\.78701932 |
| Prediction | 739\.8463950396329 |
| window\_duration\_ms | \-49\.9263491530335 |
| payload\_size\_bytes | \-9\.985786217465563 |
| interval\_ms | 0\.9715110901318496 |

### Baseline

Missing explanations: no compatible attributions provided.

## Evidence and artifact references

| Field | Value |
|---|---|
| baseline | Not provided |
| candidate\.assumptions | 3ba5877e065aeb16ebb450e19580928824e19933e1536d6e8e52ddd4854ed694 |
| candidate\.calibration\_set | f686446aa1b6e124cc3c60cc01341953c8ffaa05132a6ab002245cf6276fc5b4 |
| candidate\.evaluation\.json | 74a86bbeb117b6907afc355e016bbc5aefcea1c81de2d8d0ef34e78d2729329c |
| candidate\.explanations\.json | 26cdd40938c6d1c316020b0af00490f0e40bc7e898e9766d69b1a51d3ee68759 |
| candidate\.original\_recipe | 4a979b6cec4555c27d1813f33dc8481410e1ba2382dec2bb93b8366be32d1daf |
| candidate\.parameters | 8773204c3d7b175b3c84effa2098468e728ccf1a7db26c6e582fe1e8012d4f55 |
| candidate\.selection | 31e53f4e8f4317be71bc8fed6b0024f0985a1cc5e195f4c833d43ae62acf226b |
| candidate\.source\_dataset | 5296369ebdeceba0037931513f6a7f0d06f75072a6dd2ce7f18a157420040928 |
| candidate\.source\_manifest | b3dbe30bd5602d54bb7aa67127703a1a68583ab44be705c194b6e14fad55f9ee |
| candidate\.study\_recipe | 547c93bf038eb9a064571f3d1d46f28fb071e1f76106673ec537e597d3cb20fa |
| candidate\.target\_energy\_per\_delivered\_packet\_uj\-calibration | 42ab820b364efcff5e5f129dc037f34803f97aa346922d188c2938379bcdab44 |
| candidate\.target\_energy\_per\_delivered\_packet\_uj\-model | 95e90fee96268d211d6e4dc4c26ead7166a1440d52fc9a832f386e10b332c64a |
| candidate\.target\_mean\_power\_mw\-calibration | 7b100a97607f3821bc6efaa72b5a10f3f71de59e4963eab41139426b97ed082b |
| candidate\.target\_mean\_power\_mw\-model | 0605d0c3c95cdac6b8fb2941308e21875355e3c5f7dcc6aa922b9590c0dc606b |
| candidate\.target\_total\_energy\_mj\-calibration | 26cc914103919e9bb96783b5eac3237bfab579fb0dd97aaac0ac7d0156ae0ef7 |
| candidate\.target\_total\_energy\_mj\-model | a45c065e435a92e6592635da1bdea505e8b95a32a5699fd32477d0a23852f1d4 |

## Uncertainty and coverage

| Field | Value |
|---|---|
| allow\_assumption\_shift | false |
| allow\_unvalidated\_research\_intervals | true |
| minimum\_family\_coverage | 0\.95 |
| Coverage reference | observed\_Week8\_nominal\_family\_coverage\_not\_a\_guarantee |

Observed nominal family coverage: power 28/30, total energy 28/30, per-delivery 26/30; below nominal 95%. Assumption shifts have no calibrated coverage guarantee.
Marginal interval comparisons are not calibrated difference or joint confidence intervals.

## Assumptions and limitations

| Field | Value |
|---|---|
| Assumptions | \[&quot;frozen analytical generator and prediction profile&quot;, &quot;intervals retain observed family coverage failures&quot;, &quot;comparable full\-slot workloads and windows for regression&quot;, &quot;no joint or difference confidence guarantee&quot;\] |
| Limitations | \[&quot;research\_only\_no\_hardware\_assurance&quot;, &quot;observed\_family\_coverage\_below\_nominal\_95\_percent&quot;, &quot;marginal\_ranges\_are\_not\_calibrated\_difference\_or\_joint\_confidence\_intervals&quot;, &quot;identical\_permitted\_features\_fixed\_model\_identical\_predictions\_regardless\_of\_commit&quot;, &quot;configuration\_estimate\_not\_actual\_execution\_telemetry&quot;, &quot;consumed\_week8\_data\_not\_reused\_for\_tuning&quot;, &quot;assumption\_shift\_has\_no\_calibrated\_coverage\_guarantee&quot;, &quot;model\_attribution\_not\_physical\_causation&quot;\] |

Identical permitted features yield identical fixed-model predictions regardless of commit identity. Configuration estimates are not execution telemetry.

Rendered locally. No GitHub comment, upload, publication or deployment performed.
