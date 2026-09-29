import { Fragment } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, CornerDownRight } from "lucide-react";
import type { Preset } from "../api/mockServer";
import { ANNOTATIONS, type ScreenKey } from "./annotations";
import { runPreset } from "./presets";

interface Lane {
  title: string;
  kicker: string;
  tone: "amber" | "rust" | "blue" | "teal";
  steps: (ScreenKey | { system: string } | { screen: ScreenKey; preset: Preset; route: string; label?: string })[];
  branch?: { from: string; text: string };
}

const LANES: Lane[] = [
  {
    title: "A · Cold-start onboarding",
    kicker: "First-time learner, no history",
    tone: "blue",
    steps: ["welcome", "track", "experience", "placement", { system: "Seed P(L₀) per concept" }, "start", "home"],
  },
  {
    title: "B · Learner journey (happy path)",
    kicker: "Primary workflow: the four core screens",
    tone: "amber",
    steps: ["home", "quiz", { system: "BKT update + root-cause search" }, "results", "next", "learn", "gotit"],
    branch: { from: "S4", text: "“I'm still stuck” → lane C. Never auto-retried." },
  },
  {
    title: "C · Escalation & resolution",
    kicker: "The human safety net",
    tone: "rust",
    steps: ["stuck", "helpsent", { system: "Escalation event, priority scored" }, "e-queue", "e-case", "messages", "learn"],
  },
  {
    title: "D · Spaced re-assessment",
    kicker: "“Got it!” is not trusted outright",
    tone: "teal",
    steps: [
      "gotit",
      { system: "Schedule unseen item for that concept" },
      { screen: "quiz", preset: "recheck", route: "/learner/quiz/m5", label: "Module 5 check + hidden re-check" },
      "results",
      "progress",
    ],
    branch: { from: "S2", text: "Failed re-check → S3 marked “repeat gap” + trainer auto-flagged (high priority)." },
  },
];

export function FlowMap() {
  const nav = useNavigate();
  const open = (k: ScreenKey, preset?: Preset, route?: string) => {
    const a = ANNOTATIONS[k];
    const p = preset ?? a.preset;
    if (p) runPreset(p, nav, route ?? a.route);
    else nav(route ?? a.route);
  };
  return (
    <div className="page flows">
      <header className="page-head">
        <p className="eyebrow">Flow map</p>
        <h1>Every screen, every path</h1>
        <p className="lead">
          Four flows from the Sprint 1 design doc, now fully clickable. Grey boxes are the system working behind the screens. Click any screen to open
          it with matching demo data.
        </p>
      </header>
      <div className="lanes">
        {LANES.map((lane) => (
          <section key={lane.title} className={"lane tone-" + lane.tone}>
            <div className="lane-head">
              <h2>{lane.title}</h2>
              <p className="muted small">{lane.kicker}</p>
            </div>
            <ol className="lane-steps">
              {lane.steps.map((s, i) => (
                <Fragment key={i}>
                  {i > 0 && (
                    <li className="lane-arrow" aria-hidden>
                      <ArrowRight size={18} />
                    </li>
                  )}
                  {typeof s === "string" ? (
                    <li>
                      <button type="button" className="fnode" onClick={() => open(s)}>
                        <span className="code">{ANNOTATIONS[s].code}</span>
                        <strong>{ANNOTATIONS[s].name}</strong>
                        <span className="small muted">{ANNOTATIONS[s].stage}</span>
                      </button>
                    </li>
                  ) : "screen" in s ? (
                    <li>
                      <button type="button" className="fnode" onClick={() => open(s.screen, s.preset, s.route)}>
                        <span className="code">{ANNOTATIONS[s.screen].code}</span>
                        <strong>{s.label ?? ANNOTATIONS[s.screen].name}</strong>
                        <span className="small muted">{ANNOTATIONS[s.screen].stage}</span>
                      </button>
                    </li>
                  ) : (
                    <li>
                      <div className="fnode system">
                        <span className="code">SYS</span>
                        <strong>{s.system}</strong>
                      </div>
                    </li>
                  )}
                </Fragment>
              ))}
            </ol>
            {lane.branch && (
              <p className="lane-branch small">
                <CornerDownRight size={16} aria-hidden /> <strong>{lane.branch.from}:</strong> {lane.branch.text}
              </p>
            )}
          </section>
        ))}
      </div>
    </div>
  );
}
