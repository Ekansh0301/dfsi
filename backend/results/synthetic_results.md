# Baseline results on made-up learners

5 runs, 3000 learners each (70% train, 30% test). Mean ± standard deviation across runs.

## 1. Predicting the next answer

| Method | AUC | Accuracy | Log loss | RMSE |
|---|---|---|---|---|
| Global average | 0.500 ± 0.000 | 0.652 ± 0.010 | 0.648 ± 0.006 | 0.477 ± 0.003 |
| Per-question accuracy | 0.603 ± 0.004 | 0.665 ± 0.010 | 0.628 ± 0.006 | 0.468 ± 0.003 |
| Learner's running accuracy | 0.613 ± 0.003 | 0.681 ± 0.009 | 0.631 ± 0.008 | 0.467 ± 0.004 |
| BKT (hand-set parameters) | 0.649 ± 0.002 | 0.713 ± 0.006 | 0.598 ± 0.005 | 0.452 ± 0.003 |
| BKT (fitted) | 0.688 ± 0.002 | 0.701 ± 0.008 | 0.595 ± 0.008 | 0.450 ± 0.004 |

## 2a. Finding the gap and the lesson (fitted parameters)

| Method | Gap F1 | Recommendation is a true blocker | Hidden-prerequisite cases: blocker found | ...stopped at the assessed concept | Missed gaps | False alarms |
|---|---|---|---|---|---|---|
| Study what you got wrong (status quo) | 87.0% ± 0.6 | 31.2% ± 1.5 | 7.4% ± 0.5 | 96.2% ± 0.3 | 1.0% ± 0.1 | 50.0% ± 2.0 |
| BKT, recommend the assessed concept | 89.1% ± 0.6 | 28.5% ± 2.7 | 5.0% ± 0.6 | 96.6% ± 0.6 | 2.6% ± 1.9 | 31.9% ± 3.1 |
| BKT + prerequisite walk | 89.1% ± 0.6 | 59.2% ± 1.3 | 61.9% ± 2.8 | 5.9% ± 1.1 | 2.6% ± 1.9 | 31.9% ± 3.1 |

Mastery estimates vs hidden truth (fitted parameters): AUC 0.851 ± 0.007, Brier score 0.126 ± 0.004, mean absolute error 0.280 ± 0.006.

## 2b. Finding the gap and the lesson (hand-set parameters)

| Method | Gap F1 | Recommendation is a true blocker | Hidden-prerequisite cases: blocker found | ...stopped at the assessed concept | Missed gaps | False alarms |
|---|---|---|---|---|---|---|
| Study what you got wrong (status quo) | 87.0% ± 0.6 | 31.2% ± 1.5 | 7.4% ± 0.5 | 96.2% ± 0.3 | 1.0% ± 0.1 | 50.0% ± 2.0 |
| BKT, recommend the assessed concept | 88.5% ± 0.6 | 30.5% ± 1.6 | 7.1% ± 0.4 | 96.4% ± 0.5 | 2.1% ± 0.3 | 31.6% ± 2.0 |
| BKT + prerequisite walk | 88.5% ± 0.6 | 54.9% ± 2.1 | 55.7% ± 2.9 | 6.6% ± 0.8 | 2.1% ± 0.3 | 31.6% ± 2.0 |

Mastery estimates vs hidden truth (hand-set parameters): AUC 0.843 ± 0.005, Brier score 0.124 ± 0.004, mean absolute error 0.267 ± 0.004.

## 3. Fitted parameters (seed 0)

| Concept | p_init | p_learn | p_slip | p_guess |
|---|---|---|---|---|
| safety | 0.68 | 0.13 | 0.30 | 0.14 |
| quantities | 0.25 | 0.10 | 0.30 | 0.22 |
| ohm | 0.11 | 0.13 | 0.29 | 0.14 |
| symbols | 0.10 | 0.20 | 0.22 | 0.13 |
| wiring | 0.15 | 0.11 | 0.30 | 0.16 |
| multimeter | 0.12 | 0.15 | 0.10 | 0.15 |
| series_parallel | 0.06 | 0.17 | 0.30 | 0.12 |
| diagrams | 0.05 | 0.09 | 0.22 | 0.15 |
| earthing | 0.02 | 0.23 | 0.16 | 0.11 |
| fault | 0.03 | 0.18 | 0.30 | 0.09 |
