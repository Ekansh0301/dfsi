import { Link } from "react-router-dom";
import { ArrowRight, Columns2, GitFork, MonitorSmartphone, Smartphone } from "lucide-react";

const ENTRIES = [
  {
    to: "/learner",
    icon: Smartphone,
    title: "Learner app",
    body: "Mobile-first, in Hindi or English. Onboarding, quick checks with multiple choice, true/false and written answers, one recommendation, a lesson that can be read aloud, and help from a trainer.",
  },
  {
    to: "/educator",
    icon: MonitorSmartphone,
    title: "Trainer console",
    body: "Triage queue with reasons, learner detail with a concept map, written answers to mark, and a one-send resolution.",
  },
  { to: "/demo", icon: Columns2, title: "Side by side", body: "Both apps live at once on shared learner data. Best for the demo video." },
  {
    to: "/flows",
    icon: GitFork,
    title: "Flow map",
    body: "The learner and trainer workflows as a clickable map. Jump into any screen with matching data.",
  },
];

const CHANGES = [
  [
    "Barabari's quiz format",
    "Multiple choice, true/false and short answers with points. A true/false answer is weaker evidence than a multiple-choice one, and retakes count for less.",
  ],
  [
    "Trainer marking",
    "A written answer waits in the trainer's “To mark” list. The mark becomes partial credit in the model, and the learner gets it in Messages in their own language.",
  ],
  [
    "A real engine behind it",
    "A Python service runs Bayesian Knowledge Tracing and the prerequisite walk. The top bar shows which engine is answering, and the app falls back to its in-browser engine if the service is down.",
  ],
  ["Listen button", "Questions, lesson steps and the recommendation can be read aloud in Hindi or English with the voices on the device."],
  ["Works without signal", "Install it on a phone and keep studying offline. An unfinished quiz is kept if the page closes."],
  ["Bands, not percentages", "Mastery is shown as Needs work, Getting there or Strong, because the estimates run high in the middle range."],
  [
    "Measured, not just shown",
    "On simulated learners the improved model finds the hidden root cause 58% of the time against 49% for the baseline. It is tested end to end, and it has been checked against plain accuracy.",
  ],
];

const PRINCIPLES = [
  ["One screen, one action", "Every learner screen has a single primary button. Secondary options stay quiet."],
  ["Diagnose, don't score", "Learners see plain-language gaps, never probabilities. Trainers see numbers with confidence."],
  ["Never a dead end", "“I'm still stuck” is always one tap away and always reaches a human."],
  ["Low literacy first", "Large tap targets, icons with words, native-script language choice, a listen button, optional typing."],
  ["Honest about the model", "Self-reports are verified later, and uncertainty is shown to the trainer, not hidden."],
];

export function Overview() {
  return (
    <div className="page overview">
      <section className="ov-hero">
        <p className="eyebrow">DFSI 2026 · Problem 3B · POC v1.0</p>
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
          <h2>What's new in v1.0</h2>
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
          This is a proof of concept, not a production product: no login, user management or admin dashboards. The knowledge-tracing engine runs as a
          Python service (<code>backend/</code>) that this site calls when it is configured to; otherwise, or if the service is down, the same logic
          runs in the browser (<code>src/engine</code>). Learner records and escalations are kept in the browser, and all learners, trainers and
          batches are fictional demo data. The results behind the numbers come from simulated learners and EdNet, not from learners at Barabari or
          Nirmaan.
        </p>
      </section>
    </div>
  );
}
