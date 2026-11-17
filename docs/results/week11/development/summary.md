# Week11 analytical development diagnostics

**ANALYTICAL SIMULATION / RESEARCH ONLY. No physical detection or energy approval.**

ABSTAIN/ERROR may block; neither is a positive fault detection. Hidden actual states never enter pre-run X.

| Fault / severity | Actual energy mJ | Baseline mJ | Oracle violation | Gate / exit | Positive detection |
|---|---:|---:|---|---|---|
| beacon\_hyper\_wakeup/0 | 142\.247092 | 142\.247092 | false | ABSTAIN/3 | false |
| beacon\_hyper\_wakeup/1 | 142\.524592 | 142\.247092 | false | ABSTAIN/3 | false |
| beacon\_hyper\_wakeup/3 | 143\.079592 | 142\.247092 | false | ABSTAIN/3 | false |
| beacon\_hyper\_wakeup/20 | 147\.79709200000002 | 142\.247092 | false | ABSTAIN/3 | false |
| bursty\_retry\_storm/0 | 142\.247092 | 142\.247092 | false | ABSTAIN/3 | false |
| bursty\_retry\_storm/1 | 144\.3859288 | 142\.247092 | false | ABSTAIN/3 | false |
| bursty\_retry\_storm/3 | 148\.6636024 | 142\.247092 | false | ABSTAIN/3 | false |
| bursty\_retry\_storm/7 | 157\.21894960000003 | 142\.247092 | true | ABSTAIN/3 | false |
| cpu\_busy\_poll/0 | 142\.247092 | 142\.247092 | false | ABSTAIN/3 | false |
| cpu\_busy\_poll/1 | 142\.265222 | 142\.247092 | false | ABSTAIN/3 | false |
| cpu\_busy\_poll/400 | 149\.521847 | 142\.247092 | true | ABSTAIN/3 | false |
| cpu\_busy\_poll/1000 | 160\.43407200000001 | 142\.247092 | true | ABSTAIN/3 | false |
| none/0 | 142\.247092 | 142\.247092 | false | ABSTAIN/3 | false |
| payload\_fragmentation\_bloat/0 | 142\.247092 | 142\.247092 | false | ABSTAIN/3 | false |
| payload\_fragmentation\_bloat/1 | 146\.42202400000002 | 142\.247092 | false | ABSTAIN/3 | false |
| payload\_fragmentation\_bloat/3 | 154\.53745600000002 | 142\.247092 | true | ABSTAIN/3 | false |
| payload\_fragmentation\_bloat/15 | 207\.375676 | 142\.247092 | true | ABSTAIN/3 | false |
| tx\_power\_lock/0 | 140\.838872 | 140\.838872 | false | ABSTAIN/3 | false |
| tx\_power\_lock/1 | 141\.120516 | 140\.838872 | false | ABSTAIN/3 | false |
| tx\_power\_lock/5 | 142\.247092 | 140\.838872 | false | ABSTAIN/3 | false |
| beacon\_hyper\_wakeup/0 | 143\.3165104 | 143\.3165104 | false | ABSTAIN/3 | false |
| beacon\_hyper\_wakeup/1 | 143\.5940104 | 143\.3165104 | false | ABSTAIN/3 | false |
| beacon\_hyper\_wakeup/3 | 144\.1490104 | 143\.3165104 | false | ABSTAIN/3 | false |
| beacon\_hyper\_wakeup/20 | 148\.8665104 | 143\.3165104 | false | ABSTAIN/3 | false |
| bursty\_retry\_storm/0 | 143\.3165104 | 143\.3165104 | false | ABSTAIN/3 | false |
| bursty\_retry\_storm/1 | 146\.52476560000002 | 143\.3165104 | false | ABSTAIN/3 | false |
| bursty\_retry\_storm/3 | 152\.94127600000002 | 143\.3165104 | true | ABSTAIN/3 | false |
| bursty\_retry\_storm/7 | 165\.7742968 | 143\.3165104 | true | ABSTAIN/3 | false |
| cpu\_busy\_poll/0 | 143\.3165104 | 143\.3165104 | false | ABSTAIN/3 | false |
| cpu\_busy\_poll/1 | 143\.3345664 | 143\.3165104 | false | ABSTAIN/3 | false |
| cpu\_busy\_poll/400 | 150\.5588164 | 143\.3165104 | true | ABSTAIN/3 | false |
| cpu\_busy\_poll/1000 | 161\.42238640000002 | 143\.3165104 | true | ABSTAIN/3 | false |
| none/0 | 143\.3165104 | 143\.3165104 | false | ABSTAIN/3 | false |
| payload\_fragmentation\_bloat/0 | 143\.3165104 | 143\.3165104 | false | ABSTAIN/3 | false |
| payload\_fragmentation\_bloat/1 | 147\.37422640000003 | 143\.3165104 | false | ABSTAIN/3 | false |
| payload\_fragmentation\_bloat/3 | 156\.3012016 | 143\.3165104 | true | ABSTAIN/3 | false |
| payload\_fragmentation\_bloat/15 | 209\.86305280000002 | 143\.3165104 | true | ABSTAIN/3 | false |
| tx\_power\_lock/0 | 141\.6266464 | 141\.6266464 | false | ABSTAIN/3 | false |
| tx\_power\_lock/1 | 141\.96461920000002 | 141\.6266464 | false | ABSTAIN/3 | false |
| tx\_power\_lock/5 | 143\.3165104 | 141\.6266464 | false | ABSTAIN/3 | false |

Gate blocking means would block a candidate; these offline simulations already ran and no physical firmware execution occurred.
All assumptions/source snapshots/lineage and exact gate/model outputs are archived per case. No calibrated intervals or physical causal attributions.
