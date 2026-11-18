/**
 * The browser engine must answer exactly like the service. `parity_cases.json` holds journeys
 * recorded from the running API (`backend/scripts/export_parity_cases.py`): onboarding, quick
 * checks, "Got it!", repeat gaps and marked answers, under both models and with per-question
 * difficulty. Each is replayed here step by step.
 */
import { afterEach, describe, expect, it } from "vitest";
import cases from "./parity_cases.json";
import { CONCEPT_ORDER, MODULES } from "../../data/curriculum";
import {
  learnStep,
  masteryOf,
  onboardingPrior,
  recommend,
  recommendRepeat,
  setItemDifficulty,
  setModel,
  startModule,
  trace,
  type EngineEvent,
  type ModelName,
  type ModelState,
} from "../engine";

type Rec = Record<string, unknown> | null;
interface Step {
  op: { op: string; [k: string]: unknown };
  state: ModelState;
  recommendation?: Rec;
  start_module_id?: string;
}
interface Case {
  model: ModelName;
  difficulty: Record<string, number>;
  steps: Step[];
}

const toEvent = (e: Record<string, unknown>): EngineEvent => ({
  concept_tags: e.concept_tags as EngineEvent["concept_tags"],
  is_correct: e.is_correct as boolean,
  unsure: (e.unsure as boolean | undefined) ?? false,
  question_type: (e.question_type as EngineEvent["question_type"] | undefined) ?? "multiple_choice",
  score: e.score as number | undefined,
  attempt_number: (e.attempt_number as number | undefined) ?? 1,
  item_id: e.item_id as string | undefined,
});

function expectState(got: ModelState, want: ModelState) {
  expect(Object.keys(got.mastery).sort()).toEqual(Object.keys(want.mastery).sort());
  for (const [c, v] of Object.entries(want.mastery)) expect(got.mastery[c as keyof typeof got.mastery]).toBeCloseTo(v as number, 9);
  expect(got.observations).toEqual(want.observations);
  expect(got.tried).toEqual(want.tried);
}

function expectRec(got: ReturnType<typeof recommend>, want: Rec) {
  if (want === null) return expect(got).toBeUndefined();
  expect(got).toBeDefined();
  expect({ ...got, strong_concept_id: got!.strong_concept_id ?? null }).toEqual(want);
}

afterEach(() => {
  setModel("improved");
  setItemDifficulty({});
});

describe("browser engine against recorded service journeys", () => {
  it("has journeys for both models, with difficulty, repeat gaps and marked answers", () => {
    const all = cases.cases as unknown as Case[];
    expect(new Set(all.map((c) => c.model))).toEqual(new Set(["improved", "baseline"]));
    expect(all.some((c) => Object.keys(c.difficulty).length > 0)).toBe(true);
    const ops = new Set(all.flatMap((c) => c.steps.map((s) => s.op.op)));
    expect(ops).toEqual(new Set(["onboard", "quiz", "got_it", "marked"]));
  });

  (cases.cases as unknown as Case[]).forEach((c, i) => {
    it(`journey ${i} (${c.model}, ${c.steps.length} steps)`, () => {
      setModel(c.model);
      setItemDifficulty(c.difficulty);
      const l: ModelState = { mastery: {}, observations: {}, tried: {} };
      for (const step of c.steps) {
        const op = step.op;
        if (op.op === "onboard") {
          l.mastery = Object.fromEntries(CONCEPT_ORDER.map((k) => [k, onboardingPrior(op.experience as string)]));
          l.observations = {};
          l.tried = {};
          trace(l, (op.events as Record<string, unknown>[]).map(toEvent));
          expect(startModule(l)).toBe(step.start_module_id);
        } else if (op.op === "quiz") {
          trace(l, (op.events as Record<string, unknown>[]).map(toEvent));
          const mod = MODULES.find((m) => m.id === op.module_id)!;
          const rec = op.recheck_concept ? recommendRepeat(l, op.recheck_concept as never, 1_700_000_000_000) : recommend(l, mod.concepts, 1_700_000_000_000);
          expectRec(rec, step.recommendation ?? null);
        } else if (op.op === "got_it") {
          const k = op.concept_id as keyof typeof l.mastery;
          l.mastery[k] = learnStep(masteryOf(l, k), k);
          const done = (l.tried[k] ??= []);
          if (!done.includes(op.content_id as string)) done.push(op.content_id as string);
        } else {
          const tags = op.concept_tags as string[];
          trace(l, [
            { concept_tags: tags as never, is_correct: (op.score as number) >= 0.5, unsure: false, question_type: "short_answer", score: op.score as number, attempt_number: op.attempt_number as number, item_id: op.item_id as string },
          ]);
          expectRec(recommend(l, CONCEPT_ORDER.filter((k) => tags.includes(k)), 1_700_000_000_000), step.recommendation ?? null);
        }
        expectState(l, step.state);
      }
    });
  });
});
