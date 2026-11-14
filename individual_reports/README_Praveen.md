# Individual report: Praveen

**Course:** DFSI 2026, Problem 3B (identifying what a learner needs next) | **Team:** Impact Theory | **Project:** Circuit Coach, Hackathon 2

## My contribution: improving the model over the baseline

The baseline keeps a score for each concept using Bayesian Knowledge Tracing and walks back through prerequisites to find the real cause of a gap. My part was improving it and proving the improvement.

**Four changes**

1. **First-tag credit.** A question tagged with several concepts updates only its main one, so one wrong answer no longer blames two concepts.
2. **Question difficulty.** Slip and guess rates shift for each question by how hard it is.
3. **Prerequisite-aware learning.** Learning is assumed slower (down to half) while a prerequisite looks weak.
4. **More evidence before a lesson.** A lesson needs two answers on the concept, unless the score is already very low after one.

The settings were chosen on a separate tuning seed (100) and tested on seeds 0 to 4, so the results are not tuned to the test.

**What the evidence shows** (5 runs of 3,000 simulated learners per simulator)

- The hidden root cause is found more often: 49% to 58% in Barabari's quiz format, 62% to 69% on the older simulator.
- Fewer lessons on a concept the learner already knew: 42% to 27%, and 34% to 18%.
- Fewer false alarms: 38% to 31%, and 32% to 24%.
- Compared run by run, with 95% intervals, it is clearly better on 12 of 14 measures.
- On real student answers (EdNet) the next-answer AUC rises from 0.627 to 0.729.
- With the same prerequisite walk, knowledge tracing finds 12 to 24 points more real blockers than plain accuracy.
- Based on this, the improved model is now the service default.

**The cost, stated plainly.** Missed gaps do not improve (2.6% against 3.5% on the older simulator, within the noise of 5 runs, though worse in 4 of 5 runs), and they grow when concept tags are wrong.

I also kept the handoff notes, plan and test counts in step with the code.

## Hackathon experience

The hardest part was resisting a good-looking number. An early summary said the improved model beat the baseline on "13 of 14 measures", but comparing the two inside each run showed the real picture: 12 clearly better and 2 within the noise. Rewriting the claim, and then running the real-data comparison that had been put off, made the result more convincing, not less.

## Key learnings

- **Change one thing at a time.** Adding each change on its own showed that first-tag credit gave the largest gain and that difficulty mainly helps predicting answers.
- **Compare like with like.** Both models see the same learners in each run, so the difference is not mixed up with luck. A paired comparison with intervals is a stronger claim than two averages.
- **Choose settings and test on different data.** Otherwise the improvement may just be fitting.
- **Report the downside.** A model that finds more real blockers but misses a few more gaps is a trade-off, and the decision to accept it should be written down.
- **Simulation and real data answer different questions.** Simulated learners tell us whether the diagnosis is right; EdNet only tells us whether predictions are good.

## Where to look

`backend/circuit_coach/engine.py` (`IMPROVED`) | `backend/scripts/compare_models.py`, `paired_comparison.py`, `accuracy_baseline.py` | `backend/results/paired_comparison.md`, `accuracy_baseline.md` | `backend/docs/evaluation.md`
