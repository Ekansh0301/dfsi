# Failure analysis: multi-concept questions bias the fitted parameters

Made-up learners (seed 0, 2,100 training learners). The simulator's true slip is 0.04 to 0.14 (mean 0.09). The fitting limit for slip is 0.30.

| Concept | Slip, all tagged answers | Slip, single-concept questions only |
|---|---|---|
| safety | 0.30 | 0.11 |
| quantities | 0.30 | 0.07 |
| ohm | 0.29 | 0.19 |
| symbols | 0.22 | 0.10 |
| wiring | 0.30 | 0.11 |
| multimeter | 0.10 | 0.10 |
| series_parallel | 0.30 | 0.16 |
| diagrams | 0.22 | 0.14 |
| earthing | 0.16 | 0.16 |
| fault | 0.30 | 0.30 |

Mean slip: 0.25 using all tagged answers, 0.14 using single-concept questions only. Concepts at the 0.30 limit: 5 of 10 against 1 of 10.

Reading: when a question needs several concepts and is answered wrongly, plain BKT blames every tagged concept. That makes the model think learners often get a mastered concept wrong, so slip is overestimated.
