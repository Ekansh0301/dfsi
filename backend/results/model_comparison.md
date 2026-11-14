# Sprint 3 model against the Sprint 2 baseline

5 runs of 3000 made-up learners per simulator (70% train, 30% test), evaluation seeds 0 to 4. Mean ± standard deviation across runs. The improved model's settings were chosen on tuning seed 100.

Improved model: first-tag credit, question difficulty, prerequisite-aware learning (factor 0.5), and a lesson only after 2 answers on the concept unless its mastery is below 0.4.

## Sprint 2 simulator

### Predicting the next answer

| Model | AUC | Accuracy | Log loss | RMSE |
|---|---|---|---|---|
| Baseline: BKT, fitted | 0.688 ± 0.002 | 0.701 ± 0.008 | 0.595 ± 0.008 | 0.450 ± 0.004 |
| + first-tag credit | 0.680 ± 0.005 | 0.715 ± 0.005 | 0.588 ± 0.005 | 0.446 ± 0.002 |
| + question difficulty | 0.684 ± 0.004 | 0.716 ± 0.005 | 0.586 ± 0.005 | 0.446 ± 0.003 |
| Improved: + prerequisite-aware learning | 0.694 ± 0.002 | 0.718 ± 0.005 | 0.584 ± 0.006 | 0.444 ± 0.003 |
| Reference: per-question accuracy | 0.603 ± 0.004 | 0.665 ± 0.010 | 0.628 ± 0.006 | 0.468 ± 0.003 |

Mean fitted slip: 0.264 ± 0.009 with every tag, 0.155 ± 0.003 with first-tag credit (true slip in the simulator 0.04 to 0.14, mean about 0.09).

### Finding the gap and the lesson

| Model | Gap F1 | True blocker | Hidden blocker found | Recommended a known concept | Missed gaps | False alarms |
|---|---|---|---|---|---|---|
| Baseline: BKT + prerequisite walk | 89.1% ± 0.6 | 59.2% ± 1.3 | 61.9% ± 2.8 | 33.9% ± 3.8 | 2.6% ± 1.9 | 31.9% ± 3.1 |
| + first-tag credit | 89.1% ± 0.3 | 67.6% ± 1.4 | 68.2% ± 1.7 | 17.3% ± 1.4 | 3.8% ± 0.9 | 26.6% ± 2.2 |
| + question difficulty | 89.1% ± 0.3 | 67.5% ± 1.5 | 67.9% ± 1.6 | 17.3% ± 1.4 | 3.8% ± 0.8 | 26.7% ± 2.0 |
| + prerequisite-aware learning | 90.0% ± 0.4 | 68.5% ± 1.6 | 69.4% ± 1.9 | 18.0% ± 1.4 | 3.0% ± 0.3 | 28.2% ± 1.1 |
| Improved: + more evidence before a lesson | 90.0% ± 0.4 | 68.1% ± 1.5 | 69.3% ± 1.8 | 18.0% ± 1.3 | 3.5% ± 0.5 | 24.2% ± 1.5 |

## Barabari's quiz format

### Predicting the next answer

| Model | AUC | Accuracy | Log loss | RMSE |
|---|---|---|---|---|
| Baseline: BKT, fitted | 0.672 ± 0.005 | 0.633 ± 0.007 | 0.639 ± 0.003 | 0.473 ± 0.002 |
| + first-tag credit | 0.684 ± 0.005 | 0.647 ± 0.010 | 0.628 ± 0.005 | 0.468 ± 0.003 |
| + question difficulty | 0.700 ± 0.007 | 0.654 ± 0.010 | 0.618 ± 0.006 | 0.463 ± 0.003 |
| Improved: + prerequisite-aware learning | 0.701 ± 0.007 | 0.653 ± 0.010 | 0.617 ± 0.006 | 0.463 ± 0.003 |
| Reference: per-question accuracy | 0.628 ± 0.005 | 0.611 ± 0.006 | 0.655 ± 0.004 | 0.481 ± 0.002 |

Mean fitted slip: 0.277 ± 0.008 with every tag, 0.193 ± 0.007 with first-tag credit (true slip in the simulator 0.04 to 0.14, mean about 0.09).

### Finding the gap and the lesson

| Model | Gap F1 | True blocker | Hidden blocker found | Recommended a known concept | Missed gaps | False alarms |
|---|---|---|---|---|---|---|
| Baseline: BKT + prerequisite walk | 79.7% ± 0.3 | 47.2% ± 3.3 | 49.0% ± 2.8 | 41.9% ± 6.7 | 6.4% ± 0.4 | 38.2% ± 2.3 |
| + first-tag credit | 78.4% ± 0.5 | 52.2% ± 1.7 | 53.1% ± 1.9 | 25.0% ± 1.8 | 10.6% ± 1.2 | 28.8% ± 1.0 |
| + question difficulty | 78.4% ± 0.4 | 52.2% ± 1.6 | 52.8% ± 2.4 | 24.2% ± 1.7 | 10.9% ± 1.0 | 28.1% ± 1.4 |
| + prerequisite-aware learning | 81.9% ± 0.5 | 55.5% ± 1.9 | 58.3% ± 2.9 | 26.7% ± 1.9 | 6.2% ± 0.8 | 32.0% ± 1.3 |
| Improved: + more evidence before a lesson | 81.9% ± 0.5 | 55.5% ± 2.0 | 58.3% ± 2.9 | 26.6% ± 2.0 | 6.3% ± 0.8 | 30.7% ± 1.3 |

## EdNet (real answers, no prerequisite graph)

| Model | AUC | Accuracy | Log loss | RMSE |
|---|---|---|---|---|
| Baseline: BKT, fitted (all tags) | 0.627 | 0.625 | 0.645 | 0.476 |
| Improved: first tag + question difficulty | 0.729 | 0.694 | 0.584 | 0.447 |
| Reference: per-question accuracy | 0.721 | 0.688 | 0.590 | 0.450 |

## Promotion check (made-up learners)

| Data | Measure | Baseline | Improved | Better |
|---|---|---|---|---|
| Sprint 2 simulator | Gap F1 | 89.1% | 90.0% | yes |
| Sprint 2 simulator | True blocker | 59.2% | 68.1% | yes |
| Sprint 2 simulator | Hidden blocker found | 61.9% | 69.3% | yes |
| Sprint 2 simulator | Recommended a known concept | 33.9% | 18.0% | yes |
| Sprint 2 simulator | Missed gaps | 2.6% | 3.5% | no |
| Sprint 2 simulator | False alarms | 31.9% | 24.2% | yes |
| Sprint 2 simulator | Next-answer AUC | 0.688 | 0.694 | yes |
| Barabari's quiz format | Gap F1 | 79.7% | 81.9% | yes |
| Barabari's quiz format | True blocker | 47.2% | 55.5% | yes |
| Barabari's quiz format | Hidden blocker found | 49.0% | 58.3% | yes |
| Barabari's quiz format | Recommended a known concept | 41.9% | 26.6% | yes |
| Barabari's quiz format | Missed gaps | 6.4% | 6.3% | yes |
| Barabari's quiz format | False alarms | 38.2% | 30.7% | yes |
| Barabari's quiz format | Next-answer AUC | 0.672 | 0.701 | yes |
