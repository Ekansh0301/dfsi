/** The demo presets must land where their labels say (HANDOFF.md section 5, Issue T7). */
import { describe, expect, it } from "vitest";
import { applyPreset, getDB, markAnswer, quizFor, submitQuiz, type Preset } from "../mockServer";
import { QUESTIONS } from "../../data/curriculum";
import { PRESETS } from "../../shell/presets";

const me = () => getDB().learners[getDB().activeLearnerId];

describe("demo presets", () => {
  it("gap: a direct gap on circuit diagrams", () => {
    applyPreset("gap");
    expect(me().recommendation).toMatchObject({ concept_id: "diagrams", chain: ["diagrams"], recommended_content_id: "ct_diag_walk" });
  });

  it("rootcause: diagrams are wrong because symbols are weak", () => {
    applyPreset("rootcause");
    expect(me().recommendation).toMatchObject({ concept_id: "symbols", observed_concept_id: "diagrams", chain: ["diagrams", "symbols"] });
  });

  it("escalated: the learner has tried the diagrams lesson and asked the trainer", () => {
    applyPreset("escalated");
    expect(me().tried.diagrams).toEqual(["ct_diag_walk"]);
    expect(getDB().escalations.some((e) => e.learner_id === me().id && e.concept_id === "diagrams" && e.status === "open")).toBe(true);
  });

  it("resolved: the trainer's reply carries content for the same concept", () => {
    applyPreset("resolved");
    const msg = getDB().messages.find((m) => m.learner_id === me().id)!;
    expect(msg.concept_id).toBe("diagrams");
    expect(msg.assigned_content_id).toBe("ct_diag_practice");
  });

  it("recheck: a follow-up check is due and is hidden inside the module 5 quick check", () => {
    applyPreset("recheck");
    expect(me().rechecks.filter((r) => r.status === "scheduled").map((r) => r.concept_id)).toEqual(["diagrams"]);
    const quiz = quizFor(getDB(), "m5");
    expect(quiz.recheck).toBe("diagrams");
    expect(quiz.questions).toHaveLength(4);
  });

  it("fresh and onboarded", () => {
    applyPreset("fresh");
    expect(me().onboarded).toBe(false);
    applyPreset("onboarded");
    expect(me().onboarded && me().currentModule).toBe("m3");
  });

  it("m2check: Ohm's law is borderline, so the written answer's mark decides the lesson", async () => {
    applyPreset("m2check");
    expect(me().onboarded).toBe(true);
    expect(me().mastery.ohm!).toBeLessThan(0.3);
    expect(me().recommendation).toBeUndefined();
    const right = [
      { question_id: "q_q1", chosen: QUESTIONS.q_q1.correct },
      { question_id: "q_q2", chosen: QUESTIONS.q_q2.correct },
      { question_id: "q_o1", chosen: QUESTIONS.q_o1.correct },
      { question_id: "q_o2", chosen: 0, text: "the current goes down" },
    ];
    const res = await submitQuiz("m2", right);
    expect(res.recommendation).toBeUndefined(); // the written answer is still with the trainer
    const mark = getDB().marks.find((m) => m.question_id === "q_o2")!;
    await markAnswer(mark.id, 0.25, "Look at I = V / R again.");
    expect(me().recommendation).toMatchObject({ concept_id: "ohm", recommended_content_id: "ct_ohm_walk" });
  });

  it("every preset in the top bar exists", () => {
    const ids: Preset[] = ["fresh", "onboarded", "m1check", "m2check", "gap", "rootcause", "escalated", "resolved", "recheck"];
    expect(PRESETS.map((p) => p.id).sort()).toEqual([...ids].sort());
    for (const p of PRESETS) expect(() => applyPreset(p.id)).not.toThrow();
  });
});
