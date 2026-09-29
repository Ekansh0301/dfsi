import { useState } from "react";
import { applyPreset, type Preset } from "../api/mockServer";
import { PRESETS } from "./presets";

/**
 * Learner phone and trainer console running at once, sharing one mock backend
 * (localStorage + storage events). Tapping "I'm still stuck" on the left shows up on
 * the right, and the trainer's reply lands in the learner's Messages.
 */
export function SideBySide() {
  const [k, setK] = useState(0);
  const [learnerPath, setLearnerPath] = useState("/learner");
  const base = window.location.pathname;
  const go = (id: Preset) => {
    applyPreset(id);
    const p = PRESETS.find((x) => x.id === id)!;
    setLearnerPath(p.route.startsWith("/learner") ? p.route : "/learner/home");
    setK(k + 1);
  };
  return (
    <div className="sbs">
      <div className="sbs-bar">
        <p>
          <strong>Live demo.</strong> Both apps share one simulated backend. Try: learner taps <em>I'm still stuck</em> → the case appears for the
          trainer → the trainer's reply lands in the learner's Messages.
        </p>
        <div className="sbs-presets">
          {(["gap", "escalated", "recheck"] as Preset[]).map((id) => (
            <button key={id} type="button" className="btn btn-secondary btn-sm" onClick={() => go(id)}>
              {PRESETS.find((p) => p.id === id)!.label}
            </button>
          ))}
        </div>
      </div>
      <div className="sbs-stage">
        <div className="sbs-phone">
          <p className="sbs-label">Learner · phone</p>
          <div className="phone">
            <div className="phone-screen">
              <iframe key={"l" + k} title="Learner app" src={`${base}?embed=1#${learnerPath}`} />
            </div>
          </div>
        </div>
        <div className="sbs-edu">
          <p className="sbs-label">Trainer · tablet / laptop</p>
          <div className="sbs-window">
            <iframe key={"e" + k} title="Trainer console" src={`${base}?embed=1#/educator`} />
          </div>
        </div>
      </div>
    </div>
  );
}
