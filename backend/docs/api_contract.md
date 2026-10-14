# API contract

The engine service exposes five endpoints. All bodies are JSON. The machine-readable contract is [openapi.json](openapi.json), generated from the code by `python scripts/export_openapi.py`; `tests/test_contract.py` fails if the two disagree. When the service is running, the same schema is browsable at `/docs`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Service status and which BKT parameters are loaded |
| GET | `/v1/concepts` | Concept graph, modules and lesson ids |
| POST | `/v1/onboarding` | Seed a new learner from stated experience and the placement quiz |
| POST | `/v1/quiz-result` | Update the model from a quick check, return at most one recommendation |
| POST | `/v1/got-it` | Apply a learning step after the learner taps "Got it!" |

The frontend side of the contract is `frontend/src/api/engineClient.ts` (request and response types) and `frontend/src/api/types.ts` (`Recommendation`).

## Shared types

### `State`

Sent with every POST that changes the model and returned updated. All fields are optional on input (an empty object is a learner with no history).

| Field | Type | Notes |
|---|---|---|
| `mastery` | object, concept id to number | P(mastered), kept in [0.01, 0.99] by updates. Missing concepts use the concept's `p_init` |
| `observations` | object, concept id to integer | Answers seen per concept |
| `tried` | object, concept id to list of lesson ids | Lessons already opened; never recommended again while an untried one exists |

### `Event`

One answered question.

| Field | Type | Notes |
|---|---|---|
| `concept_tags` | list of concept ids, at least one | Every tag is updated (naive credit assignment) |
| `is_correct` | boolean | |
| `unsure` | boolean, default `false` | The learner chose "I'm not sure" |

### `Recommendation`

| Field | Type | Notes |
|---|---|---|
| `concept_id` | concept id | The concept to work on (the root cause) |
| `observed_concept_id` | concept id | The weak concept the quick check showed |
| `chain` | list of concept ids | From the observed concept back to the root cause, e.g. `["diagrams", "symbols"]` |
| `strong_concept_id` | concept id or `null` | A concept the learner did well on, used in the message |
| `diagnostic_text` | `{ "en": string, "hi": string }` | Plain-language explanation for the learner |
| `recommended_content_id` | lesson id | The one lesson to take next |
| `repeat_gap` | boolean | `true` after a failed follow-up check |
| `created_at` | integer | Copied from the request's `now` (ms) |

Concept ids: `safety`, `quantities`, `ohm`, `symbols`, `wiring`, `multimeter`, `series_parallel`, `diagrams`, `earthing`, `fault`. Module ids: `m1` to `m6`.

## Endpoints

### `GET /health`

```json
{ "status": "ok", "version": "0.1.0", "parameters": "fitted" }
```

`parameters` is `"fitted"` when `circuit_coach/fitted_params.json` exists, else `"hand-set"`.

### `GET /v1/concepts`

```json
{
  "concepts": {
    "diagrams": { "name": { "en": "Reading circuit diagrams", "hi": "..." }, "prereqs": ["symbols", "wiring"] }
  },
  "modules": { "m3": { "number": 3, "concepts": ["symbols", "wiring", "diagrams"] } },
  "content": { "diagrams": ["ct_diag_walk", "ct_diag_practice", "ct_diag_example"] }
}
```

(Shortened: every concept, module and concept's lesson list is returned.)

### `POST /v1/onboarding`

Request:

| Field | Type | Notes |
|---|---|---|
| `experience` | `"new"`, `"some"` or `"experienced"` | Sets the starting mastery of every concept to 0.12, 0.30 or 0.45 |
| `events` | list of `Event`, default `[]` | Placement quiz answers |

```json
{
  "experience": "some",
  "events": [
    { "concept_tags": ["safety"], "is_correct": true },
    { "concept_tags": ["symbols"], "is_correct": false, "unsure": true }
  ]
}
```

Response: `{ "state": State, "start_module_id": string }`. The start module is the first module with a concept that is unobserved or below 0.6.

```json
{
  "state": {
    "mastery": { "safety": 0.718, "quantities": 0.3, "symbols": 0.267, "...": 0.3 },
    "observations": { "safety": 1, "symbols": 1 },
    "tried": {}
  },
  "start_module_id": "m2"
}
```

### `POST /v1/quiz-result`

Request:

| Field | Type | Notes |
|---|---|---|
| `state` | `State` | Required |
| `module_id` | module id | Required; its concepts are the ones "assessed" |
| `events` | list of `Event` | Required (may be empty) |
| `recheck_concept` | concept id or `null` | Set when a spaced re-check on this concept was answered wrongly |
| `now` | integer, default `0` | Timestamp in ms, stored as `created_at` |

```json
{
  "state": {
    "mastery": { "symbols": 0.55, "wiring": 0.7, "diagrams": 0.3 },
    "observations": { "symbols": 2, "wiring": 2, "diagrams": 1 },
    "tried": {}
  },
  "module_id": "m3",
  "events": [
    { "concept_tags": ["symbols"], "is_correct": false },
    { "concept_tags": ["wiring"], "is_correct": true },
    { "concept_tags": ["diagrams"], "is_correct": false }
  ],
  "now": 1760000000000
}
```

Response: `{ "state": State, "recommendation": Recommendation or null }`. `null` means no assessed concept is below 0.6.

```json
{
  "state": {
    "mastery": { "symbols": 0.387, "wiring": 0.922, "diagrams": 0.184 },
    "observations": { "symbols": 3, "wiring": 3, "diagrams": 2 },
    "tried": {}
  },
  "recommendation": {
    "concept_id": "symbols",
    "observed_concept_id": "diagrams",
    "chain": ["diagrams", "symbols"],
    "strong_concept_id": "wiring",
    "diagnostic_text": {
      "en": "You got stuck on reading circuit diagrams. It builds on circuit symbols, so let's start there.",
      "hi": "..."
    },
    "recommended_content_id": "ct_sym_cards",
    "repeat_gap": false,
    "created_at": 1760000000000
  }
}
```

With `recheck_concept` set, the recommendation always exists, has `repeat_gap: true`, and uses a lesson not in `tried`.

### `POST /v1/got-it`

Request: `{ "state": State, "concept_id": concept id }`.
Response: `{ "state": State }` with one BKT learning step applied to that concept. It is not treated as proof of mastery; the frontend schedules a spaced re-check.

```json
{ "state": { "mastery": { "symbols": 0.356 }, "observations": { "symbols": 3 }, "tried": { "symbols": ["ct_sym_cards"] } } }
```

## Errors

| Status | When | Body |
|---|---|---|
| 404 | Unknown `module_id` | `{ "detail": "Unknown module m99" }` |
| 422 | Unknown concept in `state`, `events`, `recheck_concept` or `concept_id` | `{ "detail": "Unknown concepts: ['nope']" }` |
| 422 | Missing or badly typed field (FastAPI validation) | `{ "detail": [{ "type": "missing", "loc": ["body", "events"], "msg": "Field required" }] }` |

The frontend treats any non-2xx status as "service unavailable" and falls back to the in-browser engine.

## Changing the contract

1. Change the Pydantic models in `circuit_coach/api.py`.
2. Run `python scripts/export_openapi.py` and commit `docs/openapi.json`.
3. Update `frontend/src/api/engineClient.ts` and `types.ts` to match.
4. Run `pytest`; `tests/test_contract.py` checks the committed schema, the live responses and the frontend `Recommendation` type.
