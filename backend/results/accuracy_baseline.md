# Knowledge tracing against plain accuracy, with the same prerequisite walk

5 runs of 3000 made-up learners per simulator, the same seeds and 70:30 split as `results/model_comparison.md` (scored on the 30% test learners). The accuracy engine estimates mastery as (right + 1) / (answers + 2) and otherwise uses the same 0.6 threshold, prerequisite walk and lesson choice (`circuit_coach/accuracy_engine.py`). BKT rows are copied from `results/model_comparison.json`. Mean over runs.

## Sprint 2 simulator

| Method | Gap F1 | True blocker | Hidden blocker found | Recommended a known concept | Missed gaps | False alarms |
|---|---|---|---|---|---|---|
| Study what you got wrong (status quo) | 87.0% | 31.2% | 7.4% | 4.8% | 1.0% | 50.0% |
| Accuracy + prerequisite walk | 88.4% | 44.0% | 43.4% | 52.1% | 2.4% | 27.7% |
| Accuracy + prerequisite walk, 2 answers before a lesson | 88.4% | 44.0% | 43.4% | 52.1% | 2.4% | 27.7% |
| BKT baseline + prerequisite walk | 89.1% | 59.2% | 61.9% | 33.9% | 2.6% | 31.9% |
| BKT improved model (2 answers before a lesson) | 90.0% | 68.1% | 69.3% | 18.0% | 3.5% | 24.2% |

Paired difference, BKT minus accuracy with the same evidence rule (mean and 95% interval over runs; positive is better for BKT on every row):

| Measure | BKT baseline vs accuracy | BKT improved vs accuracy (2 answers) |
|---|---|---|
| Gap F1 | +0.6 pts (+0.2 to +1.0) | +1.6 pts (+1.2 to +1.9) |
| True blocker | +15.2 pts (+13.3 to +17.1) | +24.1 pts (+21.6 to +26.7) |
| Hidden blocker found | +18.5 pts (+16.1 to +20.8) | +25.9 pts (+22.9 to +29.0) |
| Recommended a known concept | +18.1 pts (+15.2 to +21.0) | +34.0 pts (+31.6 to +36.4) |
| Missed gaps | -0.2 pts (-2.6 to +2.2) | -1.1 pts (-1.6 to -0.6) |
| False alarms | -4.2 pts (-9.9 to +1.4) | +3.5 pts (+1.7 to +5.3) |

## Barabari's quiz format

| Method | Gap F1 | True blocker | Hidden blocker found | Recommended a known concept | Missed gaps | False alarms |
|---|---|---|---|---|---|---|
| Study what you got wrong (status quo) | 77.9% | 32.8% | 7.5% | 8.7% | 1.9% | 64.4% |
| Accuracy + prerequisite walk | 79.8% | 34.7% | 35.2% | 59.7% | 3.6% | 42.8% |
| Accuracy + prerequisite walk, 2 answers before a lesson | 79.8% | 34.5% | 35.1% | 59.8% | 4.0% | 42.4% |
| BKT baseline + prerequisite walk | 79.7% | 47.2% | 49.0% | 41.9% | 6.4% | 38.2% |
| BKT improved model (2 answers before a lesson) | 81.9% | 55.5% | 58.3% | 26.6% | 6.3% | 30.7% |

Paired difference, BKT minus accuracy with the same evidence rule (mean and 95% interval over runs; positive is better for BKT on every row):

| Measure | BKT baseline vs accuracy | BKT improved vs accuracy (2 answers) |
|---|---|---|
| Gap F1 | -0.2 pts (-1.0 to +0.7) | +2.0 pts (+1.3 to +2.7) |
| True blocker | +12.4 pts (+10.0 to +14.9) | +20.9 pts (+19.4 to +22.5) |
| Hidden blocker found | +13.9 pts (+11.3 to +16.4) | +23.1 pts (+19.2 to +27.1) |
| Recommended a known concept | +17.8 pts (+11.4 to +24.2) | +33.1 pts (+31.8 to +34.4) |
| Missed gaps | -2.8 pts (-3.3 to -2.3) | -2.3 pts (-3.6 to -1.1) |
| False alarms | +4.5 pts (+1.7 to +7.4) | +11.7 pts (+8.8 to +14.5) |

## Reading

- With the same walk, BKT finds clearly more true blockers and hidden blockers than accuracy, and recommends far fewer concepts the learner already knew, on both simulators. Accuracy never forgets an early wrong answer, so it keeps sending learners back to concepts they have since learned.
- Accuracy misses slightly fewer gaps (it calls a gap after a single wrong answer), at the cost of more lessons on the wrong concept.
- So the gain over "study what you got wrong" comes from the walk and from BKT together: the walk on plain accuracy recovers part of it, BKT the rest.
