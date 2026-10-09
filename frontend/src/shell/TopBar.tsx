import { useEffect, useRef, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { ChevronDown, FastForward, RotateCcw, Wand2 } from "lucide-react";
import { useEngineMode } from "../api/engineClient";
import { fastForward } from "../api/mockServer";
import { PRESETS, runPreset } from "./presets";

export function TopBar() {
  const engine = useEngineMode();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && setOpen(false);
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", esc);
    };
  }, [open]);

  const tabs = [
    { to: "/", label: "Overview", end: true },
    { to: "/learner", label: "Learner app" },
    { to: "/educator", label: "Trainer console" },
    { to: "/demo", label: "Side by side" },
    { to: "/flows", label: "Flow map" },
  ];

  return (
    <header className="topbar">
      <NavLink to="/" className="tb-brand" aria-label="Circuit Coach prototype home">
        <svg viewBox="0 0 28 28" width="26" height="26" aria-hidden>
          <rect x="1" y="1" width="26" height="26" rx="8" fill="var(--ink)" />
          <path d="M8 14h4l2-5 3 10 2-5h1" stroke="var(--amber)" strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span>
          Circuit <em>Coach</em>
        </span>
        <span className="tb-badge">UI prototype</span>
      </NavLink>
      <nav className="tb-tabs" aria-label="Prototype sections">
        {tabs.map((t) => (
          <NavLink key={t.to} to={t.to} end={t.end} className={({ isActive }) => "tb-tab" + (isActive ? " active" : "")}>
            {t.label}
          </NavLink>
        ))}
      </nav>
      <span className={"tb-engine tb-engine-" + engine} title="Where the knowledge-tracing steps run">
        {engine === "local" ? "Engine: in browser" : engine === "api" ? "Engine: API" : "Engine: API unreachable, using browser"}
      </span>
      <div className="tb-demo" ref={ref}>
        <button type="button" className="btn btn-secondary btn-sm" aria-expanded={open} aria-haspopup="menu" onClick={() => setOpen(!open)}>
          <Wand2 size={16} aria-hidden /> <span className="tb-demo-label">Demo scenarios</span> <ChevronDown size={16} aria-hidden />
        </button>
        {open && (
          <div className="menu" role="menu">
            <p className="menu-label">Jump to a moment in the story</p>
            {PRESETS.map((p) => (
              <button
                key={p.id}
                role="menuitem"
                type="button"
                className="menu-item"
                onClick={() => {
                  setOpen(false);
                  runPreset(p.id, nav);
                }}
              >
                <strong>{p.label}</strong>
                <span>{p.detail}</span>
              </button>
            ))}
            <div className="menu-sep" />
            <button role="menuitem" type="button" className="menu-item row" onClick={() => (fastForward(24), setOpen(false))}>
              <FastForward size={16} aria-hidden /> Skip ahead 1 day
            </button>
            <button role="menuitem" type="button" className="menu-item row" onClick={() => (setOpen(false), runPreset("fresh", nav, "/"))}>
              <RotateCcw size={16} aria-hidden /> Reset all demo data
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
