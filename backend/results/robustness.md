# Robustness of the engine

Made-up learners with Barabari's quiz format: 3 runs of 3000 (seeds 0 to 2), 70% train, 30% test. Mean ± standard deviation across runs.

## 1. Fitted parameters across the 5 evaluation seeds

Standard deviation across seeds, averaged over the 10 concepts, and the share of fitted values on a fitting bound.

| Simulator | Fit | p_init | p_learn | p_slip | p_guess | On a bound |
|---|---|---|---|---|---|---|
| Sprint 2 | every tag (baseline) | 0.020 | 0.025 | 0.026 | 0.018 | 16% |
| Sprint 2 | first tag (improved) | 0.012 | 0.011 | 0.022 | 0.009 | 4% |
| Barabari | every tag (baseline) | 0.018 | 0.019 | 0.023 | 0.024 | 21% |
| Barabari | first tag (improved) | 0.012 | 0.015 | 0.029 | 0.024 | 6% |

## 2. Wrong concept tags and a wrong concept graph

Mis-tagged items swap their main tag for a random other concept, in the data the model is fitted and traced on. Missing links: symbols before diagrams, diagrams before fault, ohm before series_parallel. Wrong links added: multimeter before symbols, ohm before earthing, ohm before diagrams. The hidden truth always uses the real graph.

| Condition | Model | True blocker | Hidden blocker found | Missed gaps | False alarms |
|---|---|---|---|---|---|
| Correct tags and graph | baseline | 44.7% ± 1.3 | 47.1% ± 1.9 | 6.3% ± 0.4 | 38.0% ± 2.7 |
| Correct tags and graph | improved | 54.1% ± 1.3 | 56.8% ± 2.5 | 7.0% ± 0.3 | 29.7% ± 0.6 |
| 10% of items mis-tagged | baseline | 38.5% ± 1.9 | 42.4% ± 2.8 | 5.2% ± 0.3 | 42.7% ± 2.6 |
| 10% of items mis-tagged | improved | 48.9% ± 0.9 | 53.4% ± 1.5 | 8.1% ± 0.9 | 31.8% ± 1.6 |
| 25% of items mis-tagged | baseline | 32.8% ± 1.2 | 35.1% ± 3.0 | 4.1% ± 1.3 | 52.8% ± 3.6 |
| 25% of items mis-tagged | improved | 42.1% ± 2.7 | 44.5% ± 2.9 | 8.5% ± 1.3 | 36.0% ± 3.0 |
| 3 prerequisite links missing | baseline | 40.7% ± 1.4 | 36.7% ± 1.9 | 6.3% ± 0.4 | 38.0% ± 2.7 |
| 3 prerequisite links missing | improved | 47.7% ± 0.8 | 43.2% ± 2.4 | 7.2% ± 0.2 | 29.3% ± 0.6 |
| 3 wrong prerequisite links | baseline | 42.0% ± 1.3 | 44.9% ± 2.3 | 6.3% ± 0.4 | 38.0% ± 2.7 |
| 3 wrong prerequisite links | improved | 52.0% ± 1.3 | 55.0% ± 1.8 | 6.9% ± 0.3 | 29.8% ± 0.5 |

## 3. Change from the clean condition (improved model)

| Condition | True blocker | Hidden blocker found | Missed gaps | False alarms |
|---|---|---|---|---|
| 10% of items mis-tagged | -5.2 points | -3.4 points | +1.1 points | +2.1 points |
| 25% of items mis-tagged | -12.0 points | -12.2 points | +1.6 points | +6.2 points |
| 3 prerequisite links missing | -6.4 points | -13.5 points | +0.3 points | -0.4 points |
| 3 wrong prerequisite links | -2.1 points | -1.7 points | -0.0 points | +0.0 points |
