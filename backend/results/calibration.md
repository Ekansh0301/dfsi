# Calibration of the engine's numbers

Made-up learners with Barabari's quiz format, test learners of 3 runs of 3000, pooled. 10 bins of equal width; ECE is the answer-weighted mean gap between predicted and observed (0 is perfect). The table gives the mean and spread of ECE over the runs; the plot's legend gives the ECE of all runs pooled, so the figures differ slightly (for example 0.022 and 0.020 for the improved model's next-answer probabilities).

| Quantity | Baseline ECE | Improved ECE |
|---|---|---|
| Next answer | 0.034 ± 0.004 | 0.022 ± 0.002 |
| Mastery | 0.067 ± 0.005 | 0.068 ± 0.004 |

## Next answer: predicted chance of a right answer

| Bin | Answers (baseline) | Predicted | Observed | Answers (improved) | Predicted | Observed |
|---|---|---|---|---|---|---|
| 0.0 to 0.1 | 1,475 | 0.08 | 0.18 | 1,713 | 0.08 | 0.18 |
| 0.1 to 0.2 | 5,450 | 0.15 | 0.23 | 8,730 | 0.16 | 0.18 |
| 0.2 to 0.3 | 21,495 | 0.27 | 0.26 | 25,653 | 0.25 | 0.25 |
| 0.3 to 0.4 | 35,093 | 0.35 | 0.36 | 23,578 | 0.35 | 0.37 |
| 0.4 to 0.5 | 17,342 | 0.44 | 0.51 | 14,279 | 0.45 | 0.48 |
| 0.5 to 0.6 | 21,149 | 0.54 | 0.56 | 17,936 | 0.55 | 0.52 |
| 0.6 to 0.7 | 5,838 | 0.64 | 0.77 | 9,472 | 0.64 | 0.65 |
| 0.7 to 0.8 | 791 | 0.73 | 0.80 | 5,011 | 0.74 | 0.79 |
| 0.8 to 0.9 | 116 | 0.82 | 0.88 | 2,226 | 0.84 | 0.88 |
| 0.9 to 1.0 | 0 | |  | 151 | 0.91 | 0.95 |

## Mastery: estimated P(mastered) against the hidden truth

| Bin | Estimates (baseline) | Predicted | Observed | Estimates (improved) | Predicted | Observed |
|---|---|---|---|---|---|---|
| 0.0 to 0.1 | 521 | 0.09 | 0.10 | 1,140 | 0.07 | 0.07 |
| 0.1 to 0.2 | 3,133 | 0.16 | 0.14 | 3,514 | 0.15 | 0.11 |
| 0.2 to 0.3 | 3,415 | 0.25 | 0.20 | 3,239 | 0.25 | 0.19 |
| 0.3 to 0.4 | 3,393 | 0.35 | 0.26 | 2,752 | 0.35 | 0.25 |
| 0.4 to 0.5 | 3,060 | 0.45 | 0.35 | 2,568 | 0.45 | 0.32 |
| 0.5 to 0.6 | 2,718 | 0.55 | 0.45 | 2,620 | 0.55 | 0.46 |
| 0.6 to 0.7 | 2,333 | 0.65 | 0.56 | 2,176 | 0.65 | 0.55 |
| 0.7 to 0.8 | 1,783 | 0.75 | 0.68 | 1,828 | 0.75 | 0.73 |
| 0.8 to 0.9 | 1,449 | 0.86 | 0.89 | 1,398 | 0.85 | 0.89 |
| 0.9 to 1.0 | 1,342 | 0.94 | 0.99 | 1,912 | 0.96 | 0.99 |

Plot: `results/calibration.png` (points on the diagonal are perfectly calibrated).
