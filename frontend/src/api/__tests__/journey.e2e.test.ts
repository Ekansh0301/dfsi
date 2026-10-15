/**
 * End-to-end learner journey against a running engine service (Issue T7).
 *
 *   cd backend && uvicorn circuit_coach.api:app --port 8000
 *   cd frontend && E2E_API_URL=http://localhost:8000 npm run test:e2e
 *
 * Skipped when E2E_API_URL is not set, so `npm test` needs no service. The four demo
 * scenarios from HANDOFF.md are run through the real service and again through the browser
 * engine, which must agree. The last tests take the service away mid-journey.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

const API: string | undefined = (globalThis as { process?: { env: Record<string, string | undefined> } }).process?.env.E2E_API_URL;
const DEAD = "http://127.0.0.1:9"; // nothing listens here

const PLACEMENT = ["q_x_saf4", "q_x_q3", "q_x_ohm2", "q_x_sym2", "q_x_wir2", "q_x_mm2"];
/** Module 3, both diagram questions wrong, symbols and wiring right (the app's "gap" preset). */
const M3_DIAGRAM_GAP = [
  { question_id: "q_w1", chosen: 0 },
  { question_id: "q_w2", chosen: 0 },
  { question_id: "q_w3", chosen: 1 },
  { question_id: "q_w4", chosen: 2 },
  { question_id: "q_w5", chosen: 0 },
];
/** Module 3 with the symbols question also wrong. */
const M3_SYMBOL_ROOT = [
  { question_id: "q_w1", chosen: 0 },
  { question_id: "q_w2", chosen: 0 },
  { question_id: "q_w3", chosen: null },
  { question_id: "q_w4", chosen: 2 },
  { question_id: "q_w5", chosen: 0 },
];

afterEach(() => {
  vi.unstubAllEnvs();
});

/** A fresh copy of the app's store, talking to `url` (or to nothing). */
async function app(url?: string) {
  vi.resetModules();
  if (url) vi.stubEnv("VITE_API_URL", url);
  const client = await import("../engineClient");
  const store = await import("../mockServer");
  const { QUESTIONS } = await import("../../data/curriculum");
  store.resetDemo();
  const me = () => store.getDB().learners[store.getDB().activeLearnerId];
  const right = (ids: string[]) => ids.map((id) => ({ question_id: id, chosen: QUESTIONS[id].correct }));
  return { client, store, me, right, QUESTIONS };
}
type App = Awaited<ReturnType<typeof app>>;

const placement = (a: App, wrongSymbols = false) =>
  a.right(PLACEMENT).map((x) => (wrongSymbols && x.question_id === "q_x_sym2" ? { ...x, chosen: 2 } : x));

/** Steps 1 to 3 of every scenario: onboarding, then the module 3 quick check. */
async function journey(a: App, scenario: "direct" | "hidden" | "clean") {
  const start = await a.store.finishOnboarding("some", placement(a, scenario === "hidden"));
  const quiz = scenario === "direct" ? M3_DIAGRAM_GAP : scenario === "hidden" ? M3_SYMBOL_ROOT : a.right(["q_w1", "q_w2", "q_w3", "q_w4", "q_w5"]);
  const result = await a.store.submitQuiz("m3", quiz);
  return { start, result, rec: a.me().recommendation };
}

