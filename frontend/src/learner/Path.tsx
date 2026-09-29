import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { BadgeCheck, CalendarClock, Check, MessageCircle } from "lucide-react";
import { markMessagesRead, setRecommendationFromMessage } from "../api/mockServer";
import { CONCEPTS, MODULES } from "../data/curriculum";
import { CONTENT } from "../data/content";
import { band, type Band } from "../engine/engine";
import { useT, type StrKey } from "../lib/i18n";
import { useDB, useMe } from "../lib/store";
import { useMarkScreen } from "../shell/screenStore";
import { Screen } from "./ui";

const BAND_KEY: Record<Band, StrKey> = { strong: "band_strong", getting: "band_getting", practice: "band_practice", new: "band_new" };

export function BandMeter({ b }: { b: Band }) {
  const lvl = b === "strong" ? 3 : b === "getting" ? 2 : b === "practice" ? 1 : 0;
  return (
    <span className={"band-meter b-" + b} aria-hidden>
      {[1, 2, 3].map((i) => (
        <span key={i} className={i <= lvl ? "on" : ""} />
      ))}
    </span>
  );
}

// ─── P · My skill path ───────────────────────────────────────────────────────
export function ProgressScreen() {
  useMarkScreen("progress");
  const { t, tx } = useT();
  const me = useMe();
  return (
    <Screen nav>
      <h1 className="title">{t("progress_title")}</h1>
      <p className="muted">{t("progress_body")}</p>
      <ol className="path">
        {MODULES.map((m) => {
          const done = me.completedModules.includes(m.id);
          const now = m.id === me.currentModule && !done;
          const skipped = done && !me.responses.some((r) => r.module_id === m.id);
          const status = skipped ? t("st_skipped") : done ? t("st_done") : now ? t("st_now") : t("st_next");
          return (
            <li key={m.id} className={"path-node" + (done ? " done" : "") + (now ? " now" : "")}>
              <span className="pn-dot" aria-hidden>
                {done ? <Check size={16} /> : m.number}
              </span>
              <div className="pn-body">
                <div className="pn-head">
                  <h2 className="pn-title">
                    {t("module_n", { n: m.number })} · {tx(m.title)}
                  </h2>
                  <span className={"tag " + (now ? "" : done ? "tag-teal" : "tag-plain")}>{status}</span>
                </div>
                <ul className="concept-rows">
                  {m.concepts.map((c) => {
                    const b = band(me, c);
                    const conf = me.confirmed.includes(c);
                    return (
                      <li key={c}>
                        <span className="cr-name">{tx(CONCEPTS[c].name)}</span>
                        <span className="cr-state">
                          {conf ? (
                            <span className="tag tag-teal">
                              <BadgeCheck size={14} aria-hidden /> {t("confirmed")}
                            </span>
                          ) : (
                            <>
                              <BandMeter b={b} />
                              <span className="small">{t(BAND_KEY[b])}</span>
                            </>
                          )}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            </li>
          );
        })}
      </ol>
    </Screen>
  );
}

// ─── M · Messages ────────────────────────────────────────────────────────────
export function Messages() {
  useMarkScreen("messages");
  const { t, tx, lang } = useT();
  const nav = useNavigate();
  const msgs = useDB((d) => d.messages.filter((m) => m.learner_id === d.activeLearnerId));
  const hasUnread = msgs.some((m) => !m.read);
  useEffect(() => {
    if (!hasUnread) return;
    const id = setTimeout(markMessagesRead, 1500);
    return () => clearTimeout(id);
  }, [hasUnread]);

  return (
    <Screen nav>
      <h1 className="title">{t("messages_title")}</h1>
      {msgs.length === 0 ? (
        <div className="empty">
          <MessageCircle size={36} aria-hidden />
          <p className="muted">{t("no_messages")}</p>
        </div>
      ) : (
        <ul className="msg-list">
          {msgs.map((m) => {
            const item = m.assigned_content_id ? CONTENT[m.assigned_content_id] : undefined;
            return (
              <li key={m.id} className={"msg" + (m.read ? "" : " unread")}>
                <div className="msg-head">
                  <span className="avatar">KM</span>
                  <div>
                    <p className="msg-from">{m.from}</p>
                    <p className="small muted">
                      {t("about_topic", { c: tx(CONCEPTS[m.concept_id].name) })} ·{" "}
                      {new Date(m.at).toLocaleString(lang === "hi" ? "hi-IN" : "en-IN", { weekday: "short", hour: "numeric", minute: "2-digit" })}
                    </p>
                  </div>
                </div>
                {m.text && (
                  <p className="msg-text" lang="en">
                    {m.text}
                  </p>
                )}
                {m.checkin && (
                  <p className="tag tag-blue">
                    <CalendarClock size={14} aria-hidden /> {t("checkin", { x: m.checkin })}
                  </p>
                )}
                {item && (
                  <button
                    type="button"
                    className="btn btn-primary btn-block btn-split"
                    onClick={() => {
                      setRecommendationFromMessage(m.id);
                      nav(`/learner/learn/${item.id}`);
                    }}
                  >
                    <span>{t("open_x", { title: tx(item.title) })}</span>
                    <span className="hint">{t("min", { m: item.minutes })}</span>
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </Screen>
  );
}
