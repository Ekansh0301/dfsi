import { Link } from "react-router-dom";
import { ArrowRight, Columns2, GitFork, MonitorSmartphone, Smartphone } from "lucide-react";

const ENTRIES = [
  {
    to: "/learner",
    icon: Smartphone,
    title: "Learner app",
    body: "Mobile-first PWA. Onboarding, quick checks, one recommendation, a remedial lesson, and help from a trainer.",
  },
  {
    to: "/educator",
    icon: MonitorSmartphone,
    title: "Trainer console",
    body: "Pre-diagnosed triage queue, learner detail with a concept map, and a one-send resolution.",
  },
  { to: "/demo", icon: Columns2, title: "Side by side", body: "Both apps live at once on one shared backend. Best for the demo video." },
  { to: "/flows", icon: GitFork, title: "Flow map", body: "All four workflows as a clickable map. Jump into any screen with matching data." },
];

const CHANGES = [
  ["Working assessment", "Real questions with figures, one per screen. An “I'm not sure” option replaces guessing."],
  ["Live knowledge tracing", "A BKT engine runs in the browser behind the same API the Sprint 2 backend will serve."],
  ["Root cause, explained", "When a prerequisite is the real gap, the card says so. “Why this?” shows the chain."],
  ["Hindi + read-aloud", "Every learner screen works in Hindi or English, and every text block can be heard."],
  ["Escalation that closes", "The learner says why they're stuck, gets a confirmation, and later sees the trainer's reply in Messages."],
  ["Explainable triage", "Queue priority is shown with its reasons, and shared gaps suggest a group recap."],
  ["True spaced re-check", "The check is interleaved into a later, unrelated module. A failure raises a repeat-gap flag for the trainer."],
  ["Offline-aware content", "Lessons carry an offline badge and the app shell is cached for low-bandwidth use."],
];

const PRINCIPLES = [
  ["One screen, one action", "Every learner screen has a single primary button. Secondary options stay quiet."],
  ["Diagnose, don't score", "Learners see plain-language gaps, never probabilities. Trainers see numbers with confidence."],
  ["Never a dead end", "“I'm still stuck” is always one tap away and always reaches a human."],
  ["Low literacy first", "Large tap targets, icons with words, read-aloud, native-script language choice, optional typing."],
  ["Honest about the model", "Self-reports are verified later, and uncertainty is shown to the trainer, not hidden."],
];

export function Overview() {
  return (
    <div className="page overview">
      <section className="ov-hero">
        <p className="eyebrow">DFSI 2026 · Problem 3B · Final UI design</p>
        <h1>
          Find the gap. Give <span className="hl-amber">one</span> next step. Never leave a learner stuck.
        </h1>
        <p className="lead">
          Circuit Coach is an adaptive micro-remediation layer for vocational learners. After every quick check, it traces which concept broke down,
          prescribes one short fix, and routes unresolved confusion to a trainer.
        </p>
        <div className="ov-cta">
          <Link to="/learner" className="btn btn-primary btn-lg">
            Open learner app <ArrowRight size={18} aria-hidden />
          </Link>
          <Link to="/demo" className="btn btn-secondary btn-lg">
            Watch both sides
          </Link>
        </div>
      </section>

      <section className="ov-entries" aria-label="Prototype sections">
        {ENTRIES.map(({ to, icon: Icon, title, body }) => (
          <Link key={to} to={to} className="ov-entry">
            <span className="ov-icon">
              <Icon size={22} aria-hidden />
            </span>
            <strong>{title}</strong>
            <span className="muted small">{body}</span>
            <span className="ov-go">
              Open <ArrowRight size={14} aria-hidden />
            </span>
          </Link>
        ))}
      </section>

      <div className="ov-cols">
        <section>
          <h2>Design principles</h2>
          <ul className="ov-list">
            {PRINCIPLES.map(([h, b]) => (
              <li key={h}>
                <strong>{h}</strong>
                <span className="muted">{b}</span>
              </li>
            ))}
          </ul>
        </section>
        <section>
          <h2>What's new since the Sprint 1 mock</h2>
          <ul className="ov-list numbered">
            {CHANGES.map(([h, b]) => (
              <li key={h}>
                <strong>{h}</strong>
                <span className="muted">{b}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="ov-scope">
        <h2>Scope of this prototype</h2>
        <p className="muted">
          Per the sprint plan, this is a communication and design tool, not a production frontend: no login, user management or admin dashboards. The
          knowledge-tracing engine is simulated in the browser (<code>src/engine</code>) behind a mock API (<code>src/api/mockServer.ts</code>) whose
          request and response shapes match the Design Doc §5 contract. In Sprint 2 the FastAPI service takes its place without screen changes. All
          learners, trainers and batches are fictional demo data.
        </p>
      </section>
    </div>
  );
}
