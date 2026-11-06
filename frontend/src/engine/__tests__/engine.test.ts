/** The browser engine must follow the same answer rules as the service (backend/circuit_coach/bkt.py). */
import { describe, expect, it } from "vitest";
import { BKT, TYPE_GUESS, bktUpdate } from "../engine";
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
