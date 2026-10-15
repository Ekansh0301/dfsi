# Knowledge tracing (BKT)

Code: `circuit_coach/bkt.py` (update rules and EM fitting) and `Engine.trace` in `circuit_coach/engine.py` (applying them to a learner). Tests: `tests/test_bkt.py`.

## Model

Each of the 10 concepts has its own two-state model: the learner has either mastered it or not. Four parameters describe a concept:

| Parameter | Meaning | Hand-set value |
|---|---|---|
| `p_init` | P(mastered) before the first question | 0.25 |
| `p_learn` | P(not mastered to mastered) after each opportunity | 0.12 |
| `p_slip` | P(wrong answer while mastered) | 0.10 |
| `p_guess` | P(right answer while not mastered) | 0.20 |

There is no forgetting and no link between concepts: prerequisites are handled after tracing, by the root-cause walk ([diagnosis.md](diagnosis.md)).

## Update after one answer

With `p` = current P(mastered):

```
right answer:   post = p (1 - slip) / ( p (1 - slip) + (1 - p) guess )
wrong answer:   post = p slip       / ( p slip       + (1 - p) (1 - guess) )
new p          = post + (1 - post) learn       clamped to [0.01, 0.99]
```

The clamp keeps one answer from ever making the model certain.

| Case | Handling | Code |
|---|---|---|
| "I'm not sure" | Treated as a wrong answer, but with guess set to `min(guess, 0.02)`: the learner showed they do not know, without the chance of a lucky guess. It lowers mastery more than a plain wrong answer | `bkt.posterior(..., unsure=True)` |
| Question tagged with several concepts | Every tagged concept is updated with its own parameters, and its observation count goes up by one (naive credit assignment) | `Engine.trace` |
| Unknown concept tag | Ignored by the tracer; the API rejects it with 422 before that | `Engine.trace`, `api.py` |
| "Got it!" | Learning step only: `p + (1 - p) learn`. Not treated as proof; a spaced re-check follows | `bkt.learn_step`, `Engine.got_it` |
| Onboarding | Every concept starts at 0.12 (new), 0.30 (some) or 0.45 (experienced) and the placement answers are traced from there | `Engine.onboard` |
| Concept never seen | Uses that concept's `p_init` | `Engine.mastery_of` |

Predicted chance of a right answer (used in evaluation): `p (1 - slip) + (1 - p) guess`.

## Fitting with EM

`bkt.fit_params(sequences)` fits one concept's four parameters from learners' 0/1 answer sequences with expectation maximisation (Baum-Welch on the two-state model, scaled forward-backward, vectorised over learners).

- Five starting points (the hand-set values, two fixed alternatives and two random ones from a seeded generator) are tried, and the highest likelihood wins, because EM can stop in a poor local maximum.
- Parameters are bounded so the model stays identifiable: `p_slip` at most 0.30 and `p_guess` at most 0.35, so "not mastered" cannot explain everything.
- With fewer than 5 usable sequences (2 or more answers each) the hand-set values are returned.
- The fit uses right and wrong only. "I'm not sure" counts as wrong when fitting.
- A multi-concept answer appears in the sequence of every tagged concept, which is the source of the inflated slip rates described in `results/ablation_multitag.md`.

`scripts/run_synthetic.py` fits all 10 concepts on the training learners and writes `circuit_coach/fitted_params.json`, which the service loads at start-up (`GET /health` reports `"parameters": "fitted"`). Without the file the service uses the hand-set values.

## What the tests check

| Requirement | Tests in `tests/test_bkt.py` |
|---|---|
| Mastery update after right and wrong answers | `test_correct_answer_follows_the_bkt_formula`, `test_wrong_answer_follows_the_bkt_formula`, `test_correct_answer_raises_mastery_and_wrong_lowers_it` |
| Role of each parameter | `test_more_guessing_makes_a_correct_answer_weaker_evidence`, `test_more_slipping_makes_a_wrong_answer_weaker_evidence`, `test_no_learning_means_the_update_is_just_the_posterior`, `test_learn_step_follows_the_transition`, `test_predicted_correctness_mixes_slip_and_guess` |
| Bounds | `test_mastery_stays_inside_bounds`, `test_fitted_parameters_stay_inside_the_bounds` |
| "I'm not sure" | `test_unsure_uses_a_near_zero_guess_rate`, `test_unsure_is_weaker_evidence_of_mastery_than_a_plain_wrong_answer` |
| Multi-concept questions | `test_multi_concept_question_updates_each_concept_with_its_own_parameters`, `test_unknown_concept_tags_are_ignored_by_the_tracer` (and `tests/test_engine.py::test_multi_concept_question_updates_every_tag`) |
| Recovery of known parameters on simulated data | `test_em_recovers_known_parameters`, `test_em_recovers_several_known_parameter_sets` (three parameter sets, 3,000 simulated learners each, every parameter within 0.05) |
| Fitting behaviour | `test_em_fit_beats_the_hand_set_parameters_on_likelihood`, `test_fitting_is_reproducible`, `test_fit_falls_back_to_hand_set_when_there_is_too_little_data` |

Run them with `pytest tests/test_bkt.py`.

## Known limits

- One independent model per concept: the model does not know that weak prerequisites slow learning.
- No question difficulty: on EdNet, per-question accuracy beats BKT (AUC 0.721 against 0.627, `results/ednet_results.md`).
- Naive multi-concept credit inflates fitted slip (0.25 against about 0.09 true, `results/ablation_multitag.md`).
