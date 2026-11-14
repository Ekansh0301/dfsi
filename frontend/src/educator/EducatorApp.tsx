import { useMemo, useState } from "react";
import { Link, NavLink, Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  BadgeCheck,
  CalendarClock,
  ChevronRight,
  Inbox,
  Languages,
  Lightbulb,
  ListChecks,
  MessageSquareText,
  PenLine,
  RotateCcw,
  Send,
  TriangleAlert,
  Users,
} from "lucide-react";
import { cohortGaps, markAnswer, now, priorityOf, resolveEscalation } from "../api/mockServer";
import type { DB, Escalation, StuckReason } from "../api/types";
import { CONCEPTS, QUESTIONS, moduleById } from "../data/curriculum";
import { CONTENT, contentFor } from "../data/content";
import { COHORT, EDUCATOR } from "../data/seed";
import { band, confidence, masteryOf, rootCause } from "../engine/engine";
import { BAND_LABEL, ConceptMap, SHORT } from "../components/ConceptMap";
import { useDB } from "../lib/store";
import { useMarkScreen } from "../shell/screenStore";

const REASON: Record<StuckReason, string> = {
  unclear: "The lesson wasn't clear",
  need_example: "Needs a real example",
  language: "Wants it in their language",
  other: "Something else",
};

const initials = (name: string) =>
  name
    .split(/\s+/)
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

function ago(ms: number) {
  const m = Math.max(1, Math.round(ms / 60000));
  if (m < 60) return `${m} min ago`;
  const h = Math.round(m / 60);
  if (h < 24) return `${h} h ago`;
  return `${Math.round(h / 24)} d ago`;
}

export function EducatorApp() {
  const open = useDB((d) => d.escalations.filter((e) => e.status === "open").length);
  const toMark = useDB((d) => d.marks.filter((m) => m.status === "waiting").length);
  return (
    <div className="edu">
      <aside className="edu-rail">
        <div className="edu-brand">
          <svg viewBox="0 0 28 28" width="28" height="28" aria-hidden>
            <rect x="1" y="1" width="26" height="26" rx="8" fill="var(--amber)" />
            <path d="M8 14h4l2-5 3 10 2-5h1" stroke="var(--on-amber)" strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <div>
            <strong>Circuit Coach</strong>
            <span>Trainer console</span>
          </div>
        </div>
        <nav className="edu-nav" aria-label="Trainer">
          <NavLink to="/educator" end className={({ isActive }) => (isActive ? "active" : "")}>
            <Inbox size={18} aria-hidden /> Needs you
            {open > 0 && <span className="count">{open}</span>}
          </NavLink>
          <NavLink to="/educator/marking" className={({ isActive }) => (isActive ? "active" : "")}>
            <PenLine size={18} aria-hidden /> To mark
            {toMark > 0 && <span className="count">{toMark}</span>}
          </NavLink>
          <NavLink to="/educator/resolved" className={({ isActive }) => (isActive ? "active" : "")}>
            <ListChecks size={18} aria-hidden /> Resolved
          </NavLink>
        </nav>
        <div className="edu-me">
          <span className="avatar">KM</span>
          <div>
            <strong>{EDUCATOR.name}</strong>
            <span>{COHORT}</span>
          </div>
        </div>
      </aside>
      <main className="edu-main">
        <Routes>
          <Route index element={<Queue />} />
          <Route path="case/:id" element={<Case />} />
          <Route path="marking" element={<Marking />} />
          <Route path="resolved" element={<Resolved />} />
          <Route path="*" element={<Navigate to="/educator" replace />} />
        </Routes>
      </main>
    </div>
  );
}

// ─── E4 · Short answers to mark (Barabari's instructor review) ────────────────

const MARKS = [
  { score: 0, label: "0" },
  { score: 0.25, label: "1/4" },
  { score: 0.5, label: "1/2" },
  { score: 0.75, label: "3/4" },
  { score: 1, label: "Full" },
];

