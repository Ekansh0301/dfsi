# Evaluation and baseline comparison

Code: `circuit_coach/prediction.py` (next-answer baselines), `circuit_coach/diagnosis_eval.py` (gap and lesson metrics), `scripts/run_synthetic.py`, `scripts/run_ednet.py`, `scripts/ablation_multitag.py`, `scripts/failure_analysis.py`. Reports: `results/`. Tests: `tests/test_evaluation.py`.

## What is compared

Every model sees a learner's answers one at a time and, before each answer, outputs the probability that it will be right.

| Model | Uses |
|---|---|
| Global average | Nothing: the overall correct rate in the training data |
| Per-question accuracy | The question's own correct rate in the training data |
| Learner's running accuracy | The learner's accuracy so far on the concepts tagged on the question |
| BKT (hand-set parameters) | Per-concept Bayesian Knowledge Tracing with the hand-set values |
| BKT (fitted) | The same, with parameters fitted by EM on the training learners |

The first 3 answers of each learner are not scored. Learners are split 70:30 by learner into train and test; parameters and per-question rates come from the training learners only.

## Metrics

| Metric | Used for | Meaning |
|---|---|---|
| AUC | next answer, mastery estimates | Chance that a right answer is scored above a wrong one (0.5 is chance) |
| Accuracy | next answer | Share of answers on the right side of 0.5 |
| Log loss | next answer | Penalises confident wrong probabilities (lower is better) |
| RMSE | next answer | Root mean square of (probability minus answer) (lower is better) |
| Gap F1 | diagnosis | Does the engine flag a quick check as having a gap exactly when the learner truly lacks an assessed concept |
| Recommendation is a true blocker | diagnosis | The recommended concept is an unmastered concept whose prerequisites are mastered |
| Hidden-prerequisite cases: blocker found | diagnosis | Among true gaps with an unmastered prerequisite, the recommendation is the real blocker |
| ...stopped at the assessed concept | diagnosis | Same cases, but the recommendation stayed on the concept that was assessed |
| Missed gaps, false alarms | diagnosis | Real gaps with no recommendation; recommendations when nothing is truly lacking |
| AUC, Brier score, mean absolute error | mastery estimates | Estimated P(mastered) against the hidden true state |

Diagnosis metrics need hidden truth, so they are computed on made-up learners only. Three methods are compared: "study what you got wrong" (recommend a concept the learner answered wrongly), BKT recommending the assessed concept, and BKT plus the prerequisite walk.

## Reproduce

```bash
python scripts/run_synthetic.py --learners 3000 --seeds 5     # about 2 minutes
python scripts/ablation_multitag.py
python scripts/failure_analysis.py
python scripts/run_ednet.py --users 40000                      # needs the EdNet files, see README
```

`run_synthetic.py` writes `results/synthetic_results.md` and `.json` (mean and standard deviation over 5 seeds) and the fitted parameters used by the service. Everything is seeded: seed `k` always generates the same learners, split and fits. Run the scripts from `backend/` with the package installed (`pip install -e .`) or with `PYTHONPATH=.`.

Reruns give the same tables. On another machine or numpy build, floating point values in the JSON files can differ in the 16th digit (the committed report was regenerated on Windows with numpy 2.2.2 and every figure in the Markdown tables matched). `tests/test_evaluation.py` checks that the same seed gives the same report, that every baseline is scored on every metric, and that the committed report contains all required metrics.

## Results

Made-up learners, 5 runs of 3,000 learners (mean over runs; full tables with standard deviations in `results/synthetic_results.md`):

| Method | AUC | Accuracy | Log loss | RMSE |
|---|---|---|---|---|
| Global average | 0.500 | 0.652 | 0.648 | 0.477 |
| Per-question accuracy | 0.603 | 0.665 | 0.628 | 0.468 |
| Learner's running accuracy | 0.613 | 0.681 | 0.631 | 0.467 |
| BKT (hand-set parameters) | 0.649 | 0.713 | 0.598 | 0.452 |
| BKT (fitted) | 0.688 | 0.701 | 0.595 | 0.450 |

| Diagnosis (fitted parameters) | Gap F1 | True blocker | Hidden-prerequisite blocker found | False alarms |
|---|---|---|---|---|
| Study what you got wrong | 87.0% | 31.2% | 7.4% | 50.0% |
| BKT, assessed concept | 89.1% | 28.5% | 5.0% | 31.9% |
| BKT + prerequisite walk | 89.1% | 59.2% | 61.9% | 31.9% |

Real data (EdNet KT1, 14,460 students, 357,756 test answers): per-question accuracy AUC 0.721, fitted BKT 0.627 (first tag only 0.641), learner running accuracy 0.598, global average 0.500 (`results/ednet_results.md`). On real data BKT does not beat per-question accuracy because it ignores question difficulty.

## Limits

- Made-up learners follow the simulator's assumptions (`docs/synthetic_data.md`); results there say how the engine behaves when those assumptions hold.
- EdNet has no prerequisite graph and no hidden truth, so it only checks next-answer prediction, on a Korean English-test tutor.
- Nothing here shows that learners learn more. That needs real learners.
- Failure analysis and the multi-concept ablation (`results/failure_analysis.md`, `results/ablation_multitag.md`) list where the engine goes wrong; they are the starting point for the next model.
