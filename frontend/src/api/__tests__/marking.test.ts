/** Short answers wait for the trainer's mark, which then counts as partial credit (PLAN S4-5). */
import { afterEach, describe, expect, it, vi } from "vitest";

const API = "http://engine.test";

async function load(apiUrl?: string) {
  vi.resetModules();
  if (apiUrl) vi.stubEnv("VITE_API_URL", apiUrl);
  const store = await import("../mockServer");
  const { QUESTIONS } = await import("../../data/curriculum");
  store.applyPreset("onboarded");
  const me = () => store.getDB().learners[store.getDB().activeLearnerId];
  return { store, me, QUESTIONS };
}

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

const M2_RIGHT = [
  { question_id: "q_q1", chosen: 0 },
  { question_id: "q_q2", chosen: 0 },
  { question_id: "q_o1", chosen: 0 },
];

describe("short answers in the browser engine", () => {
  it("the demo data has one answer waiting to be marked", async () => {
    const { store } = await load();
    expect(store.getDB().marks.filter((m) => m.status === "waiting").map((m) => m.learner_id)).toEqual(["sandeep"]);
  });

  it("a written answer waits for the trainer and is left out of the model and the score", async () => {
    const { store, me } = await load();
    const before = me().observations.ohm ?? 0;
    await store.submitQuiz("m2", [...M2_RIGHT, { question_id: "q_o2", chosen: 0, text: "The current goes down, I = V / R" }]);
    const mark = store.getDB().marks.find((m) => m.learner_id === me().id)!;
    expect(mark).toMatchObject({ status: "waiting", question_id: "q_o2", concepts: ["ohm"], text: "The current goes down, I = V / R" });
    expect(me().observations.ohm).toBe(before + 1); // only q_o1 so far
    expect(me().lastQuiz!.answers.find((a) => a.question_id === "q_o2")!.pending).toBe(true);
  });

  it("'I'm not sure' on a short answer is traced at once, with nothing to mark", async () => {
    const { store, me } = await load();
    const before = me().observations.ohm ?? 0;
    await store.submitQuiz("m2", [...M2_RIGHT, { question_id: "q_o2", chosen: null }]);
    expect(store.getDB().marks.some((m) => m.learner_id === me().id)).toBe(false);
    expect(me().observations.ohm).toBe(before + 2);
  });

  it("the trainer's mark moves mastery by the mark and tells the learner", async () => {
    const { store, me } = await load();
    await store.submitQuiz("m2", [...M2_RIGHT, { question_id: "q_o2", chosen: 0, text: "it goes up" }]);
    const mark = store.getDB().marks.find((m) => m.learner_id === me().id)!;
    const before = me().mastery.ohm!;
    await store.markAnswer(mark.id, 0.25, "Look at I = V / R again.");
    expect(me().mastery.ohm!).toBeLessThan(before);
    expect(store.getDB().marks.find((m) => m.id === mark.id)).toMatchObject({ status: "marked", score: 0.25, comment: "Look at I = V / R again." });
    const msg = store.getDB().messages.find((m) => m.learner_id === me().id)!;
    expect(msg.text).toBe("Your written answer got 1 of 4 marks. Look at I = V / R again.");
  });

  it("a learner who reads Hindi gets the mark message in Hindi", async () => {
    const { store, me } = await load();
    store.getDB().learners[me().id].lang = "hi";
    await store.submitQuiz("m2", [...M2_RIGHT, { question_id: "q_o2", chosen: 0, text: "करंट कम होगा" }]);
    const mark = store.getDB().marks.find((m) => m.learner_id === me().id)!;
    await store.markAnswer(mark.id, 0.75);
    const msg = store.getDB().messages.find((m) => m.learner_id === me().id)!;
    expect(msg.text).toBe("आपके लिखे जवाब को 4 में से 3 अंक मिले।");
  });

  it("full marks raise mastery, and a mark is saved only once", async () => {
    const { store, me } = await load();
    await store.submitQuiz("m2", [...M2_RIGHT, { question_id: "q_o2", chosen: 0, text: "goes down" }]);
    const mark = store.getDB().marks.find((m) => m.learner_id === me().id)!;
    const before = me().mastery.ohm!;
    await store.markAnswer(mark.id, 1);
    const after = me().mastery.ohm!;
    expect(after).toBeGreaterThan(before);
    await store.markAnswer(mark.id, 0);
    expect(me().mastery.ohm!).toBe(after);
  });

  it("a trainer can mark another learner's answer", async () => {
    const { store } = await load();
    const before = store.getDB().learners.sandeep.mastery.ohm!;
    await store.markAnswer("mark_sandeep", 0);
    expect(store.getDB().learners.sandeep.mastery.ohm!).toBeLessThan(before);
  });
});

describe("short answers with the service", () => {
  it("quiz-result leaves the written answer out and the mark goes to /v1/marked-answer", async () => {
    const calls: { url: string; body: any }[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init: RequestInit) => {
        const body = JSON.parse(String(init.body));
        calls.push({ url, body });
        return new Response(JSON.stringify({ state: { mastery: { ohm: 0.2 }, observations: { ohm: 3 }, tried: {} }, recommendation: null }), { status: 200 });
      }),
    );
    const { store, me } = await load(API);
    await store.submitQuiz("m2", [...M2_RIGHT, { question_id: "q_o2", chosen: 0, text: "goes up" }]);
    expect(calls[0].body.events).toHaveLength(3);
    const mark = store.getDB().marks.find((m) => m.learner_id === me().id)!;
    await store.markAnswer(mark.id, 0.5);
    expect(calls[1].url).toBe(API + "/v1/marked-answer");
    expect(calls[1].body).toMatchObject({ concept_tags: ["ohm"], score: 0.5 });
    expect(me().mastery.ohm).toBe(0.2);
  });
});
