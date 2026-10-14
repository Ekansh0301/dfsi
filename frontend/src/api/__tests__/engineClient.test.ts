/**
 * The prototype talks to the engine service when VITE_API_URL is set and falls back to the
 * in-browser engine when the service is missing, failing or slow (Issue T4).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const API = "http://engine.test";

type Call = { url: string; body: any };
let calls: Call[] = [];

/** Load fresh copies of the client and the store, so the env var is read again. */
async function load(apiUrl?: string) {
  vi.resetModules();
  if (apiUrl) vi.stubEnv("VITE_API_URL", apiUrl);
  const client = await import("../engineClient");
  const store = await import("../mockServer");
  store.resetDemo();
  return { client, store, me: () => store.getDB().learners[store.getDB().activeLearnerId] };
}

/** A fetch that answers like the service, recording every request. */
function serviceFetch(reply: (path: string, body: any) => unknown) {
  return vi.fn(async (url: string, init: RequestInit) => {
    const body = JSON.parse(String(init.body));
    calls.push({ url, body });
    return new Response(JSON.stringify(reply(url.replace(API, ""), body)), { status: 200 });
  });
}

const PLACEMENT_RIGHT = ["q_x_saf4", "q_x_q3", "q_x_ohm2", "q_x_sym2", "q_x_wir2", "q_x_mm2"];
const M3 = ["q_w1", "q_w2", "q_w3", "q_w4", "q_w5"];

beforeEach(() => {
  calls = [];
});
afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("without VITE_API_URL", () => {
  it("uses the in-browser engine and never calls the network", async () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    const { client, store, me } = await load();
    const { QUESTIONS } = await import("../../data/curriculum");
    expect(client.getEngineMode()).toBe("local");

    await store.finishOnboarding("some", PLACEMENT_RIGHT.map((id) => ({ question_id: id, chosen: QUESTIONS[id].correct })));
    const res = await store.submitQuiz("m3", M3.map((id) => ({ question_id: id, chosen: null })));

    expect(fetch).not.toHaveBeenCalled();
    expect(client.getEngineMode()).toBe("local");
    expect(me().onboarded).toBe(true);
    expect(res.recommendation).toBeDefined();
  });
});

describe("with VITE_API_URL", () => {
  it("sends onboarding, quiz result and Got it! to the service and uses its answers", async () => {
    const state = { mastery: { symbols: 0.31, diagrams: 0.22 }, observations: { symbols: 2, diagrams: 2 }, tried: {} };
    const recommendation = {
      concept_id: "symbols",
      observed_concept_id: "diagrams",
      chain: ["diagrams", "symbols"],
      strong_concept_id: null,
      diagnostic_text: { en: "from the service", hi: "from the service" },
      recommended_content_id: "ct_sym_cards",
      repeat_gap: false,
      created_at: 1,
    };
    vi.stubGlobal(
      "fetch",
      serviceFetch((path) => {
        if (path === "/v1/onboarding") return { state, start_module_id: "m3" };
        if (path === "/v1/quiz-result") return { state, recommendation };
        return { state: { ...state, mastery: { ...state.mastery, symbols: 0.42 } } };
      }),
    );
    const { client, store, me } = await load(API + "/");

    await store.finishOnboarding("new", [{ question_id: "q_x_sym2", chosen: null }]);
    expect(calls[0].url).toBe(API + "/v1/onboarding");
    expect(calls[0].body).toEqual({ experience: "new", events: [{ concept_tags: ["symbols"], is_correct: false, unsure: true }] });
    expect(me().currentModule).toBe("m3");
    expect(me().mastery).toEqual(state.mastery);
    expect(client.getEngineMode()).toBe("api");

    const res = await store.submitQuiz("m3", [{ question_id: "q_w3", chosen: null }]);
    expect(calls[1].url).toBe(API + "/v1/quiz-result");
    expect(calls[1].body).toMatchObject({ module_id: "m3", events: [{ concept_tags: ["diagrams", "symbols"], is_correct: false, unsure: true }] });
    expect(calls[1].body.state).toHaveProperty("mastery");
    expect(calls[1].body.recheck_concept).toBeUndefined();
    expect(res.recommendation?.diagnostic_text.en).toBe("from the service");
    expect(res.recommendation?.strong_concept_id).toBeUndefined();

    store.startContent("ct_sym_cards", "symbols");
    await store.gotIt();
    expect(calls[2].url).toBe(API + "/v1/got-it");
    expect(calls[2].body.concept_id).toBe("symbols");
    expect(calls[2].body.state.tried).toEqual({ symbols: ["ct_sym_cards"] });
    expect(me().mastery.symbols).toBe(0.42);
    expect(me().rechecks.some((r) => r.concept_id === "symbols" && r.status === "scheduled")).toBe(true);
  });

  it("sends a failed re-check as recheck_concept", async () => {
    vi.stubGlobal("fetch", serviceFetch(() => ({ state: { mastery: {}, observations: {}, tried: {} }, recommendation: null })));
    const { store, me } = await load(API);
    store.applyPreset("gap");
    await store.gotIt();
    const rc = me().rechecks.find((r) => r.status === "scheduled")!;
    await store.submitQuiz("m4", [{ question_id: "q_p1", chosen: 0 }, { question_id: rc.question_id, chosen: null }]);
    const quiz = calls.filter((c) => c.url.endsWith("/v1/quiz-result")).pop()!;
    expect(quiz.body.recheck_concept).toBe(rc.concept_id);
  });
});

