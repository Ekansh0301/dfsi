import { useEffect } from "react";
import { HashRouter, Link, NavLink, Navigate, Route, Routes } from "react-router-dom";
import { ArrowLeftRight, ChartNoAxesColumn, House, MessageCircle } from "lucide-react";
import { checkHealth, useEngineMode } from "../api/engineClient";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { moduleById } from "../data/curriculum";
import { EducatorApp } from "../educator/EducatorApp";
import { LearnerApp } from "../learner/LearnerApp";
import { useT } from "../lib/i18n";
import { useDB, useMe } from "../lib/store";
import "../styles/webapp.css";

/**
 * The responsive web app: the same learner app and trainer console as the prototype, without the
 * prototype's top bar, phone frame or design notes. Opened with `?app=1` (for example
 * `/?app=1#/learner`). It shares the one backend with the prototype, so a learner tab and a
 * trainer tab update each other live.
 *
 * Phones: the learner app full-screen with its bottom navigation, as before.
 * Tablets: the same screens in a centred column.
 * Laptops and desktops: a side navigation, wider content, lessons with the picture beside the text.
 */
export function WebApp() {
  useEffect(() => {
    void checkHealth();
  }, []);
  return (
    <HashRouter>
      <ErrorBoundary>
        <Routes>
          <Route path="/learner/*" element={<LearnerWeb />} />
          <Route path="/educator/*" element={<TrainerWeb />} />
          <Route path="*" element={<Navigate to="/learner" replace />} />
        </Routes>
      </ErrorBoundary>
    </HashRouter>
  );
}

function LearnerWeb() {
  return (
    <div className="webapp wa-learner">
      <LearnerSide />
      <div className="wa-main">
        <LearnerApp />
      </div>
    </div>
  );
}

function LearnerSide() {
  const { t, tx } = useT();
  const me = useMe();
  const unread = useDB((d) => d.messages.filter((m) => m.learner_id === d.activeLearnerId && !m.read).length);
  const items = [
    { to: "/learner/home", icon: House, label: t("nav_home") },
    { to: "/learner/progress", icon: ChartNoAxesColumn, label: t("nav_progress") },
    { to: "/learner/messages", icon: MessageCircle, label: t("nav_messages"), badge: unread },
  ];
  const m = moduleById(me.currentModule);
  return (
    <aside className="wa-side" lang={me.lang}>
      <Brand />
      {me.onboarded ? (
        <>
          <div className="wa-me">
            <span className="wa-avatar" aria-hidden>
              {me.name
                .split(/\s+/)
                .map((p) => p[0])
                .join("")}
            </span>
            <span>
              <strong>{me.name}</strong>
              <span className="small muted">
                {t("track_electrical")} · {t("module_n", { n: m.number })}
              </span>
            </span>
          </div>
          <nav className="wa-nav" aria-label={t("nav_main")}>
            {items.map(({ to, icon: Icon, label, badge }) => (
              <NavLink key={to} to={to} className={({ isActive }) => "wa-nav-item" + (isActive ? " active" : "")}>
                <Icon size={20} aria-hidden />
                <span>{label}</span>
                {!!badge && (
                  <span className="badge" aria-label={t("n_new", { n: badge })}>
                    {badge}
                  </span>
                )}
              </NavLink>
            ))}
          </nav>
          <div className="wa-module small muted">
            <span className="tag tag-plain">{t("module_n", { n: m.number })}</span> {tx(m.title)}
          </div>
        </>
      ) : (
        <p className="small muted">{t("welcome_body")}</p>
      )}
      <div className="wa-side-foot">
        <Link to="/educator" className="wa-switch-link">
          <ArrowLeftRight size={16} aria-hidden /> Trainer view
        </Link>
        <EngineNote />
      </div>
    </aside>
  );
}

function TrainerWeb() {
  return (
    <div className="webapp wa-trainer">
      <EducatorApp />
      <Link to="/learner/home" className="wa-switch">
        <ArrowLeftRight size={16} aria-hidden /> Learner view
      </Link>
    </div>
  );
}

function Brand() {
  return (
    <div className="wa-brand">
      <svg viewBox="0 0 28 28" width="30" height="30" aria-hidden>
        <rect x="1" y="1" width="26" height="26" rx="8" fill="var(--ink)" />
        <path d="M8 14h4l2-5 3 10 2-5h1" stroke="var(--amber)" strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span>
        Circuit <em>Coach</em>
      </span>
    </div>
  );
}

function EngineNote() {
  const engine = useEngineMode();
  const label =
    engine === "api" ? "Engine: online" : engine === "checking" ? "Engine: checking…" : engine === "fallback" ? "Engine: offline, using this device" : "Engine: on this device";
  return <span className={"wa-engine wa-engine-" + engine}>{label}</span>;
}
