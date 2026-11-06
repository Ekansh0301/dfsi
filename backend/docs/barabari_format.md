# Barabari's quiz format and how the engine uses it

Source: "The Barabari Collective Quiz & Assignment Format and Evaluation" (shared by Barabari, November 2026). Code: `circuit_coach/barabari.py`, `circuit_coach/barabari_tags.json`. Tests: `tests/test_barabari.py`. Sample data: `datasets/barabari_sample/`.

Barabari's LMS (Async-LMS on PostgreSQL) attaches a quiz to each unit. We adapt only what changes the algorithm: question types, points, retakes and instructor-marked short answers. Assignments (code, spreadsheets, web pages) are graded by Barabari's own evaluator, so we do not grade them.

## What Barabari's format says, and what we did with it

| Barabari rule | Engine change |
|---|---|
| Quizzes sit at the unit level and gate the next unit | A Barabari unit maps to one of our modules; the unit's quiz is the module quick check |
| `multiple_choice`: 2 to 6 options, one correct | Unchanged; uses the concept's fitted guess rate |
| `true_false` | Guess rate 0.5: a right answer is weaker evidence than a multiple-choice one |
| `short_answer`, graded by an instructor | Points earned / points becomes partial credit from 0 to 1. Guess rate 0.05. Unmarked answers are left out until marked |
| Points per question | Used for the quiz score; partial credit on a short answer uses its points |
| Pass at 60% (`passing_score / max_score`) | Reported per attempt; matches our gap threshold of 0.6 |
| Retakes allowed; every attempt kept | Attempt k counts with weight 0.5 to the power k minus 1 (1, 0.5, 0.25, ...) |
| Correct answers revealed after 3 attempts (`MIN_ATTEMPTS_FOR_REVEAL = 3`) | Reported as `answers_revealed`; why later attempts count for less |
| No concept tags in their data | Unit-level tags in `barabari_tags.json`, with per-question overrides checked by a trainer |

## Update rules

For a mastery estimate p and the usual slip s and learn l, the guess g now depends on the question type (multiple choice: the concept's own; true/false: 0.5; short answer: 0.05). With partial credit c from 0 to 1:

```latex
p' = c \cdot P(\text{mastered} \mid \text{right}) + (1 - c) \cdot P(\text{mastered} \mid \text{wrong})
```

A retake moves the estimate only part of the way, then learning applies as before:

```latex
p'' = p + 0.5^{\,k-1} (p' - p), \qquad p_{\text{new}} = p'' + (1 - p'')\,\ell
```

With the defaults (multiple choice, no score, first attempt) the update is exactly the original BKT step.

## Concept tags

Barabari's questions carry no concept tags. `TagMap` tags every question with its unit's concepts, and a trainer can override a single question (key: question id, or `quiz id/question id`). Question tags always win. `TagMap.from_modules()` builds the unit map from our own modules (`unit_m1` to `unit_m6`).

Unit-level tags put several concepts on every question, which is the multi-concept credit problem in `results/ablation_multitag.md`. Question-level tags are better wherever a trainer can supply them.

## Assumed attempt record

The PDF names the `quiz_attempts` table but not its columns. Until Barabari shares them we read this shape (only `parse_attempt` would change):

```json
{
  "id": "att_002",
  "quiz_id": "quiz_unit_m3_wiring_basics",
  "student_id": "usr_b_anon",
  "attempt_number": 1,
  "submitted_at": "2026-11-02T10:07:00Z",
  "answers": [
    { "question_id": "q_01", "selected_option_id": "opt_1b" },
    { "question_id": "q_05", "text_answer": "L1 because S1 is closed", "points_earned": 12 }
  ]
}
```

## Using it

- **Service:** `POST /v1/barabari/quiz-attempt` takes `state`, Barabari's `quiz`, one `attempt` and optional `tags`. It returns the updated state, the recommendation, the quiz score (points, percent, passed, points awaiting review, whether answers are revealed) and the assessed concepts. See [api_contract.md](api_contract.md).
- **Offline:** `barabari.parse_quiz`, `parse_attempt` and `attempt_events` turn an export into engine events for evaluation.

## Still needed from Barabari

- An anonymised `quiz_attempts` export (scores only is enough) to check the assumed shape and to evaluate on real attempts.
- Nothing else: their assignment evaluator stays theirs.