describe("fallback to the in-browser engine", () => {
  async function runFlow(apiUrl?: string) {
    const { client, store, me } = await load(apiUrl);
    const { QUESTIONS } = await import("../../data/curriculum");
    const start = await store.finishOnboarding("some", PLACEMENT_RIGHT.map((id) => ({ question_id: id, chosen: QUESTIONS[id].correct })));
    const res = await store.submitQuiz("m3", M3.map((id) => ({ question_id: id, chosen: null })));
    return { client, store, me, start, res };
  }

  it("keeps the flow working when the service is unreachable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const { client, me, start, res } = await runFlow(API);
    expect(client.getEngineMode()).toBe("fallback");
    expect(start).toBeTruthy();
    expect(me().onboarded).toBe(true);
    expect(res.recommendation?.recommended_content_id).toMatch(/^ct_/);
  });

  it("falls back on an error status", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("boom", { status: 500 })));
    const { client, res } = await runFlow(API);
    expect(client.getEngineMode()).toBe("fallback");
    expect(res.recommendation).toBeDefined();
  });

  it("gives the same answer the browser engine gives on its own", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const fallback = await runFlow(API);
    const fallbackMastery = structuredClone(fallback.me().mastery);
    vi.unstubAllEnvs();
    const local = await runFlow();
    expect(fallback.res.recommendation?.concept_id).toBe(local.res.recommendation?.concept_id);
    expect(fallbackMastery).toEqual(local.me().mastery);
  });

  it("gives up on a call that takes longer than 4 seconds", async () => {
    vi.useFakeTimers();
    const hang = vi.fn(
      (_url: string, init: RequestInit) =>
        new Promise<Response>((_, reject) => init.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")))),
    );
    vi.stubGlobal("fetch", hang);
    const { client, store, me } = await load(API);
    const done = store.finishOnboarding("new", []);
    await vi.advanceTimersByTimeAsync(5000);
    await done;
    expect(hang).toHaveBeenCalledTimes(1);
    expect(client.getEngineMode()).toBe("fallback");
    expect(me().onboarded).toBe(true);
  });

  it("returns to API mode once the service answers again", async () => {
    let up = false;
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        if (!up) throw new TypeError("Failed to fetch");
        return new Response(JSON.stringify({ state: { mastery: {}, observations: {}, tried: {} }, start_module_id: "m1" }), { status: 200 });
      }),
    );
    const { client, store } = await load(API);
    await store.finishOnboarding("new", []);
    expect(client.getEngineMode()).toBe("fallback");
    up = true;
    await store.finishOnboarding("new", []);
    expect(client.getEngineMode()).toBe("api");
  });
});
