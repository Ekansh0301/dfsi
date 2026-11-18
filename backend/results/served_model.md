# The improved model as the service serves it

Same learners and seeds as `model_comparison.md` (5 runs of 3,000 made-up learners per simulator). The service ships an empty per-question difficulty table until it has answers for its own questions, so every question counts as average. Differences are within each run, with 95% intervals over the runs (`paired_comparison.py`).

## Sprint 2 simulator

### As served against the baseline

| Measure | Mean difference | Median difference | 95% interval | Better in | Verdict |
|---|---|---|---|---|---|
| Gap F1 (higher is better) | +0.9 pts | +0.9 pts | +0.4 pts to +1.4 pts | 5 of 5 runs | better |
| True blocker (higher is better) | +8.9 pts | +9.2 pts | +7.1 pts to +10.7 pts | 5 of 5 runs | better |
| Hidden blocker found (higher is better) | +7.5 pts | +7.6 pts | +4.9 pts to +10.2 pts | 5 of 5 runs | better |
| Recommended a known concept (lower is better) | -15.8 pts | -17.5 pts | -19.8 pts to -11.7 pts | 5 of 5 runs | better |
| Missed gaps (lower is better) | +1.0 pts | +1.7 pts | -1.5 pts to +3.5 pts | 1 of 5 runs | no clear difference |
| False alarms (lower is better) | -7.5 pts | -8.2 pts | -12.0 pts to -3.0 pts | 5 of 5 runs | better |

### As served against the improved model with a difficulty table

| Measure | Mean difference | Median difference | 95% interval | Better in | Verdict |
|---|---|---|---|---|---|
| Gap F1 (higher is better) | -0.0 pts | -0.0 pts | -0.1 pts to +0.1 pts | 2 of 5 runs | no clear difference |
| True blocker (higher is better) | -0.0 pts | -0.0 pts | -0.3 pts to +0.3 pts | 1 of 5 runs | no clear difference |
| Hidden blocker found (higher is better) | +0.1 pts | +0.0 pts | -0.4 pts to +0.5 pts | 3 of 5 runs | no clear difference |
| Recommended a known concept (lower is better) | +0.1 pts | +0.1 pts | -0.0 pts to +0.3 pts | 0 of 5 runs | no clear difference |
| Missed gaps (lower is better) | +0.1 pts | +0.1 pts | +0.0 pts to +0.2 pts | 0 of 5 runs | worse |
| False alarms (lower is better) | +0.2 pts | -0.3 pts | -1.3 pts to +1.7 pts | 4 of 5 runs | no clear difference |

## Barabari's quiz format

### As served against the baseline

| Measure | Mean difference | Median difference | 95% interval | Better in | Verdict |
|---|---|---|---|---|---|
| Gap F1 (higher is better) | +2.0 pts | +2.0 pts | +1.5 pts to +2.6 pts | 5 of 5 runs | better |
| True blocker (higher is better) | +7.7 pts | +7.3 pts | +4.6 pts to +10.7 pts | 5 of 5 runs | better |
| Hidden blocker found (higher is better) | +9.0 pts | +9.7 pts | +5.1 pts to +12.9 pts | 5 of 5 runs | better |
| Recommended a known concept (lower is better) | -14.0 pts | -14.9 pts | -21.1 pts to -7.0 pts | 5 of 5 runs | better |
| Missed gaps (lower is better) | -0.1 pts | +0.6 pts | -1.5 pts to +1.3 pts | 2 of 5 runs | no clear difference |
| False alarms (lower is better) | -6.7 pts | -7.4 pts | -9.8 pts to -3.5 pts | 5 of 5 runs | better |

### As served against the improved model with a difficulty table

| Measure | Mean difference | Median difference | 95% interval | Better in | Verdict |
|---|---|---|---|---|---|
| Gap F1 (higher is better) | -0.2 pts | -0.1 pts | -0.3 pts to +0.0 pts | 0 of 5 runs | no clear difference |
| True blocker (higher is better) | -0.6 pts | -0.5 pts | -1.4 pts to +0.1 pts | 1 of 5 runs | no clear difference |
| Hidden blocker found (higher is better) | -0.3 pts | -0.2 pts | -1.2 pts to +0.7 pts | 2 of 5 runs | no clear difference |
| Recommended a known concept (lower is better) | +1.2 pts | +1.4 pts | +0.6 pts to +1.8 pts | 0 of 5 runs | worse |
| Missed gaps (lower is better) | -0.0 pts | -0.0 pts | -0.2 pts to +0.2 pts | 3 of 5 runs | no clear difference |
| False alarms (lower is better) | +0.8 pts | +0.8 pts | +0.2 pts to +1.4 pts | 0 of 5 runs | worse |

## Summary

Against the baseline, the improved model as served is clearly better on 10 of 12 diagnosis measures, clearly worse on 0, and not clearly different on 2.