describe.skipIf(!API)("demo scenarios through the real service", () => {
  it("1. direct gap: recommends the circuit diagrams lesson", async () => {
    const a = await app(API);
    const { start, rec } = await journey(a, "direct");
    expect(a.client.getEngineMode()).toBe("api");
    expect(start).toBe("m3");
    expect(rec).toMatchObject({ concept_id: "diagrams", observed_concept_id: "diagrams", repeat_gap: false, recommended_content_id: "ct_diag_walk" });
  });

  it("2. hidden cause: the weak symbols prerequisite is recommended instead", async () => {
    const a = await app(API);
    const { rec } = await journey(a, "hidden");
    expect(rec).toMatchObject({ concept_id: "symbols", observed_concept_id: "diagrams", chain: ["diagrams", "symbols"], recommended_content_id: "ct_sym_cards" });
  });

  it("3. clean result: no recommendation", async () => {
    const a = await app(API);
    const { result, rec } = await journey(a, "clean");
    expect(rec).toBeUndefined();
    expect(result.correct).toBe(result.total);
  });

  it("4. follow-up: Got it!, a failed re-check, a repeat gap and a flagged trainer", async () => {
    const a = await app(API);
    const { rec } = await journey(a, "direct");
    a.store.startContent(rec!.recommended_content_id, rec!.concept_id);
    const before = a.me().mastery.diagrams!;
    await a.store.gotIt();
    expect(a.me().mastery.diagrams!).toBeGreaterThan(before);
    expect(a.me().recommendation).toBeUndefined();
    const check = a.me().rechecks.find((r) => r.status === "scheduled")!;
    expect(check.concept_id).toBe("diagrams");

    const res = await a.store.submitQuiz("m4", [
      { question_id: "q_p1", chosen: 0 },
      { question_id: check.question_id, chosen: null },
      { question_id: "q_p2", chosen: 0 },
    ]);
    expect(res.recheck).toEqual({ concept: "diagrams", passed: false });
    expect(res.recommendation).toMatchObject({ repeat_gap: true, concept_id: "diagrams" });
    expect(res.recommendation!.recommended_content_id).not.toBe("ct_diag_walk");
    const esc = a.store.getDB().escalations.find((e) => e.learner_id === a.me().id && e.concept_id === "diagrams");
    expect(esc?.repeat_gap).toBe(true);
  });
});

describe.skipIf(!API)("service and browser engine agree", () => {
  for (const scenario of ["direct", "hidden", "clean"] as const) {
    it(`${scenario}: same recommendation and mastery`, async () => {
      const viaApi = await app(API);
      const r1 = await journey(viaApi, scenario);
      const m1 = structuredClone(viaApi.me().mastery);
      const local = await app();
      const r2 = await journey(local, scenario);
      expect(r1.start).toBe(r2.start);
      expect(r1.rec?.concept_id).toBe(r2.rec?.concept_id);
      expect(r1.rec?.chain).toEqual(r2.rec?.chain);
      expect(r1.rec?.recommended_content_id).toBe(r2.rec?.recommended_content_id);
      for (const [c, p] of Object.entries(local.me().mastery)) expect(m1[c as keyof typeof m1]).toBeCloseTo(p as number, 1);
    });
  }
});

describe("API failure and fallback (no service needed)", () => {
  it("a service that is down does not stop the journey: the direct-gap scenario still ends the same way", async () => {
    const a = await app(DEAD);
    const { start, rec } = await journey(a, "direct");
    expect(a.client.getEngineMode()).toBe("fallback");
    expect(start).toBe("m3");
    expect(rec).toMatchObject({ concept_id: "diagrams", recommended_content_id: "ct_diag_walk" });
  });

  it("the follow-up flow works with the service down", async () => {
    const a = await app(DEAD);
    const { rec } = await journey(a, "direct");
    a.store.startContent(rec!.recommended_content_id, rec!.concept_id);
    await a.store.gotIt();
    const check = a.me().rechecks.find((r) => r.status === "scheduled")!;
    const res = await a.store.submitQuiz("m4", [
      { question_id: "q_p1", chosen: 0 },
      { question_id: check.question_id, chosen: null },
    ]);
    expect(res.recommendation?.repeat_gap).toBe(true);
    expect(a.client.getEngineMode()).toBe("fallback");
  });
});

describe.skipIf(!API)("service goes down and comes back during one journey", () => {
  it("falls back on the failed step and returns to the service afterwards", async () => {
    const a = await app(API);
    await a.store.finishOnboarding("some", placement(a));
    expect(a.client.getEngineMode()).toBe("api");

    const realFetch = globalThis.fetch;
    globalThis.fetch = (() => Promise.reject(new TypeError("Failed to fetch"))) as typeof fetch;
    try {
      await a.store.submitQuiz("m3", M3_DIAGRAM_GAP);
      expect(a.client.getEngineMode()).toBe("fallback");
      expect(a.me().recommendation?.concept_id).toBe("diagrams");
    } finally {
      globalThis.fetch = realFetch;
    }

    a.store.startContent("ct_diag_walk", "diagrams");
    await a.store.gotIt();
    expect(a.client.getEngineMode()).toBe("api");
  });
});
