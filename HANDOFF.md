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

Aman Srivastava completed all seven issues on 14 October 2026 (eight commits on the official repo, one per issue plus the revised design document). Each issue is documented in `backend/docs/` rather than in its own folder, with tests alongside.

| Issue | Covered by |
|---|---|
| T1 Architecture and API contracts | `backend/docs/architecture.md`, `api_contract.md`, `openapi.json`, `tests/test_contract.py` |
| T2 BKT | `backend/docs/bkt.md`, `tests/test_bkt.py` |
| T3 Prerequisite diagnosis and recommendations | `backend/docs/diagnosis.md`, `tests/test_diagnosis.py` |
| T4 React and FastAPI integration | `frontend/src/api/__tests__/engineClient.test.ts` |
| T5 Made-up learner generator | `backend/docs/synthetic_data.md`, `circuit_coach/dataset.py`, `backend/datasets/synthetic_seed0/` |
| T6 Evaluation and baselines | `backend/docs/evaluation.md`, `tests/test_evaluation.py`, `backend/results/` |
| T7 End-to-end test and demo | `backend/docs/e2e_results.md`, `frontend/src/api/__tests__/journey.e2e.test.ts` |

The revised design document is `backend/docs/Technical_Design_Doc.md`. It also corrects the three errors in the submitted PDF (PostgreSQL claim, 36 answers per learner, 357,756 EdNet answers). `handoff/Technical_Design_Doc.pdf` is the earlier Sprint 2 version.

**Still open**

- The demo video is not recorded. Steps are in `backend/docs/e2e_results.md`.
- Server-side storage of learners is not built. The plan is SQLite first, PostgreSQL by changing the connection URL.
- The improvement candidates in section 3 (single-concept credit, question difficulty, a prerequisite-aware model, more evidence before a lesson).

Test counts at the last check: 86 backend tests, 17 frontend tests plus 8 end-to-end tests that need the service running (`E2E_API_URL=http://localhost:8000 npm run test:e2e`). If you have a `frontend/.env.local` with `VITE_API_URL`, move it aside before `npm test`, or one "without VITE_API_URL" test fails.

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
