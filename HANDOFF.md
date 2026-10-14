# Handoff notes

For teammates continuing **Circuit Coach** (Team Impact Theory, DFSI 2026, Problem 3B: identifying what a learner needs next). Anchor NGOs: Barabari Collective and Nirmaan.

Live prototype: https://dfsi.vercel.app/

## 1. What exists today

| Part | Where | State |
|---|---|---|
| Clickable prototype (learner app, trainer console, side-by-side demo, flow map, English and Hindi, light and dark) | `frontend/` | Done and deployed |
| Engine service (stateless FastAPI, Bayesian Knowledge Tracing, prerequisite walk, one-lesson recommender) | `backend/circuit_coach/` | Done, 29 tests pass |
| Made-up learner generator with hidden mastery | `backend/circuit_coach/simulate.py` | Done |
| Evaluation on made-up learners and on real EdNet data, failure analysis | `backend/scripts/`, results in `backend/results/` | Done |
| Prototype connected to the engine, with fallback to the in-browser engine | `frontend/src/api/engineClient.ts`, `mockServer.ts` | Done, hand-tested |
| Technical design document (Sprint 2) | `handoff/Technical_Design_Doc.pdf` and `.md` | Done |

Read `handoff/Technical_Design_Doc.pdf` first. It explains the design, the evaluation and the results in four pages.

## 2. Run it

Engine service:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[eval,dev]"
uvicorn circuit_coach.api:app --port 8000
pytest
```

Prototype:

```bash
cd frontend
npm install
npm run dev
```

By default the prototype uses its own in-browser engine. To use the service, copy `frontend/.env.example` to `frontend/.env.local` and set `VITE_API_URL=http://localhost:8000`. The top bar then shows "Engine: API". If the service is down it says so and falls back to the browser engine.

Evaluation commands are in `backend/README.md`. The EdNet raw files (1.2 GB) are not in the repo. Download KT1 from https://github.com/riiid/ednet into `backend/data/raw` (the exact files and the command are in `backend/README.md`).

## 3. Key results so far

On made-up learners (3,000 learners per run, 5 runs):

- Next-answer AUC: fitted BKT 0.688, hand-set BKT 0.649, best simple baseline 0.613.
- The prerequisite walk finds the real blocker in 61.9% of hidden-prerequisite cases, against 5.0% without it.

On real EdNet data (14,460 students, 1,765,406 answers, 357,756 of them in the test portion):

- Per-question accuracy AUC 0.721 beats fitted BKT 0.627. BKT ignores question difficulty.
- Using only the first concept tag (0.641) beats using all tags (0.627).

What did not work (the next work should start here):

1. Questions tagged with several concepts distort the fitted model (slip averages 0.25 against 0.14 when fitting on single-concept questions only, true value about 0.09).
2. BKT ignores question difficulty.
3. About 32% of checks with no real gap still trigger a lesson.
4. The prerequisite walk is a rule added after the model. The model itself does not know prerequisites.

Candidate improvements: single-concept credit, question difficulty, a prerequisite-aware model.

## 4. Hackathon 1 issues (T1 to T7)

The pre-hackathon document submitted to the instructors lists seven issues. The plan is to solve each in its own subdirectory. **The layout is undecided; agree it as a team first** (options: a top-level `hackathon1/` folder, subfolders inside the existing directories, or moving code).

| Issue | Task | Priority | Where | State at handoff |
|---|---|---|---|---|
| T1 | System architecture and API contracts | P0 | `backend/` | Gap. The diagram is only in `handoff/arch.svg` and the design doc. The API contract exists only as code and README. Commit a diagram and the request and response schemas. |
| T2 | BKT with tests | P0 | `backend/circuit_coach/` | Done: EM fitting, multi-concept, "I'm not sure", tests for updates and parameter recovery. Document and verify. |
| T3 | Prerequisite diagnosis and recommendations | P0 | `backend/circuit_coach/` | Done: gap threshold 0.6, prerequisite walk, first untried lesson, repeat-gap. Document and verify. |
| T4 | Connect React to FastAPI | P0 | `frontend/` | Built and hand-tested. Gap: no automated test for API mode and fallback. |
| T5 | Made-up learner generator | P0 | `backend/` | Done. Gaps: no saved dataset files and no validation step. |
| T6 | Evaluate models, compare baselines | P1 | `backend/` | Done, reports in `backend/results/`. |
| T7 | End-to-end test and demo | P1 | `frontend/` and `backend/` | Not done. Run the full learner journey (onboarding, quiz, recommendation, follow-up, API failure, fallback), record the results, record the demo video. |

Decisions already made: add persistence with SQLite first (written so PostgreSQL works by changing the connection URL); in each issue folder, document and verify what exists, then fill the gaps.

**Corrections to the submitted document.** It contains three errors. Fix them in the revised technical design document:

1. It says PostgreSQL stores learner state. The service is currently stateless. This becomes true only once the SQLite work is added.
2. It says about 36 answers per learner. The real mean is 29.5, so one run of 3,000 learners is about 88,600 answers.
3. It gives 357,756 answers for EdNet. That is only the test portion. The full sample is 1,765,406 answers.

The issues themselves live in the private team repository, so check the issue numbers there before linking any commit to them.

## 5. Demo scenarios (verified against the engine)

1. Direct gap: symbols and wiring right, both diagram questions wrong. Recommends the circuit diagrams lesson.
2. Hidden cause: the symbol question is also wrong. Recommends the circuit symbols lesson instead.
3. Clean result: all correct. No recommendation.
4. Follow-up check failed after "Got it!": repeat-gap recommendation with a different lesson, and the trainer is flagged.

Use **Demo scenarios** in the top bar, then **Reset all demo data**.

## 6. Conventions

- No em dashes or en dashes anywhere in the site content or READMEs. `npm run build` runs `npm run check:dashes` and fails if one appears.
- Commits are made under your own name with a short plain message. Course PDFs and sprint documents are not committed (see `.gitignore`); `handoff/` is the exception.
- The curriculum lives in two places that must match: `frontend/src/data/curriculum.ts` and `backend/circuit_coach/curriculum.py`. `backend/tests/test_parity.py` checks this.
- Deploy: import the repository in Vercel with Root Directory `frontend`, build command `npm run build`, output directory `dist`.

## 7. Not in the repo

The original course PDFs, the UI design plan, the project summary and the Hackathon 1 plan are kept locally by Ekansh. The Hackathon 1 plan uses a different task numbering (T1 to T16) from the submitted T1 to T7, so do not reuse it as is.
