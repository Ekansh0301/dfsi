import type { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { ArrowLeft, ChartNoAxesColumn, House, MessageCircle, Pause, Volume2 } from "lucide-react";
import { setLang } from "../api/mockServer";
import { speak, speechSupported, stopSpeaking, useSpeaking } from "../lib/speech";
import { useT } from "../lib/i18n";
import { useDB, useMe } from "../lib/store";

/** Read-aloud button. Every learner-facing block of text can be heard. */
export function Listen({ id, text, compact = false }: { id: string; text: string; compact?: boolean }) {
  const { t, lang } = useT();
  const on = useSpeaking(id);
  if (!speechSupported) return null;
  return (
    <button
      type="button"
      className={"listen" + (on ? " on" : "") + (compact ? " compact" : "")}
      onClick={() => (on ? stopSpeaking() : speak(id, text, lang))}
      aria-pressed={on}
      aria-label={on ? t("stop") : t("listen")}
    >
      {on ? <Pause size={18} aria-hidden /> : <Volume2 size={18} aria-hidden />}
      {!compact && <span>{on ? t("stop") : t("listen")}</span>}
    </button>
  );
}

export function LangToggle() {
  const { t, lang } = useT();
  return (
    <button type="button" className="lang-toggle" onClick={() => setLang(lang === "en" ? "hi" : "en")} lang={lang === "en" ? "hi" : "en"}>
      {t("lang_switch")}
    </button>
  );
}

/** Top bar. `back` shows a back arrow; otherwise the brand mark. */
export function AppBar({ back, title, right }: { back?: string | number; title?: ReactNode; right?: ReactNode }) {
  const nav = useNavigate();
  const { t } = useT();
  return (
    <header className="appbar">
      {back !== undefined ? (
        <button type="button" className="icon-btn ghost" onClick={() => (typeof back === "number" ? nav(back) : nav(back))} aria-label={t("back")}>
          <ArrowLeft size={22} aria-hidden />
        </button>
      ) : (
        <div className="brandmark" aria-label={t("app_name")}>
          <svg viewBox="0 0 28 28" width="28" height="28" aria-hidden>
            <rect x="1" y="1" width="26" height="26" rx="8" fill="var(--ink)" />
            <path d="M8 14h4l2-5 3 10 2-5h1" stroke="var(--amber)" strokeWidth="2.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span>{t("app_name")}</span>
        </div>
      )}
      <div className="appbar-title">{title}</div>
      <div className="appbar-right">{right ?? <LangToggle />}</div>
    </header>
  );
}

export function BottomNav() {
  const { t } = useT();
  const unread = useDB((d) => d.messages.filter((m) => m.learner_id === d.activeLearnerId && !m.read).length);
  const items = [
    { to: "/learner/home", icon: House, label: t("nav_home") },
    { to: "/learner/progress", icon: ChartNoAxesColumn, label: t("nav_progress") },
    { to: "/learner/messages", icon: MessageCircle, label: t("nav_messages"), badge: unread },
  ];
  return (
    <nav className="bottomnav" aria-label="Main">
      {items.map(({ to, icon: Icon, label, badge }) => (
        <NavLink key={to} to={to} className={({ isActive }) => "bn-item" + (isActive ? " active" : "")}>
          <span className="bn-icon">
            <Icon size={24} aria-hidden />
            {!!badge && (
              <span className="badge" aria-label={`${badge} new`}>
                {badge}
              </span>
            )}
          </span>
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}

/** Screen scaffold: app bar, scrollable body, optional sticky footer and bottom nav. */
export function Screen({
  bar,
  children,
  footer,
  nav = false,
  className = "",
}: {
  bar?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  nav?: boolean;
  className?: string;
}) {
  const me = useMe();
  return (
    <div className={"screen " + className} lang={me.lang}>
      {bar ?? <AppBar />}
      <main className="screen-body">{children}</main>
      {footer && <div className="screen-footer">{footer}</div>}
      {nav && <BottomNav />}
    </div>
  );
}

export function Progress({ value, total, label }: { value: number; total: number; label: string }) {
  return (
    <div className="segbar" role="progressbar" aria-valuemin={0} aria-valuemax={total} aria-valuenow={value} aria-label={label}>
      {Array.from({ length: total }, (_, i) => (
        <span key={i} className={i < value ? "on" : i === value ? "cur" : ""} />
      ))}
    </div>
  );
}
