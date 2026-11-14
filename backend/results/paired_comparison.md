# Improved model against the baseline, paired by run

Each evaluation seed gives both models the same made-up learners, so the difference is taken within a seed (improved minus baseline) and then averaged. The 95% interval uses the t distribution over the seeds. "Better" or "worse" means the interval excludes zero; otherwise the difference is within the noise of 5 runs. Source: `results/model_comparison.json`.

## Sprint 2 simulator

| Measure | Mean difference | Median difference | 95% interval | Improved better in | Verdict |
|---|---|---|---|---|---|
| Gap F1 (higher is better) | +0.9 pts | +0.9 pts | +0.5 pts to +1.4 pts | 5 of 5 runs | better |
| True blocker (higher is better) | +8.9 pts | +9.2 pts | +7.0 pts to +10.8 pts | 5 of 5 runs | better |
| Hidden blocker found (higher is better) | +7.5 pts | +7.6 pts | +4.9 pts to +10.0 pts | 5 of 5 runs | better |
| Recommended a known concept (lower is better) | -15.9 pts | -17.6 pts | -19.9 pts to -11.8 pts | 5 of 5 runs | better |
| Missed gaps (lower is better) | +0.9 pts | +1.5 pts | -1.6 pts to +3.3 pts | 1 of 5 runs | no clear difference |
| False alarms (lower is better) | -7.7 pts | -8.0 pts | -12.2 pts to -3.2 pts | 5 of 5 runs | better |
| Next-answer AUC (higher is better) | +0.006 | +0.007 | +0.003 to +0.010 | 5 of 5 runs | better |

## Barabari's quiz format

| Measure | Mean difference | Median difference | 95% interval | Improved better in | Verdict |
|---|---|---|---|---|---|
| Gap F1 (higher is better) | +2.2 pts | +2.2 pts | +1.6 pts to +2.8 pts | 5 of 5 runs | better |
| True blocker (higher is better) | +8.3 pts | +8.2 pts | +4.6 pts to +12.0 pts | 5 of 5 runs | better |
| Hidden blocker found (higher is better) | +9.3 pts | +9.9 pts | +4.5 pts to +14.1 pts | 5 of 5 runs | better |
| Recommended a known concept (lower is better) | -15.2 pts | -16.0 pts | -22.8 pts to -7.6 pts | 5 of 5 runs | better |
| Missed gaps (lower is better) | -0.1 pts | +0.6 pts | -1.5 pts to +1.3 pts | 2 of 5 runs | no clear difference |
| False alarms (lower is better) | -7.5 pts | -7.9 pts | -10.8 pts to -4.3 pts | 5 of 5 runs | better |
| Next-answer AUC (higher is better) | +0.029 | +0.030 | +0.022 to +0.036 | 5 of 5 runs | better |

## Summary

Of 14 measures, the improved model is clearly better on 12, clearly worse on 0, and not clearly different on 2.

Read the run counts with the interval: a measure can be within the noise overall and still be worse in most runs, as missed gaps on the Sprint 2 simulator are (one baseline run at 6.4% widens the interval; the median difference is the better guide there).
