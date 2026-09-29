import { applyPreset, type Preset } from "../api/mockServer";

export const PRESETS: { id: Preset; label: string; detail: string; route: string }[] = [
  { id: "fresh", label: "New learner (cold start)", detail: "No history yet → onboarding", route: "/learner/welcome" },
  { id: "onboarded", label: "Onboarded, starting Module 3", detail: "Placement done, Modules 1 and 2 skipped", route: "/learner/home" },
  { id: "gap", label: "Gap diagnosed: circuit diagrams", detail: "Module 3 check just submitted", route: "/learner/results" },
  { id: "rootcause", label: "Root cause is a prerequisite", detail: "Diagrams wrong because symbols are weak", route: "/learner/next" },
  { id: "escalated", label: "Learner escalated to trainer", detail: "“I'm still stuck” was tapped", route: "/educator" },
  { id: "resolved", label: "Trainer replied", detail: "Tip, new content and a check-in in Messages", route: "/learner/messages" },
  { id: "recheck", label: "Spaced re-check is due", detail: "Hidden inside the Module 5 quick check", route: "/learner/home" },
];

export function runPreset(id: Preset, navigate: (to: string) => void, to?: string) {
  applyPreset(id);
  navigate(to ?? PRESETS.find((p) => p.id === id)!.route);
}
