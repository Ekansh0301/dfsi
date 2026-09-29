import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Code2, Cpu, NotebookPen, X } from "lucide-react";
import { LearnerApp } from "../learner/LearnerApp";
import { ANNOTATIONS, FLOW_LABEL, type ScreenKey } from "./annotations";
import { useCurrentScreen } from "./screenStore";
import { runPreset } from "./presets";

/** Desktop: learner app inside a phone frame, with live design notes. Phones: the app full-bleed. */
export function LearnerFrame() {
  const [notesOpen, setNotesOpen] = useState(false);
  return (
    <div className="lframe">
      <div className="phone" aria-label="Learner app (phone preview)">
        <div className="phone-screen">
          <LearnerApp />
        </div>
      </div>
      <aside className={"notes" + (notesOpen ? " open" : "")} aria-label="Design notes">
        <button type="button" className="icon-btn notes-close" onClick={() => setNotesOpen(false)} aria-label="Close notes">
          <X size={18} aria-hidden />
        </button>
        <Notes />
      </aside>
      <button type="button" className="notes-fab" onClick={() => setNotesOpen(true)} aria-label="Show design notes">
        <NotebookPen size={20} aria-hidden />
      </button>
    </div>
  );
}

export function Notes() {
  const key = useCurrentScreen();
  const a = ANNOTATIONS[key];
  const nav = useNavigate();
  const siblings = (Object.keys(ANNOTATIONS) as ScreenKey[]).filter((k) => ANNOTATIONS[k].flow === a.flow && !k.startsWith("e-"));
  return (
    <div className="notes-inner" aria-live="polite">
      <p className="notes-flow">{FLOW_LABEL[a.flow]}</p>
      <div className="notes-title">
        <span className="code">{a.code}</span>
        <h2>{a.name}</h2>
      </div>
      <p className="notes-stage">
        UX stage: <strong>{a.stage}</strong>
      </p>
      <p className="notes-why">{a.why}</p>
      {a.system && (
        <div className="notes-box">
          <p className="nb-h">
            <Cpu size={14} aria-hidden /> Behind the screen
          </p>
          <p>{a.system}</p>
        </div>
      )}
      {a.api && (
        <div className="notes-box mono">
          <p className="nb-h">
            <Code2 size={14} aria-hidden /> API (Sprint 2)
          </p>
          <code>{a.api}</code>
        </div>
      )}
      {siblings.length > 1 && (
        <div className="notes-jump">
          <p className="nb-h">Screens in this flow</p>
          <p className="small muted">Jumping loads a matching demo scenario.</p>
          <div className="jump-list">
            {siblings.map((k) => {
              const s = ANNOTATIONS[k];
              return (
                <button
                  key={k}
                  type="button"
                  className={"jump" + (k === key ? " on" : "")}
                  onClick={() => (s.preset ? runPreset(s.preset, nav, s.route) : nav(s.route))}
                  title={s.name}
                >
                  <span className="code">{s.code}</span> {s.name}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
