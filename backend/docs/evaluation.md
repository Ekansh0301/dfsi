# Evaluation and baseline comparison

Code: `circuit_coach/prediction.py` (next-answer baselines), `circuit_coach/diagnosis_eval.py` (gap and lesson metrics), `circuit_coach/accuracy_engine.py` (accuracy baseline), `scripts/run_synthetic.py`, `scripts/compare_models.py`, `scripts/paired_comparison.py`, `scripts/accuracy_baseline.py`, `scripts/run_ednet.py`, `scripts/ablation_multitag.py`, `scripts/failure_analysis.py`. Reports: `results/`. Tests: `tests/test_evaluation.py`.

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
python scripts/compare_models.py                               # both models on both simulators
python scripts/paired_comparison.py                            # seconds: reads model_comparison.json
python scripts/accuracy_baseline.py                            # under a minute
PYTHONPATH=scripts python scripts/served_model_check.py        # the model as the service runs it, about 15 minutes
python scripts/run_ednet.py --users 40000                      # needs the EdNet files, see README
```

`run_synthetic.py` writes `results/synthetic_results.md` and `.json` (mean and standard deviation over 5 seeds) and the fitted parameters to `results/fitted_params_sprint2.json`. The parameters the service ships with (`circuit_coach/fitted_params.json`, the frozen model) change only with `--write-service-params`, and `tests/test_shipped_params.py` fails if they drift. Everything is seeded: seed `k` always generates the same learners, split and fits. Run the scripts from `backend/` with the package installed (`pip install -e .`) or with `PYTHONPATH=.`.

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

## Sprint 3: improved model against the baseline

`scripts/compare_models.py` adds the model changes one at a time on both simulators (5 evaluation seeds of 3,000 learners each; the settings were chosen on a separate tuning seed, 100). Full tables: `results/model_comparison.md`.

| Change | Plan | What it does |
|---|---|---|
| First-tag credit | S3-2 | A multi-concept question updates only its first, main concept |
| Question difficulty | S3-3 | Slip and guess shift per question by its difficulty, estimated from training answers |
| Prerequisite-aware learning | S3-5 | Learning runs at 0.5 to 1 times the normal rate, lower while observed prerequisites look weak |
| More evidence before a lesson | S3-6 | A lesson needs 2 answers on the concept, unless its mastery is below 0.4 after one |

| Measure | Sprint 2 simulator: baseline | improved | Barabari simulator: baseline | improved |
|---|---|---|---|---|
| Next-answer AUC | 0.688 | 0.694 | 0.672 | 0.701 |
| Mean fitted slip (true about 0.09) | 0.264 | 0.155 | 0.277 | 0.193 |
| Gap F1 | 89.1% | 90.0% | 79.7% | 81.9% |
| Recommendation is a true blocker | 59.2% | 68.1% | 47.2% | 55.5% |
| Hidden-prerequisite blocker found | 61.9% | 69.3% | 49.0% | 58.3% |
| Recommended a concept the learner knew | 33.9% | 18.0% | 41.9% | 26.6% |
| Missed gaps | 2.6% | 3.5% | 6.4% | 6.3% |
| False alarms | 31.9% | 24.2% | 38.2% | 30.7% |

What each change did:

- **First-tag credit** brought the biggest gain: fitted slip fell from 0.26 to 0.16 and the share of lessons on a concept the learner already knew halved (33.9% to 17.3% on the Sprint 2 simulator). On its own it misses more gaps on the Barabari simulator (6.4% to 10.6%), because second tags no longer count as evidence.
- **Question difficulty** raised next-answer AUC on the Barabari simulator (0.684 to 0.700), where questions differ in difficulty, and changed diagnosis little.
- **Prerequisite-aware learning** found more hidden blockers and won back the missed gaps (10.9% to 6.2% on the Barabari simulator), at the cost of more false alarms.
- **More evidence before a lesson** cut those false alarms again (32.0% to 30.7%; 28.2% to 24.2% on the Sprint 2 simulator).

### Promotion decision (S3-7)

**Decision (Hackathon 2): the improved model is the service default.** The baseline stays selectable (`?model=baseline`, `CIRCUIT_COACH_MODEL=baseline`).

Why:

- **Made-up learners.** Paired by run (both models see the same learners in each seed; `results/paired_comparison.md`), the improved model is clearly better on 12 of 14 measures and not clearly different on the other 2 (missed gaps on both simulators).
- **EdNet (real answers).** The promotion rule asks the improved model to narrow the EdNet gap to per-question accuracy. It does more than that: next-answer AUC 0.729 against 0.627 for the baseline and 0.721 for per-question accuracy (40,000 sampled students; first-tag credit and question difficulty only, since EdNet has no prerequisite graph). Table in `results/model_comparison.md`.
- **The cost, accepted.** Missed gaps on the Sprint 2 simulator: the averages are 2.6% (baseline) and 3.5%, and the 95% interval of the paired difference (-1.6 to +3.3 points) includes zero, but the improved model misses more in 4 of the 5 runs (median +1.5 points). The baseline's average comes from one run at 6.4%; in the other four it misses 1.3% to 2.1%. The plan's target was no more than the baseline. Against this the improved model finds about 9 points more true blockers, sends about 15 points fewer learners to a lesson they do not need, and predicts real answers far better. Missed gaps also grow under heavy mis-tagging (`results/robustness.md`), which is one more reason a trainer checks the tags.

What the default means in practice: a request without `?model=` is answered by the improved model, `GET /health` reports `"model": "improved"`, and the top bar of the prototype shows "Engine: API (improved)". The in-browser engine is the same engine and follows the service's default model, so when the service is down, or on the deployed site that has none, the app answers exactly like the service (120 recorded journeys under both models, `parity.test.ts`; the three demo scenarios, `journey.e2e.test.ts`). The model itself has been frozen since tag `v0.9`: promoting it changed one setting, not the model. To repeat the EdNet check: download EdNet into `backend/data/raw/` (see README) and run `python scripts/compare_models.py` (about 15 minutes), which adds the EdNet table.

## Sprint 4: robustness, calibration and failure analysis

Scripts: `scripts/robustness.py`, `scripts/calibration.py`, `scripts/failure_analysis.py`. Tables: `results/robustness.md`, `results/calibration.md` (plot `results/calibration.png`), `results/failure_analysis.md`. All on made-up learners.

### Robustness (S4-2)

- **Fitted parameters are stable across seeds**: their standard deviation is about 0.01 to 0.03. With every tag credited, 16% to 21% of fitted values sit on a fitting bound (mostly slip at 0.30); with first-tag credit only 4% to 6% do.
- **Mis-tagged questions** (a question's main concept swapped for a random one, in the data the model is fitted and traced on, as unit-level tags in Barabari's data might cause): with 10% of items mis-tagged the improved model finds 5 points fewer true blockers and raises 2 points more false alarms; with 25%, 12 points fewer and 6 more. It stays ahead of the baseline at every level of noise, but at 25% it falls just below a clean baseline (42.1% against 44.7% true blockers).
- **A wrong concept graph**: three missing prerequisite links cost 13.5 points of hidden blockers found (the walk cannot follow a link it does not know); three wrong extra links cost only about 2 points, because the walk follows a prerequisite only when it was observed and is weak.
- **What we do about it**: concept tags and the graph must be checked by a trainer (the tag map allows per-question overrides), and missing links matter more than extra ones, so when in doubt a link should be kept.

### Calibration (S4-3)

| Quantity | Baseline ECE | Improved ECE |
|---|---|---|
| Next answer (predicted chance of a right answer) | 0.034 | 0.022 |
| Mastery (estimated P(mastered) against the hidden truth) | 0.067 | 0.068 |

- Next-answer probabilities are well calibrated; the improved model's are closer to the diagonal.
- **Mastery estimates run about 10 points high between 0.2 and 0.7**: of learners the engine puts at 0.55 to 0.65, only about half truly know the concept. So the 0.6 gap threshold flags a concept when roughly half the learners at that estimate have mastered it. Above 0.8 the estimates are slightly low (0.85 predicted, 0.89 observed).
- The ranking of learners is what drives recommendations, and it is good (mastery AUC 0.79 to 0.85); a recalibration step (for example isotonic regression on the mastery estimate) is the simple fix if trainers are shown the numbers.

### Failure analysis

In hidden-prerequisite cases the improved model cuts lessons on a concept the learner already knew from 20.2% to 13.0% (Sprint 2 simulator) and from 41.8% to 18.4% (Barabari simulator). The cost is more blockers that looked fine on the answers seen (8.5% to 9.8%, and 4.2% to 14.9%), because second tags no longer count as evidence about a prerequisite. Asking about each prerequisite directly would close that gap.

## Hackathon 2: paired comparison and an accuracy baseline

- **Paired comparison** (`scripts/paired_comparison.py`, `results/paired_comparison.md`): differences improved minus baseline within each seed, with a 95% interval over the 5 runs and the number of runs each model won. 12 of 14 measures are clearly better; missed gaps are not clearly different overall but worse in 4 of 5 Sprint 2 runs.
- **Accuracy baseline** (`scripts/accuracy_baseline.py`, `results/accuracy_baseline.md`): the same threshold, prerequisite walk and lesson choice on top of the learner's smoothed accuracy ((right + 1) / (answers + 2)), on the same learners as the model comparison. BKT finds 12 to 24 points more true blockers and recommends 18 to 34 points fewer lessons on known concepts; accuracy misses 0 to 3 points fewer gaps. The walk on plain accuracy recovers part of the gain over "study what you got wrong", BKT the rest.
- **The model as served** (`scripts/served_model_check.py`, `results/served_model.md`): the same learners and seeds with the service's own configuration, which has no per-question difficulty table until it has answers for its questions (`scripts/estimate_item_difficulty.py` builds it from stored answers). Against the baseline it is clearly better on 10 of 12 diagnosis measures and not clearly different on missed gaps. A table estimated from the simulator's answers would add about 1 point on Barabari's format and nothing measurable on the Sprint 2 simulator.
- **Shipped parameters:** the evaluation scripts no longer touch `circuit_coach/fitted_params.json` unless run with `--write-service-params`; `tests/test_shipped_params.py` checks the file against the frozen version.

## Limits

- Made-up learners follow the simulator's assumptions (`docs/synthetic_data.md`); results there say how the engine behaves when those assumptions hold.
- EdNet has no prerequisite graph and no hidden truth, so it only checks next-answer prediction, on a Korean English-test tutor.
- Nothing here shows that learners learn more. That needs real learners.
- Failure analysis and the multi-concept ablation (`results/failure_analysis.md`, `results/ablation_multitag.md`) list where the engine goes wrong; they are the starting point for the next model.
