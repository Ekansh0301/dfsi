# Made-up learner generator

Code: `circuit_coach/simulate.py` (the generator) and `circuit_coach/dataset.py` (files, split, validation). Script: `scripts/generate_dataset.py`. Tests: `tests/test_simulate.py`, `tests/test_dataset.py`.

Real learner data from the NGOs does not exist yet, and real datasets never say which concept a learner really lacked. Made-up learners have a **hidden mastery state that is known**, so the engine can be checked against the truth.

## What is generated

For each learner, with all randomness drawn from one seeded generator (`numpy.random.default_rng(seed)`):

| Part | How it is generated |
|---|---|
| Experience | `new` 30%, `some` 50%, `experienced` 20%, with base mastery 0.25, 0.55 and 0.80 |
| Hidden mastery | A mastered or not mastered flag per concept, drawn in prerequisite order. A concept with all prerequisites mastered is mastered with probability 0.7 times the base. A concept with an unmastered prerequisite is mastered with probability 0.03 |
| Learning speed | One multiplier per learner, log-normal with spread 0.35 |
| Item bank | 14 items per concept; 30% are tagged with a second concept (a prerequisite). Each item has its own slip (0.04 to 0.14) and guess (0.15 to 0.30) |
| Answers | An item is answered right with probability `1 - slip` when every tagged concept is mastered, otherwise by guessing. A learner who does not know chooses "I'm not sure" 30% of the time instead of guessing |
| Learning events | Every answer is a chance to learn the tagged concepts (`P_LEARN = 0.12` times speed). While a prerequisite is unmastered learning is 5 times slower (factor 0.2): **the prerequisite effect** |
| Journey | Modules in order with quick checks of 3 to 5 questions. Concepts answered wrongly get a lesson (`P_LESSON = 0.35`) and two practice questions. 10% of learners drop out after each module |
| Ground truth | At the end of each quick check the true mastery of all 10 concepts is stored (an "assessment point") together with how many answers the engine would have seen by then |

The limits of this story (for example that a multi-concept question needs all its concepts) are written at the top of `simulate.py`. Results on made-up data only reflect these assumptions.

## Barabari's quiz format (Sprint 3)

`SimConfig()` (named `barabari`) adds the parts of Barabari's quiz format that change the algorithm ([barabari_format.md](barabari_format.md)). `SimConfig.sprint2()` switches them all off and draws exactly the same random numbers as before, so the Sprint 2 results and dataset are reproduced byte for byte (`tests/test_simulate.py::test_sprint2_config_reproduces_the_sprint2_simulator_exactly`).

| Part | Barabari simulator |
|---|---|
| Question types | 70% multiple choice, 20% true/false (guess 0.5), 10% short answer marked by an instructor in quarters (mean mark 0.85 if the concepts are mastered, 0.2 if not) |
| Difficulty | Each item gets a difficulty d drawn from a normal distribution with spread 0.8 on the logit scale: harder items slip more and are guessed less often |
| Points | 20 for a hard item (d above 0.5), 10 otherwise |
| Retakes | A quick check passes at 60% of its points. A failed check is retaken with probability 0.8, up to 4 attempts, on the same items |
| Answers from memory | Right/wrong feedback helps on attempts 2 and 3 (probability 0.15 of answering right without mastery); after 3 attempts the answers are revealed (probability 0.6) |
| Ground truth | Stored after the last attempt of each quick check |

Pick the simulator with `--sim` in `scripts/generate_dataset.py` (default `barabari`) and `scripts/run_synthetic.py` (default `sprint2`, which keeps the published Sprint 2 results and the service's fitted parameters).

## Reproducible runs and the 70:30 split

```bash
python scripts/generate_dataset.py --learners 500 --seed 0      # writes datasets/synthetic_seed0/
python scripts/generate_dataset.py --check datasets/synthetic_seed0
```

- The same `--learners` and `--seed` give byte-identical files (`tests/test_dataset.py::test_saved_files_are_identical_for_the_same_seed`).
- The split is made **by learner**, so no learner has answers in both parts. A seeded random permutation puts 70% of learners in `train` and 30% in `test` (350 and 150 for 500 learners). The split is stored in `learners.csv`.

## Saved dataset

`backend/datasets/synthetic_seed0/` is committed, made with the Barabari simulator: 500 learners, 21,877 answers (mean 43.8 per learner), 350 train and 150 test. 17,526 answers are multiple choice, 2,702 true/false and 1,649 short answers; 1,417 of 2,341 quick checks were retaken at least once (12,533 first attempts, 4,827 second, 2,816 third, 1,701 fourth). It is small on purpose; the evaluation scripts regenerate larger runs in memory (3,000 learners per run).

| File | Content |
|---|---|
| `items.csv` | `item_id, concepts, slip, guess, question_type, points, difficulty` (concepts joined with `\|`) |
| `learners.csv` | `learner_id, experience, split, n_responses` |
| `responses.csv` | `learner_id, step, item_id, concepts, correct, unsure, module, question_type, score, attempt, points` in answer order (`score` only for short answers) |
| `ground_truth.csv` | `learner_id, module, n_responses, assessed`, then one 0/1 column per concept (true mastery at the end of that quick check) |
| `manifest.json` | simulator, seed, sizes, split sizes, SHA-256 of every file |

`datasets/.gitattributes` turns line-ending conversion off so the checksums hold on every operating system.

Load it with `circuit_coach.dataset.load(path)`; it returns the learners (with answers and ground truth), the item bank and the split.

## Validation

`dataset.validate(ds)` returns a list of problems, empty when the data is consistent. It checks:

- learner ids are unique and the split covers exactly the learners with only `train` and `test`, with a 70% train share;
- every item has known concepts, a known question type, positive points, and slip and guess between 0 and 1 that add up to less than 1;
- every learner has answers and at least one assessment point;
- every answer refers to a known item, carries that item's concepts and question type, belongs to a known module, and is never both unsure and correct;
- a short answer carries a score from 0 to 1 that matches `correct` (a score of 0.5 or more), other answers carry none, and attempts start at 1;
- assessment points are in order, cover all 10 concepts, and assess exactly the concepts of their module;
- the hidden states respect prerequisites: no more than 10% of (concept, assessment point) pairs are mastered with an unmastered prerequisite (it is about 4% in the committed dataset).

`dataset.verify_files(path)` checks the saved files against the manifest checksums. `generate_dataset.py` runs both before it finishes, and `tests/test_dataset.py` runs them on the committed dataset, so an edited or corrupted file fails the tests.
