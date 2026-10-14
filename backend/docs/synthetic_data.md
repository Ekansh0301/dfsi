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

## Reproducible runs and the 70:30 split

```bash
python scripts/generate_dataset.py --learners 500 --seed 0      # writes datasets/synthetic_seed0/
python scripts/generate_dataset.py --check datasets/synthetic_seed0
```

- The same `--learners` and `--seed` give byte-identical files (`tests/test_dataset.py::test_saved_files_are_identical_for_the_same_seed`).
- The split is made **by learner**, so no learner has answers in both parts. A seeded random permutation puts 70% of learners in `train` and 30% in `test` (350 and 150 for 500 learners). The split is stored in `learners.csv`.

## Saved dataset

`backend/datasets/synthetic_seed0/` is committed (500 learners, 14,935 answers, mean 29.9 answers per learner, 350 train and 150 test). It is small on purpose; the evaluation scripts regenerate larger runs in memory (3,000 learners per run).

| File | Content |
|---|---|
| `items.csv` | `item_id, concepts, slip, guess` (concepts joined with `\|`) |
| `learners.csv` | `learner_id, experience, split, n_responses` |
| `responses.csv` | `learner_id, step, item_id, concepts, correct, unsure, module` in answer order |
| `ground_truth.csv` | `learner_id, module, n_responses, assessed`, then one 0/1 column per concept (true mastery at the end of that quick check) |
| `manifest.json` | seed, sizes, split sizes, SHA-256 of every file |

`datasets/.gitattributes` turns line-ending conversion off so the checksums hold on every operating system.

Load it with `circuit_coach.dataset.load(path)`; it returns the learners (with answers and ground truth), the item bank and the split.

## Validation

`dataset.validate(ds)` returns a list of problems, empty when the data is consistent. It checks:

- learner ids are unique and the split covers exactly the learners with only `train` and `test`, with a 70% train share;
- every item has known concepts and slip and guess strictly between 0 and 0.5;
- every learner has answers and at least one assessment point;
- every answer refers to a known item, carries that item's concepts, belongs to a known module, and is never both unsure and correct;
- assessment points are in order, cover all 10 concepts, and assess exactly the concepts of their module;
- the hidden states respect prerequisites: no more than 10% of (concept, assessment point) pairs are mastered with an unmastered prerequisite (it is about 3% by construction).

`dataset.verify_files(path)` checks the saved files against the manifest checksums. `generate_dataset.py` runs both before it finishes, and `tests/test_dataset.py` runs them on the committed dataset, so an edited or corrupted file fails the tests.
