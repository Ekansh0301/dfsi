/** The browser engine must follow the same answer rules as the service (backend/circuit_coach/bkt.py). */
import { describe, expect, it } from "vitest";
import { BKT, TYPE_GUESS, bktUpdate, enoughEvidence, modelName, setItemDifficulty, setModel, trace, type EngineEvent, type ModelState } from "../engine";
import { MODULES, QUESTIONS, questionPoints } from "../../data/curriculum";

describe("question types", () => {
  it("uses the service's guess rates", () => {
    expect(TYPE_GUESS).toEqual({ true_false: 0.5, short_answer: 0.05 });
  });

  it("matches the BKT formula for a true/false answer", () => {
    const p = 0.4;
    const post = (p * (1 - BKT.pSlip)) / (p * (1 - BKT.pSlip) + (1 - p) * 0.5);
    expect(bktUpdate(p, true, false, "true_false")).toBeCloseTo(post + (1 - post) * BKT.pLearn, 10);
  });

  it("makes a right true/false answer weaker evidence than a multiple-choice one", () => {
    expect(bktUpdate(0.4, true, false, "true_false")).toBeLessThan(bktUpdate(0.4, true));
    expect(bktUpdate(0.4, true, false, "true_false")).toBeGreaterThan(0.4);
  });

  it("keeps the original update for multiple choice", () => {
    const p = 0.4;
    const post = (p * 0.9) / (p * 0.9 + (1 - p) * 0.2);
    expect(bktUpdate(p, true)).toBeCloseTo(post + (1 - post) * BKT.pLearn, 10);
  });
});

describe("curriculum", () => {
  it("has well-formed true/false questions in the module quick checks", () => {
    const tf = Object.values(QUESTIONS).filter((q) => q.type === "true_false");
    expect(tf.map((q) => q.id).sort()).toEqual(["q_e2", "q_s4"]);
    for (const q of tf) {
      expect(q.options.map((o) => o.text.en)).toEqual(["True", "False"]);
      expect(MODULES.some((m) => m.quiz.includes(q.id))).toBe(true);
    }
  });

  it("gives every question positive points", () => {
    expect(Object.values(QUESTIONS).every((q) => questionPoints(q) > 0)).toBe(true);
  });
});

describe("edge cases (same as the service, S4-1)", () => {
  it("does not recommend a lesson for a concept never answered", async () => {
    const { recommend } = await import("../engine");
    const { freshLearner } = await import("../../data/seed");
    expect(recommend(freshLearner(), ["symbols", "wiring", "diagrams"], 0)).toBeUndefined();
  });
});

const fresh = (): ModelState => ({ mastery: {}, observations: {}, tried: {} });
const wrong = (o: Partial<EngineEvent> = {}): EngineEvent => ({ concept_tags: ["ohm"], is_correct: false, unsure: false, question_type: "multiple_choice", ...o });

describe("the improved model is the default, as in the service", () => {
  it("starts on the improved model and can be switched to the baseline", () => {
    expect(modelName()).toBe("improved");
    setModel("baseline");
    expect(modelName()).toBe("baseline");
    setModel("improved");
  });

  it("credits only a question's first concept; the baseline credits every concept", () => {
    const a = fresh();
    trace(a, [wrong({ concept_tags: ["ohm", "quantities"] })]);
    expect(Object.keys(a.observations)).toEqual(["ohm"]);
    setModel("baseline");
    const b = fresh();
    trace(b, [wrong({ concept_tags: ["ohm", "quantities"] })]);
    setModel("improved");
    expect(Object.keys(b.observations).sort()).toEqual(["ohm", "quantities"]);
  });

  it("needs two answers before a lesson, unless the first one leaves mastery very low", () => {
    const l = fresh();
    l.mastery.ohm = 0.5;
    l.observations.ohm = 1;
    expect(enoughEvidence(l, "ohm")).toBe(false);
    l.mastery.ohm = 0.3;
    expect(enoughEvidence(l, "ohm")).toBe(true);
    l.observations.ohm = 2;
    l.mastery.ohm = 0.5;
    expect(enoughEvidence(l, "ohm")).toBe(true);
    expect(enoughEvidence(fresh(), "ohm")).toBe(false);
  });
});

describe("retakes and difficulty", () => {
  it("counts a retaken answer for less: attempt k moves the estimate 0.5 to the power k minus 1 as far", () => {
    const p = 0.4;
    const move = (attempt: number) => bktUpdate(p, true, false, "multiple_choice", undefined, { attempt, learn: 0 }) - p;
    expect(move(2)).toBeCloseTo(move(1) / 2, 10);
    expect(move(3)).toBeCloseTo(move(1) / 4, 10);
  });

  it("passes the attempt number through tracing", () => {
    const first = fresh();
    const second = fresh();
    trace(first, [wrong()]);
    trace(second, [wrong({ attempt_number: 2 })]);
    expect(second.mastery.ohm).not.toBe(first.mastery.ohm);
  });

  it("shifts slip and guess for a question with a known difficulty, and ignores unknown questions", () => {
    setItemDifficulty({ hard_q: 1.5 });
    const plain = fresh();
    const hard = fresh();
    const unknown = fresh();
    trace(plain, [wrong()]);
    trace(hard, [wrong({ item_id: "hard_q" })]);
    trace(unknown, [wrong({ item_id: "not_in_the_table" })]);
    setItemDifficulty({});
    expect(hard.mastery.ohm).not.toBe(plain.mastery.ohm);
    expect(unknown.mastery.ohm).toBe(plain.mastery.ohm);
  });

  it("does not use difficulty in the baseline", () => {
    setModel("baseline");
    setItemDifficulty({ hard_q: 1.5 });
    const plain = fresh();
    const hard = fresh();
    trace(plain, [wrong()]);
    trace(hard, [wrong({ item_id: "hard_q" })]);
    setItemDifficulty({});
    setModel("improved");
    expect(hard.mastery.ohm).toBe(plain.mastery.ohm);
  });
});
