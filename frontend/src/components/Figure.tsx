import type { ReactNode } from "react";
import type { FigureId } from "../api/types";

interface Props {
  id: FigureId;
  /** `true` closes every switch; an array closes only those switch parts (e.g. ["s1"]). */
  closed?: boolean | string[];
  highlight?: string[];
  /** Show lit lamps for closed loops. Off for quiz figures, so the figure does not give the answer away. */
  live?: boolean;
  title?: string;
  className?: string;
}

const ALT: Record<FigureId, string> = {
  "sym-switch": "Switch symbol: a line with a gap",
  "sym-lamp": "Lamp symbol: a circle with a cross",
  "sym-cell": "Cell symbol: a long and a short line",
  "sym-resistor": "Resistor symbol: a small rectangle",
  "circuit-simple": "Circuit: a cell, a switch and a lamp in one loop",
  "circuit-series": "Circuit: a cell, a switch and two lamps in series",
  "circuit-parallel": "Circuit: a cell and a switch feeding two lamps in parallel branches",
  "circuit-two-switch": "Circuit: two branches, S1 with lamp L1 and S2 with lamp L2",
  "meter-dial": "Multimeter dial with AC voltage, DC voltage, resistance and current settings",
};

/** Hand-drawn IEC-style circuit figures. Parts carry `data-part` names used for highlighting. */
export function Figure({ id, closed = false, highlight = [], live = true, title, className = "" }: Props) {
  const isClosed = (sw: string) => closed === true || (Array.isArray(closed) && closed.includes(sw));
  const hl = new Set(highlight);
  const P = ({ name, children }: { name: string; children: ReactNode }) => (
    <g data-part={name} className={"part" + (hl.has(name) ? " hl" : "")}>
      {children}
    </g>
  );
  const Switch = ({ name, x, y, label }: { name: string; x: number; y: number; label?: string }) => (
    <P name={name}>
      <rect className="halo" x={x - 8} y={y - 30} width={56} height={44} rx={10} />
      <circle cx={x} cy={y} r={3.5} fill="currentColor" />
      <circle cx={x + 40} cy={y} r={3.5} fill="currentColor" />
      {isClosed(name) ? <line x1={x} y1={y} x2={x + 40} y2={y} /> : <line x1={x} y1={y} x2={x + 36} y2={y - 20} />}
      {label && (
        <text x={x + 20} y={y + 24} textAnchor="middle">
          {label}
        </text>
      )}
    </P>
  );
  const Lamp = ({
    name,
    x,
    y,
    label,
    lit,
    lx = 26,
    ly = 5,
  }: {
    name: string;
    x: number;
    y: number;
    label?: string;
    lit?: boolean;
    lx?: number;
    ly?: number;
  }) => (
    <P name={name}>
      <circle className="halo" cx={x} cy={y} r={26} />
      {lit && live && <circle className="glow" cx={x} cy={y} r={22} />}
      <circle cx={x} cy={y} r={16} fill="var(--surface)" />
      <line x1={x - 11} y1={y - 11} x2={x + 11} y2={y + 11} />
      <line x1={x + 11} y1={y - 11} x2={x - 11} y2={y + 11} />
      {label && (
        <text x={x + lx} y={y + ly} textAnchor={lx < 0 ? "end" : "start"}>
          {label}
        </text>
      )}
    </P>
  );
  const Cell = ({ x, y }: { x: number; y: number }) => (
    <P name="src">
      <rect className="halo" x={x - 26} y={y - 24} width={52} height={40} rx={10} />
      <line x1={x} y1={30} x2={x} y2={y - 8} />
      <line x1={x - 18} y1={y - 8} x2={x + 18} y2={y - 8} strokeWidth={3.5} />
      <line x1={x - 9} y1={y + 6} x2={x + 9} y2={y + 6} strokeWidth={5} />
      <text x={x - 24} y={y - 12} textAnchor="end">
        +
      </text>
      <text x={x - 24} y={y + 16} textAnchor="end">
        −
      </text>
    </P>
  );

  let body: ReactNode;
  let viewBox = "0 0 320 180";

  switch (id) {
    case "sym-switch":
      viewBox = "0 0 120 60";
      body = (
        <P name="sym">
          <line x1={10} y1={40} x2={38} y2={40} />
          <circle cx={42} cy={40} r={3.5} fill="currentColor" />
          <line x1={42} y1={40} x2={76} y2={20} />
          <circle cx={80} cy={40} r={3.5} fill="currentColor" />
          <line x1={84} y1={40} x2={110} y2={40} />
        </P>
      );
      break;
    case "sym-lamp":
      viewBox = "0 0 120 60";
      body = (
        <P name="sym">
          <line x1={10} y1={30} x2={44} y2={30} />
          <circle cx={60} cy={30} r={16} fill="none" />
          <line x1={49} y1={19} x2={71} y2={41} />
          <line x1={71} y1={19} x2={49} y2={41} />
          <line x1={76} y1={30} x2={110} y2={30} />
        </P>
      );
      break;
    case "sym-cell":
      viewBox = "0 0 120 60";
      body = (
        <P name="sym">
          <line x1={10} y1={30} x2={52} y2={30} />
          <line x1={52} y1={10} x2={52} y2={50} strokeWidth={3.5} />
          <line x1={66} y1={20} x2={66} y2={40} strokeWidth={5} />
          <line x1={66} y1={30} x2={110} y2={30} />
          <text x={40} y={16} textAnchor="middle">
            +
          </text>
          <text x={80} y={18} textAnchor="middle">
            −
          </text>
        </P>
      );
      break;
    case "sym-resistor":
      viewBox = "0 0 120 60";
      body = (
        <P name="sym">
          <line x1={10} y1={30} x2={36} y2={30} />
          <rect x={36} y={20} width={48} height={20} fill="none" />
          <line x1={84} y1={30} x2={110} y2={30} />
        </P>
      );
      break;
    case "circuit-simple": {
      const on = isClosed("sw");
      body = (
        <>
          <Cell x={40} y={90} />
          <P name="w-top">
            <line x1={40} y1={30} x2={140} y2={30} />
            <line x1={180} y1={30} x2={280} y2={30} />
          </P>
          <Switch name="sw" x={140} y={30} label="S" />
          <P name="w-right">
            <line x1={280} y1={30} x2={280} y2={74} />
            <line x1={280} y1={106} x2={280} y2={150} />
          </P>
          <Lamp name="lamp" x={280} y={90} label="L" lx={-26} lit={on} />
          <P name="w-bottom">
            <line x1={280} y1={150} x2={40} y2={150} />
            <line x1={40} y1={150} x2={40} y2={96} />
          </P>
        </>
      );
      break;
    }
    case "circuit-series": {
      const on = isClosed("sw");
      body = (
        <>
          <Cell x={40} y={90} />
          <P name="w-top">
            <line x1={40} y1={30} x2={90} y2={30} />
            <line x1={130} y1={30} x2={204} y2={30} />
            <line x1={236} y1={30} x2={280} y2={30} />
            <line x1={280} y1={30} x2={280} y2={74} />
          </P>
          <Switch name="sw" x={90} y={30} label="S" />
          <Lamp name="l1" x={220} y={30} label="L1" lx={-9} ly={44} lit={on} />
          <Lamp name="l2" x={280} y={90} label="L2" lx={-26} lit={on} />
          <P name="w-bottom">
            <line x1={280} y1={106} x2={280} y2={150} />
            <line x1={280} y1={150} x2={40} y2={150} />
            <line x1={40} y1={150} x2={40} y2={96} />
          </P>
        </>
      );
      break;
    }
    case "circuit-parallel": {
      const on = isClosed("sw");
      body = (
        <>
          <Cell x={40} y={90} />
          <P name="w-top">
            <line x1={40} y1={30} x2={90} y2={30} />
            <line x1={130} y1={30} x2={280} y2={30} />
            <circle cx={190} cy={30} r={4} fill="currentColor" />
            <circle cx={190} cy={150} r={4} fill="currentColor" />
          </P>
          <Switch name="sw" x={90} y={30} label="S" />
          <P name="w-b1">
            <line x1={190} y1={30} x2={190} y2={74} />
            <line x1={190} y1={106} x2={190} y2={150} />
          </P>
          <Lamp name="l1" x={190} y={90} label="L1" lx={-26} lit={on} />
          <P name="w-b2">
            <line x1={280} y1={30} x2={280} y2={74} />
            <line x1={280} y1={106} x2={280} y2={150} />
          </P>
          <Lamp name="l2" x={280} y={90} label="L2" lx={-26} lit={on} />
          <P name="w-bottom">
            <line x1={280} y1={150} x2={40} y2={150} />
            <line x1={40} y1={150} x2={40} y2={96} />
          </P>
        </>
      );
      break;
    }
    case "circuit-two-switch": {
      const on1 = isClosed("s1");
      const on2 = isClosed("s2");
      body = (
        <>
          <Cell x={40} y={100} />
          <P name="w-main">
            <line x1={40} y1={30} x2={130} y2={30} />
            <circle cx={100} cy={30} r={4} fill="currentColor" />
            <line x1={100} y1={30} x2={100} y2={100} />
            <line x1={280} y1={30} x2={280} y2={160} />
            <circle cx={280} cy={100} r={4} fill="currentColor" />
            <line x1={280} y1={160} x2={40} y2={160} />
            <line x1={40} y1={160} x2={40} y2={106} />
          </P>
          <Switch name="s1" x={130} y={30} label="S1" />
          <P name="w-b1">
            <line x1={170} y1={30} x2={214} y2={30} />
            <line x1={246} y1={30} x2={280} y2={30} />
          </P>
          <Lamp name="l1" x={230} y={30} label="L1" lx={-9} ly={44} lit={on1} />
          <P name="w-b2">
            <line x1={100} y1={100} x2={130} y2={100} />
            <line x1={170} y1={100} x2={214} y2={100} />
            <line x1={246} y1={100} x2={280} y2={100} />
          </P>
          <Switch name="s2" x={130} y={100} label="S2" />
          <Lamp name="l2" x={230} y={100} label="L2" lx={-9} ly={44} lit={on2} />
        </>
      );
      break;
    }
    case "meter-dial": {
      const cx = 160;
      const cy = 100;
      const seg = (name: string, angle: number, label: string) => {
        const r = (angle * Math.PI) / 180;
        const x = cx + Math.cos(r) * 96;
        const y = cy + Math.sin(r) * 60 + 5;
        return (
          <P name={name} key={name}>
            <circle className="halo" cx={x} cy={y - 5} r={20} />
            <line x1={cx + Math.cos(r) * 46} y1={cy + Math.sin(r) * 46} x2={cx + Math.cos(r) * 56} y2={cy + Math.sin(r) * 54} />
            <text x={x} y={y} textAnchor="middle">
              {label}
            </text>
          </P>
        );
      };
      body = (
        <>
          <P name="body">
            <rect x={22} y={10} width={276} height={164} rx={22} fill="none" />
            <circle cx={cx} cy={cy} r={38} fill="var(--surface)" />
            <line x1={cx} y1={cy} x2={cx} y2={cy - 30} strokeWidth={5} />
            <circle cx={cx} cy={cy} r={6} fill="currentColor" />
          </P>
          {seg("off", -90, "OFF")}
          {seg("vac", -150, "V~")}
          {seg("vdc", 170, "V⎓")}
          {seg("ohm", -30, "Ω")}
          {seg("amp", 10, "A")}
        </>
      );
      break;
    }
  }

  return (
    <svg
      viewBox={viewBox}
      className={`fig ${hl.size ? "has-hl" : ""} ${className}`}
      role="img"
      aria-label={title ?? ALT[id]}
      fill="none"
      stroke="currentColor"
      strokeWidth={2.5}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {body}
    </svg>
  );
}
