# Failure analysis: hidden-prerequisite cases

Made-up learners (seed 0, 900 test learners): what happened at each assessment point where the real blocker is a prerequisite of the gap the quick check showed. The first column is the Sprint 2 analysis (hand-set parameters); the others use fitted parameters.

| What happened | Sprint 2 sim, hand-set (Sprint 2) | Sprint 2 sim, baseline | Sprint 2 sim, improved | Barabari sim, baseline | Barabari sim, improved |
|---|---|---|---|---|---|
| Cases | 2,342 | 2,342 | 2,342 | 1,861 | 1,861 |
| Found the true blocker | 60.5% | 66.6% | 72.2% | 45.7% | 59.8% |
| Recommended a concept the learner actually knew | 31.6% | 20.2% | 13.0% | 41.8% | 18.4% |
| Blocker was asked about but looked fine | 4.1% | 8.5% | 9.8% | 4.2% | 14.9% |
| Recommended a real gap, but the real blocker was further upstream | 2.5% | 2.9% | 4.0% | 3.3% | 4.4% |
| Blocker was never asked about | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| Engine saw no gap at all | 1.3% | 1.9% | 0.9% | 4.9% | 2.5% |

Reading: with fitted parameters the improved model cuts lessons on a concept the learner already knew (20.2% to 13.0% on the Sprint 2 simulator, 41.8% to 18.4% on the Barabari one), because a wrong answer on a two-concept question no longer blames both. The cost is more blockers that looked fine (8.5% to 9.8%, and 4.2% to 14.9%): a prerequisite's second tags no longer count as evidence about it, so it is judged on fewer answers. Asking about each prerequisite directly would close that gap.
