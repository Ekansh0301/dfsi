import type { ConceptId, DB, Escalation, LearnerState } from "../api/types";

/** Demo data only: fictional learners in a fictional electrician batch. */
export const COHORT = "Electrician batch B · Sep 2026";
export const EDUCATOR = { name: "Kavitha M.", role: "Trainer" };
export const ACTIVE_ID = "asha";
/** Bump when seed data or the DB shape changes, so stale browser data is replaced. */
export const DB_VERSION = 5;

const H = 3600_000;

type M = Partial<Record<ConceptId, number>>;

function learner(id: string, name: string, mastery: M, module: string, completed: string[]): LearnerState {
  const observations: Partial<Record<ConceptId, number>> = {};
  for (const k of Object.keys(mastery) as ConceptId[]) observations[k] = 3 + (name.length % 4);
  return {
    id,
    name,
    cohort: COHORT,
    lang: "en",
    onboarded: true,
    track: "electrical",
    experience: "some",
    mastery,
    observations,
    confirmed: [],
    completedModules: completed,
    currentModule: module,
    responses: [],
    tried: {},
    rechecks: [],
  };
}

export function freshLearner(): LearnerState {
  return {
    id: ACTIVE_ID,
    name: "Asha Reddy",
    cohort: COHORT,
    lang: "en",
    onboarded: false,
    mastery: {},
    observations: {},
    confirmed: [],
    completedModules: [],
    currentModule: "m1",
    responses: [],
    tried: {},
    rechecks: [],
  };
}

export function seedDB(now: number): DB {
  const others: LearnerState[] = [
    learner(
      "imran",
      "Imran Shaikh",
      { safety: 0.9, quantities: 0.82, ohm: 0.55, symbols: 0.84, wiring: 0.8, diagrams: 0.71, series_parallel: 0.32 },
      "m4",
      ["m1", "m2", "m3"],
    ),
    learner("lakshmi", "Lakshmi Prasanna", { safety: 0.93, quantities: 0.74, ohm: 0.69, symbols: 0.62, wiring: 0.38, diagrams: 0.45 }, "m3", [
      "m1",
      "m2",
    ]),
    learner("sandeep", "Sandeep Naik", { safety: 0.88, quantities: 0.61, ohm: 0.41 }, "m2", ["m1"]),
    learner(
      "divya",
      "Divya Rao",
      { safety: 0.95, quantities: 0.9, ohm: 0.86, symbols: 0.9, wiring: 0.83, diagrams: 0.78, series_parallel: 0.52 },
      "m4",
      ["m1", "m2", "m3"],
    ),
    learner(
      "farhan",
      "Farhan Ali",
      { safety: 0.91, quantities: 0.85, ohm: 0.79, symbols: 0.88, wiring: 0.86, diagrams: 0.81, series_parallel: 0.84, multimeter: 0.72 },
      "m5",
      ["m1", "m2", "m3", "m4"],
    ),
    learner("meena", "Meena Kumari", { safety: 0.86, quantities: 0.7, ohm: 0.58, symbols: 0.66, wiring: 0.72 }, "m3", ["m1", "m2"]),
  ];
  others.find((l) => l.id === "lakshmi")!.tried = { wiring: ["ct_wiring_walk"] };
  others.find((l) => l.id === "imran")!.tried = { series_parallel: ["ct_sp_walk"] };
  others.find((l) => l.id === "sandeep")!.tried = { ohm: ["ct_ohm_walk"] };
  others.find((l) => l.id === "sandeep")!.lang = "hi";

  const escalations: Escalation[] = [
    {
      id: "esc_imran",
      learner_id: "imran",
      concept_id: "series_parallel",
      prior_attempts: [{ content_id: "ct_sp_walk", at: now - 1.2 * H, outcome: "stuck" }],
      reason: "need_example",
      note: "I get series but parallel ke loops confusing hai",
      repeat_gap: false,
      timestamp: now - 1.1 * H,
      status: "open",
    },
    {
      id: "esc_lakshmi",
      learner_id: "lakshmi",
      concept_id: "wiring",
      prior_attempts: [
        { content_id: "ct_wiring_walk", at: now - 30 * H, outcome: "stuck" },
        { content_id: "ct_wiring_practice", at: now - 20 * H, outcome: "recheck_failed" },
      ],
      reason: "unclear",
      repeat_gap: true,
      timestamp: now - 20 * H,
      status: "open",
    },
    {
      id: "esc_sandeep",
      learner_id: "sandeep",
      concept_id: "ohm",
      prior_attempts: [{ content_id: "ct_ohm_walk", at: now - 3.5 * H, outcome: "stuck" }],
      reason: "language",
      note: "",
      repeat_gap: false,
      timestamp: now - 3.4 * H,
      status: "open",
    },
    {
      id: "esc_divya",
      learner_id: "divya",
      concept_id: "series_parallel",
      prior_attempts: [{ content_id: "ct_sp_walk", at: now - 50 * H, outcome: "stuck" }],
      reason: "need_example",
      repeat_gap: false,
      timestamp: now - 50 * H,
      status: "resolved",
      resolution: {
        tip: "Showed the two-lamp board in class. Try the worked example again.",
        assigned_content_id: "ct_sp_example",
        resolved_by: EDUCATOR.name,
        at: now - 44 * H,
      },
    },
  ];

  const learners: DB["learners"] = { [ACTIVE_ID]: freshLearner() };
  for (const l of others) learners[l.id] = l;
  return { version: DB_VERSION, clockOffset: 0, learners, escalations, messages: [], activeLearnerId: ACTIVE_ID };
}
