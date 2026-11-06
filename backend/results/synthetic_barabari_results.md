# Baseline results on made-up learners with Barabari's quiz format

5 runs, 3000 learners each (70% train, 30% test). Mean ± standard deviation across runs.

## 1. Predicting the next answer

| Method | AUC | Accuracy | Log loss | RMSE |
|---|---|---|---|---|
| Global average | 0.500 ± 0.000 | 0.578 ± 0.006 | 0.681 ± 0.002 | 0.494 ± 0.001 |
| Per-question accuracy | 0.628 ± 0.005 | 0.611 ± 0.006 | 0.655 ± 0.004 | 0.481 ± 0.002 |
| Learner's running accuracy | 0.575 ± 0.003 | 0.609 ± 0.005 | 0.694 ± 0.004 | 0.497 ± 0.002 |
| BKT (hand-set parameters) | 0.666 ± 0.004 | 0.642 ± 0.009 | 0.636 ± 0.005 | 0.472 ± 0.003 |
| BKT (fitted) | 0.672 ± 0.005 | 0.633 ± 0.007 | 0.639 ± 0.003 | 0.473 ± 0.002 |

## 2a. Finding the gap and the lesson (fitted parameters)

| Method | Gap F1 | Recommendation is a true blocker | Hidden-prerequisite cases: blocker found | ...stopped at the assessed concept | Missed gaps | False alarms |
|---|---|---|---|---|---|---|
| Study what you got wrong (status quo) | 77.9% ± 0.3 | 32.8% ± 1.4 | 7.5% ± 0.2 | 92.8% ± 0.7 | 1.9% ± 0.2 | 64.4% ± 1.7 |
| BKT, recommend the assessed concept | 79.7% ± 0.3 | 29.4% ± 1.5 | 4.8% ± 0.5 | 90.5% ± 1.3 | 6.4% ± 0.4 | 38.2% ± 2.3 |
| BKT + prerequisite walk | 79.7% ± 0.3 | 47.2% ± 3.3 | 49.0% ± 2.8 | 7.7% ± 2.9 | 6.4% ± 0.4 | 38.2% ± 2.3 |

Mastery estimates vs hidden truth (fitted parameters): AUC 0.789 ± 0.003, Brier score 0.182 ± 0.001, mean absolute error 0.372 ± 0.001.

## 2b. Finding the gap and the lesson (hand-set parameters)

| Method | Gap F1 | Recommendation is a true blocker | Hidden-prerequisite cases: blocker found | ...stopped at the assessed concept | Missed gaps | False alarms |
|---|---|---|---|---|---|---|
| Study what you got wrong (status quo) | 77.9% ± 0.3 | 32.8% ± 1.4 | 7.5% ± 0.2 | 92.8% ± 0.7 | 1.9% ± 0.2 | 64.4% ± 1.7 |
| BKT, recommend the assessed concept | 81.0% ± 0.4 | 31.1% ± 1.3 | 8.5% ± 0.7 | 91.2% ± 0.9 | 7.8% ± 0.2 | 28.7% ± 0.7 |
| BKT + prerequisite walk | 81.0% ± 0.4 | 46.0% ± 1.9 | 47.5% ± 2.8 | 10.7% ± 0.4 | 7.8% ± 0.2 | 28.7% ± 0.7 |

Mastery estimates vs hidden truth (hand-set parameters): AUC 0.827 ± 0.006, Brier score 0.176 ± 0.003, mean absolute error 0.363 ± 0.004.

## 3. Fitted parameters (seed 0)

| Concept | p_init | p_learn | p_slip | p_guess |
|---|---|---|---|---|
| safety | 0.60 | 0.01 | 0.30 | 0.35 |
| quantities | 0.16 | 0.09 | 0.30 | 0.30 |
| ohm | 0.06 | 0.13 | 0.30 | 0.28 |
| symbols | 0.05 | 0.18 | 0.15 | 0.26 |
| wiring | 0.06 | 0.10 | 0.30 | 0.26 |
| multimeter | 0.12 | 0.13 | 0.30 | 0.20 |
| series_parallel | 0.05 | 0.13 | 0.30 | 0.24 |
| diagrams | 0.04 | 0.07 | 0.30 | 0.22 |
| earthing | 0.06 | 0.20 | 0.26 | 0.19 |
| fault | 0.01 | 0.15 | 0.30 | 0.19 |