function Marking() {
  useMarkScreen("e-marking");
  const d = useDB();
  const waiting = d.marks.filter((m) => m.status === "waiting");
  const marked = d.marks.filter((m) => m.status === "marked").slice(0, 5);
  return (
    <div className="edu-page">
      <header className="edu-head">
        <div>
          <h1>To mark</h1>
          <p className="muted">Written answers from quick checks. Your mark counts as partial credit in the learner's model.</p>
        </div>
      </header>
      {waiting.length === 0 ? (
        <div className="edu-card empty">
          <BadgeCheck size={28} aria-hidden />
          <p>Nothing to mark right now.</p>
        </div>
      ) : (
        <div className="mark-list">
          {waiting.map((m) => (
            <MarkCard key={m.id} id={m.id} />
          ))}
        </div>
      )}
      {marked.length > 0 && (
        <section className="edu-card">
          <h2 className="card-h">Recently marked</h2>
          <ul className="plain-list">
            {marked.map((m) => (
              <li key={m.id}>
                <strong>{d.learners[m.learner_id].name}</strong> · {CONCEPTS[m.concepts[0]].name.en} ·{" "}
                {MARKS.find((x) => x.score === m.score)?.label ?? m.score} marks
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function MarkCard({ id }: { id: string }) {
  const d = useDB();
  const m = d.marks.find((x) => x.id === id)!;
  const q = QUESTIONS[m.question_id];
  const l = d.learners[m.learner_id];
  const [score, setScore] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  return (
    <article className="edu-card mark-card" data-mark={m.id}>
      <div className="mark-who">
        <span className="avatar">{initials(l.name)}</span>
        <div>
          <strong>{l.name}</strong>
          <span className="muted small">
            {moduleById(m.module_id).title.en} · {CONCEPTS[m.concepts[0]].name.en} · {ago(now(d) - m.at)}
          </span>
        </div>
      </div>
      <p className="mark-q">{q.prompt.en}</p>
      <blockquote className="quote">{m.text}</blockquote>
      <p className="small muted">
        <Lightbulb size={14} aria-hidden /> Model answer: {q.why.en}
      </p>
      <div className="mark-scale" role="radiogroup" aria-label="Mark">
        {MARKS.map((x) => (
          <button
            key={x.label}
            type="button"
            role="radio"
            aria-checked={score === x.score}
            className={"suggest" + (score === x.score ? " on" : "")}
            onClick={() => setScore(x.score)}
          >
            {x.label}
          </button>
        ))}
      </div>
      <textarea
        className="textarea"
        rows={2}
        placeholder="Optional note to the learner"
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        aria-label="Note to the learner"
      />
      <button
        type="button"
        className="btn btn-primary"
        disabled={score === null || busy}
        onClick={async () => {
          setBusy(true);
          await markAnswer(m.id, score!, comment.trim());
        }}
      >
        <Send size={16} aria-hidden /> {busy ? "Saving…" : "Save mark"}
      </button>
    </article>
  );
}

// ─── E1 · Triage queue ───────────────────────────────────────────────────────
function Queue() {
  useMarkScreen("e-queue");
  const d = useDB();
  const rows = d.escalations
    .filter((e) => e.status === "open")
    .map((e) => ({ e, p: priorityOf(e, d) }))
    .sort((a, b) => b.p.score - a.p.score);
  const gaps = cohortGaps(d);

  return (
    <div className="edu-page">
      <header className="edu-head">
        <div>
          <h1>Learners who need you</h1>
          <p className="muted">{rows.length} open · sorted by priority. Only cases the app could not resolve on its own appear here.</p>
        </div>
      </header>
      <div className="edu-grid">
        <section aria-label="Open escalations">
          {rows.length === 0 ? (
            <div className="edu-card empty">
              <BadgeCheck size={32} aria-hidden />
              <p>Nobody is stuck right now. New requests appear here the moment a learner taps “I'm still stuck”.</p>
            </div>
          ) : (
            <ul className="triage">
              {rows.map(({ e, p }) => (
                <TriageRow key={e.id} e={e} p={p} d={d} />
              ))}
            </ul>
          )}
        </section>
        <aside className="edu-side">
          <div className="edu-card">
            <h2 className="card-h">
              <Users size={18} aria-hidden /> Common gaps in this batch
            </h2>
            {gaps.length === 0 ? (
              <p className="muted small">No shared gaps yet.</p>
            ) : (
              <ul className="gap-list">
                {gaps.slice(0, 4).map((g) => (
                  <li key={g.concept}>
                    <div className="gl-top">
                      <span>{CONCEPTS[g.concept].name.en}</span>
                      <strong>
                        {g.weak.length}/{g.observed}
                      </strong>
                    </div>
                    <div className="gl-bar">
                      <span style={{ width: `${(g.weak.length / Math.max(1, g.observed)) * 100}%` }} />
                    </div>
                    <p className="small muted">{g.weak.map((id) => d.learners[id].name.split(" ")[0]).join(", ")}</p>
                  </li>
                ))}
              </ul>
            )}
            {gaps[0] && gaps[0].weak.length >= 3 && (
              <p className="hint-box">
                <Lightbulb size={16} aria-hidden /> {gaps[0].weak.length} learners share “{CONCEPTS[gaps[0].concept].name.en}”. A 10-minute group
                recap may help more than one-to-one fixes.
              </p>
            )}
          </div>
          <div className="edu-card">
            <h2 className="card-h">How priority is set</h2>
            <ol className="small prio-rules">
              <li>
                <strong>Repeat gap:</strong> the learner said “Got it” but failed the spaced re-check.
              </li>
              <li>
                <strong>Fixes tried:</strong> each content item that didn't work.
              </li>
              <li>
                <strong>Waiting time:</strong> older requests rise slowly.
              </li>
            </ol>
          </div>
        </aside>
      </div>
    </div>
  );
}

function TriageRow({ e, p, d }: { e: Escalation; p: ReturnType<typeof priorityOf>; d: DB }) {
  const l = d.learners[e.learner_id];
  return (
    <li>
      <Link to={`/educator/case/${e.id}`} className={"triage-row prio-" + p.level}>
        <span className="avatar lg">{initials(l.name)}</span>
        <div className="tr-main">
          <div className="tr-top">
            <strong>{l.name}</strong>
            <span className={"prio prio-" + p.level}>{p.level === "high" ? "High" : p.level === "medium" ? "Medium" : "Normal"}</span>
          </div>
          <p className="tr-concept">{CONCEPTS[e.concept_id].name.en}</p>
          <p className="small muted tr-quote">{e.note ? `“${e.note}”` : e.reason ? REASON[e.reason] : "Re-check failed (auto-flagged)"}</p>
          <div className="chips">
            {p.reasons.map((r) => (
              <span key={r.en} className={"tag " + (r.en === "Repeat gap" ? "tag-rust" : "tag-plain")}>
                {r.en === "Repeat gap" && <RotateCcw size={12} aria-hidden />}
                {r.en === "Language barrier" && <Languages size={12} aria-hidden />}
                {r.en}
              </span>
            ))}
          </div>
        </div>
        <div className="tr-right">
          <span className="small muted">{ago(now(d) - e.timestamp)}</span>
          <ChevronRight size={20} aria-hidden />
        </div>
      </Link>
    </li>
  );
}

// ─── E2 · Learner detail & resolution ────────────────────────────────────────
type Two = { en: string; hi: string };
const TIPS: Partial<Record<string, Two[]>> = {
  diagrams: [
    {
      en: "Use two fingers: one stays on +, the other walks the wire. If it can't get back to −, the lamp is off.",
      hi: "दो उँगलियाँ लगाइए: एक + पर रहे, दूसरी तार के साथ चले। अगर वह − तक वापस न पहुँचे, तो बल्ब बंद रहेगा।",
    },
    {
      en: "Redraw the circuit as a real board. Every line on paper is one wire on the board.",
      hi: "सर्किट को असली बोर्ड की तरह फिर से बनाइए। कागज़ की हर लाइन बोर्ड का एक तार है।",
    },
  ],
  series_parallel: [
    {
      en: "Count the paths back to the cell: one path = series, more than one = parallel.",
      hi: "सेल तक वापस जाने के रास्ते गिनिए: एक रास्ता = सीरीज़, एक से ज़्यादा = पैरेलल।",
    },
    {
      en: "Try the two-lamp board in the lab. Unscrew one bulb and see which one stays on.",
      hi: "लैब में दो बल्ब वाला बोर्ड आज़माइए। एक बल्ब खोलिए और देखिए कौन-सा जलता रहता है।",
    },
  ],
  wiring: [
    {
      en: "Remember: the switch cuts the phase, so the holder is safe when it's OFF.",
      hi: "याद रखिए: स्विच फेज़ को काटता है, इसलिए OFF होने पर होल्डर सुरक्षित रहता है।",
    },
    {
      en: "Colour check: red/brown = phase, black/blue = neutral, green = earth.",
      hi: "रंग याद रखिए: लाल/भूरा = फेज़, काला/नीला = न्यूट्रल, हरा = अर्थ।",
    },
  ],
  ohm: [
    {
      en: "Cover the letter you need in the V-I-R triangle. What's left is the formula.",
      hi: "V-I-R त्रिकोण में जो अक्षर चाहिए उसे ढकिए। जो बचे, वही फ़ॉर्मूला है।",
    },
    {
      en: "Try it with money: ₹12 shared by 6 people = ₹2 each. Same as 12 V ÷ 6 Ω = 2 A.",
      hi: "पैसों से समझिए: ₹12 को 6 लोगों में बाँटें = हर एक को ₹2। वैसे ही 12 V ÷ 6 Ω = 2 A।",
    },
  ],
  symbols: [
    { en: "Make flashcards: symbol on one side, real part on the other.", hi: "फ़्लैशकार्ड बनाइए: एक तरफ़ चिह्न, दूसरी तरफ़ असली पुर्ज़ा।" },
    {
      en: "Find each symbol on the lab board. Touch the real part when you name it.",
      hi: "लैब बोर्ड पर हर चिह्न ढूँढिए। नाम लेते समय असली पुर्ज़े को छुइए।",
    },
  ],
};
const DEFAULT_TIP: Two = { en: "Let's go through this together at the next class.", hi: "अगली क्लास में हम इसे साथ में समझेंगे।" };
const CHECKINS: Two[] = [
  { en: "Today, 16:00 in the lab", hi: "आज, 16:00 बजे लैब में" },
  { en: "Tomorrow, 10:00 in the lab", hi: "कल, 10:00 बजे लैब में" },
  { en: "Next class, before the practical", hi: "अगली क्लास में, प्रैक्टिकल से पहले" },
];

function Case() {
  useMarkScreen("e-case");
  const { id } = useParams();
  const d = useDB();
  const nav = useNavigate();
  const e = d.escalations.find((x) => x.id === id);
  const [tip, setTip] = useState("");
  const [content, setContent] = useState<string>("");
  const [checkin, setCheckin] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState("");
  const l = e ? d.learners[e.learner_id] : undefined;
  const chain = useMemo(() => (l && e ? rootCause(l, e.concept_id) : []), [l, e]);

  if (!e || !l) return <Navigate to="/educator" replace />;
  const p = priorityOf(e, d);
  const c = CONCEPTS[e.concept_id];
  const pct = Math.round(masteryOf(l, e.concept_id) * 100);
  const conf = confidence(l, e.concept_id);
  const items = contentFor(e.concept_id);
  const tried = new Set([...(l.tried[e.concept_id] ?? []), ...e.prior_attempts.map((a) => a.content_id)]);
  const canSend = e.status === "open" && (tip.trim() || content || checkin);
  const first = l.name.split(" ")[0];

  const send = async () => {
    setBusy(true);
    await resolveEscalation(e.id, { tip: tip.trim() || undefined, assigned_content_id: content || undefined, checkin: checkin || undefined });
    setToast(`Sent to ${first}. Case resolved.`);
    setTimeout(() => nav("/educator"), 1100);
  };

  return (
    <div className="edu-page">
      <Link to="/educator" className="back-link">
        <ArrowLeft size={16} aria-hidden /> Needs you
      </Link>
      <header className="case-head">
        <span className="avatar xl">{initials(l.name)}</span>
        <div>
          <h1>{l.name}</h1>
          <p className="muted small">
            {l.cohort} · Module {moduleById(l.currentModule).number} · prefers {l.lang === "hi" ? "Hindi" : "English"} · escalated{" "}
            {ago(now(d) - e.timestamp)}
          </p>
          <div className="chips">
            <span className={"prio prio-" + p.level}>{p.level === "high" ? "High" : p.level === "medium" ? "Medium" : "Normal"} priority</span>
            {p.reasons.map((r) => (
              <span key={r.en} className={"tag " + (r.en === "Repeat gap" ? "tag-rust" : "tag-plain")}>
                {r.en}
              </span>
            ))}
          </div>
        </div>
      </header>

      <div className="case-grid">
        <div className="case-col">
          <section className="edu-card">
            <h2 className="card-h">
              <TriangleAlert size={18} aria-hidden /> What the app saw
            </h2>
            <div className="diag">
              <div>
                <p className="small muted">Stuck on</p>
                <p className="diag-concept">{c.name.en}</p>
              </div>
              <div className="diag-meter">
                <div className="dm-top">
                  <span className="small muted">Estimated mastery</span>
                  <strong title={`Estimate ${pct}%`}>{BAND_LABEL[band(l, e.concept_id)]}</strong>
                </div>
                <div className="gl-bar">
                  <span style={{ width: `${pct}%` }} className={pct < 60 ? "low" : ""} />
                </div>
                <p className="small muted">
                  Confidence: <strong>{conf}</strong> ({l.observations[e.concept_id] ?? 0} answers)
                </p>
              </div>
            </div>
            <div className="prereqs">
              <p className="small muted">Prerequisites</p>
              <ul>
                {c.prereqs.map((pr) => {
                  const b = band(l, pr);
                  return (
                    <li key={pr} className={b === "practice" ? "weak" : ""}>
                      <span>{CONCEPTS[pr].name.en}</span>
                      <strong title={l.observations[pr] ? `Estimate ${Math.round(masteryOf(l, pr) * 100)}%` : undefined}>{BAND_LABEL[b]}</strong>
                    </li>
                  );
                })}
              </ul>
              {chain.length > 1 && (
                <p className="hint-box">
                  <Lightbulb size={16} aria-hidden /> The underlying gap may be <strong>{CONCEPTS[chain[chain.length - 1]].name.en}</strong>.
                </p>
              )}
            </div>
          </section>

          <section className="edu-card">
            <h2 className="card-h">Already tried</h2>
            <ol className="timeline">
              {e.prior_attempts.map((a, i) => {
                const it = CONTENT[a.content_id];
                return (
                  <li key={i}>
                    <span className={"tl-dot " + a.outcome} aria-hidden />
                    <div>
                      <p>
                        <strong>{it?.title.en ?? a.content_id}</strong>{" "}
                        <span className="small muted">
                          · {it?.kind} · {it?.minutes} min
                        </span>
                      </p>
                      <p className="small">
                        {a.outcome === "stuck" ? (
                          <span className="tag tag-rust">Tapped “I'm still stuck”</span>
                        ) : (
                          <span className="tag tag-rust">Said “Got it”, then failed the re-check</span>
                        )}{" "}
                        <span className="muted">{ago(now(d) - a.at)}</span>
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>
          </section>

          <section className="edu-card">
            <h2 className="card-h">
              <MessageSquareText size={18} aria-hidden /> In their words
            </h2>
            <p>
              <span className="tag tag-plain">{e.reason ? REASON[e.reason] : "Auto-flagged after failed re-check"}</span>
            </p>
            {e.note && <blockquote className="quote">“{e.note}”</blockquote>}
          </section>
        </div>

        <aside className="case-col resolve">
          {e.status === "resolved" ? (
            <section className="edu-card">
              <h2 className="card-h">
                <BadgeCheck size={18} aria-hidden /> Resolved
              </h2>
              <p className="small">{e.resolution?.tip}</p>
            </section>
          ) : (
            <section className="edu-card sticky" aria-labelledby="resolve-h">
              <h2 id="resolve-h" className="card-h">
                How do you want to help {first}?
              </h2>

              <fieldset className="rs-block">
                <legend>1 · Send a tip</legend>
                <textarea
                  className="textarea"
                  rows={3}
                  value={tip}
                  onChange={(ev) => setTip(ev.target.value)}
                  placeholder={`A short, practical hint for ${first}…`}
                />
                <div className="chips">
                  {(TIPS[e.concept_id] ?? [DEFAULT_TIP]).map((two) => {
                    // The tip is sent in the learner's language; the trainer also sees the English.
                    const s = two[l.lang];
                    return (
                      <button key={two.en} type="button" className="suggest" title={two.en} onClick={() => setTip(s)}>
                        <span lang={l.lang}>{s.length > 52 ? s.slice(0, 50) + "…" : s}</span>
                      </button>
                    );
                  })}
                </div>
              </fieldset>

              <fieldset className="rs-block">
                <legend>2 · Assign different content</legend>
                <div className="radio-list">
                  {items.map((it) => (
                    <label key={it.id} className={"radio-row" + (content === it.id ? " on" : "")}>
                      <input type="radio" name="content" checked={content === it.id} onChange={() => setContent(it.id)} />
                      <span>
                        <strong>{it.title.en}</strong>
                        <span className="small muted">
                          {" "}
                          · {it.kind} · {it.minutes} min
                        </span>
                      </span>
                      {tried.has(it.id) && <span className="tag tag-plain">Tried</span>}
                    </label>
                  ))}
                  <label className={"radio-row" + (content === "" ? " on" : "")}>
                    <input type="radio" name="content" checked={content === ""} onChange={() => setContent("")} />
                    <span className="muted">No new content</span>
                  </label>
                </div>
              </fieldset>

              <fieldset className="rs-block">
                <legend>3 · Plan a check-in</legend>
                <div className="chips">
                  {CHECKINS.map((two) => {
                    const s = two[l.lang];
                    return (
                      <button
                        key={two.en}
                        type="button"
                        className={"suggest" + (checkin === s ? " on" : "")}
                        aria-pressed={checkin === s}
                        title={two.en}
                        onClick={() => setCheckin(checkin === s ? "" : s)}
                      >
                        <CalendarClock size={14} aria-hidden /> <span lang={l.lang}>{s}</span>
                      </button>
                    );
                  })}
                </div>
              </fieldset>

              {canSend && (
                <div className="preview">
                  <p className="small muted">{first} will see</p>
                  <div className="preview-msg">
                    {tip.trim() && <p>{tip.trim()}</p>}
                    {content && <p className="tag">Open: {CONTENT[content].title.en}</p>}
                    {checkin && <p className="tag tag-blue">Meet: {checkin}</p>}
                  </div>
                </div>
              )}

              <button type="button" className="btn btn-primary btn-block btn-lg" disabled={!canSend || busy} onClick={send}>
                <Send size={18} aria-hidden /> {busy ? "Sending…" : "Send & mark resolved"}
              </button>
              <p className="small muted center">The flag clears and {first} is routed back into their normal flow.</p>
            </section>
          )}
        </aside>
      </div>
      <section className="edu-card">
        <h2 className="card-h">Concept map · {first}</h2>
        <div className="cmap-wrap">
          <ConceptMap learner={l} focus={e.concept_id} chain={chain} />
        </div>
        <p className="small muted">
          Arrows point from a prerequisite to the concept that builds on it. Each box shows a band (Needs work, Getting there or Strong); hover for
          the estimate.
        </p>
      </section>
      {toast && (
        <div className="toast" role="status">
          <BadgeCheck size={18} aria-hidden /> {toast}
        </div>
      )}
    </div>
  );
}

// ─── E3 · Resolved log ───────────────────────────────────────────────────────
function Resolved() {
  useMarkScreen("e-resolved");
  const d = useDB();
  const rows = d.escalations.filter((e) => e.status === "resolved").sort((a, b) => (b.resolution?.at ?? 0) - (a.resolution?.at ?? 0));
  return (
    <div className="edu-page">
      <header className="edu-head">
        <div>
          <h1>Resolved</h1>
          <p className="muted">What worked, and for whom. This log becomes evaluation data for which interventions close which gaps.</p>
        </div>
      </header>
      <div className="edu-card table-card">
        <table className="table">
          <thead>
            <tr>
              <th>Learner</th>
              <th>Concept</th>
              <th>What you did</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((e) => {
              const r = e.resolution!;
              return (
                <tr key={e.id}>
                  <td>
                    <span className="avatar sm">{initials(d.learners[e.learner_id].name)}</span> {d.learners[e.learner_id].name}
                  </td>
                  <td>{SHORT[e.concept_id]}</td>
                  <td>
                    <div className="chips">
                      {r.tip && <span className="tag tag-plain">Tip</span>}
                      {r.assigned_content_id && <span className="tag">{CONTENT[r.assigned_content_id].title.en}</span>}
                      {r.checkin && <span className="tag tag-blue">{r.checkin}</span>}
                    </div>
                  </td>
                  <td className="muted small">{ago(now(d) - r.at)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
