# End-to-end test results and demo script

Covers the full learner journey: onboarding, quick check, recommendation, follow-up, API failure and fallback. Tests: `frontend/src/api/__tests__/journey.e2e.test.ts` (needs the service), `presets.test.ts`, `engineClient.test.ts`.

## Repeat the demo

Terminal 1, the service:

```bash
cd backend
pip install -e ".[dev]"
uvicorn circuit_coach.api:app --port 8000
```

Terminal 2, the prototype in API mode:

```bash
cd frontend
npm install
echo VITE_API_URL=http://localhost:8000 > .env.local
npm run dev        # http://localhost:5173, the top bar shows "Engine: API"
```

Use **Demo scenarios** in the top bar to jump to any step, and **Reset all demo data** between runs.

| Step | What to do | What you should see |
|---|---|---|
| 1. Direct gap | Demo scenarios, "Gap diagnosed: circuit diagrams" | The one recommendation is the circuit diagrams lesson |
| 2. Hidden cause | "Root cause is a prerequisite" | Diagrams were wrong because symbols are weak: the circuit symbols lesson is recommended instead |
| 3. Clean result | Learner app, finish a quick check with every answer right | No recommendation |
| 4. Follow-up | Take the diagrams lesson, tap "Got it!", then answer the due re-check wrongly (Demo scenarios, "Spaced re-check is due", then the Module 5 quick check) | A repeat-gap recommendation with a different lesson, and the trainer console shows a flagged escalation |
| 5. API failure | Stop uvicorn (Ctrl+C) and finish any quick check | The top bar changes to "Engine: API unreachable, using browser"; the recommendation still appears |
| 6. Recovery | Start uvicorn again and finish another step | The top bar returns to "Engine: API" |

Without `VITE_API_URL` the top bar shows "Engine: in browser (improved)" and the same flow runs fully offline, with the same answers as the service.

## Automated results

Run on 2026-11-14 for POC v1.0 (Windows 11, Python 3.13.1, Node 22.13.1). The first run, on 2026-10-14, had 86 backend and 17 frontend tests.

| Suite | Command | Result |
|---|---|---|
| Backend | `cd backend && pytest` | 239 passed |
| Frontend unit and fallback | `cd frontend && npm test` | 174 passed, 8 skipped (the 8 need the service) |
| Frontend end to end, service running | `E2E_API_URL=http://localhost:8000 npm run test:e2e` (or `npm test` with the variable set) | 182 passed (all frontend tests, including the 8 journey tests) |
| Types and build | `npm run typecheck`, `npm run build` | passed |

End-to-end cases (`journey.e2e.test.ts`):

| Case | Needs service | Result |
|---|---|---|
| Scenario 1, direct gap: diagrams, `ct_diag_walk`, API mode | yes | passed |
| Scenario 2, hidden cause: chain diagrams then symbols, `ct_sym_cards` | yes | passed |
| Scenario 3, clean result: no recommendation, 5 of 5 right | yes | passed |
| Scenario 4, follow-up: "Got it!" raises mastery, re-check scheduled, wrong answer gives a repeat gap with a new lesson, escalation flagged | yes | passed |
| Service and browser engine agree (direct, hidden, clean): same start module, concept, chain, lesson, mastery | yes | passed (3) |
| Service goes down mid-journey, falls back, returns to API mode on the next call | yes | passed |
| Service down for the whole journey, scenario 1 and the follow-up flow | no | passed (2) |

Other tests that cover the journey: `engineClient.test.ts` (requests sent in API mode, use of the service's answers, network error, error status, 4 second timeout, recovery, health check on start-up, quick checks while the service stays down), `presets.test.ts` (every demo preset lands where its label says), backend `test_api.py`, `test_engine.py`, `test_diagnosis.py`, `test_contract.py`.

## Manual run in the browser

The prototype was run in the built-in browser against a live service (`uvicorn` on port 8765, Vite with `VITE_API_URL` set):

| Check | Result |
|---|---|
| Top bar shows "Engine: API" on load | yes |
| Onboarding: welcome, track, experience, six placement questions, all answered "I'm not sure" | the browser sent `OPTIONS` then `POST /v1/onboarding`, both 200 (CORS works); the start screen recommended Module 1, as the engine returns for a learner who is unsure of everything |
| Service stopped, Module 1 quick check answered and submitted | top bar changed to "Engine: API unreachable, using browser"; the results screen appeared ("0 of 3 right") and the flow continued |

The quick check answers in this run were entered by calling the on-screen buttons from the page's script, because clicking by coordinates did not line up in the resized pane. The click handlers that ran are the app's own.

### Manual checks for POC v1.0 (2026-11-14, built-in browser)

| Check | Result |
|---|---|
| Module 2 check, written answer, "See my answers" | The review lists the written answer with "Waiting for your trainer's mark"; no blank screen |
| Escalation preset, trainer case view | Mastery shown as Needs work, Getting there, Strong |
| Reload in the middle of a quick check | Returns to the same question with the earlier answers |
| Listen button on a question | Speech starts, the button shows the stop state; hidden when the device has no voice for the language |
| Built site: service worker and cache | Worker active; the app's script and styles cached after the first visit |
| Top bar | Shows "Engine: API" once the service answers, and the version and build commit |

## Found and fixed

The demo preset **"Gap diagnosed: circuit diagrams"** answered `q_w1` (a symbols question) wrongly, so symbols was also weak and it recommended the symbols lesson. That made it identical to the "Root cause is a prerequisite" preset and contradicted scenario 1. `frontend/src/api/mockServer.ts` now answers `q_w1` correctly; `presets.test.ts` checks both presets.

## Not done

- **The demo video is not recorded.** It has to be recorded by a person with the screen capture of their choice, following the table above.
- The manual run did not repeat the lesson, "Got it!" and trainer-console screens by hand; those are covered by the automated tests above.
