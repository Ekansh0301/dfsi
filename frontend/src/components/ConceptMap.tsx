import type { ConceptId, LearnerState } from "../api/types";
import { CONCEPTS, CONCEPT_ORDER } from "../data/curriculum";
import { band, masteryOf } from "../engine/engine";

export const SHORT: Record<ConceptId, string> = {
  safety: "Safety",
  quantities: "V · I · R",
  ohm: "Ohm's law",
  symbols: "Symbols",
  wiring: "Switch wiring",
  multimeter: "Multimeter",
  series_parallel: "Series/parallel",
  diagrams: "Diagrams",
  earthing: "Earthing / MCB",
  fault: "Fault finding",
};

const W = 142;
const H = 44;
const GX = 170;
const GY = 62;
const PAD = 8;

/** Concept dependency DAG coloured by one learner's mastery. Educator-facing, so numbers are shown. */
export function ConceptMap({ learner, focus, chain = [] }: { learner: LearnerState; focus?: ConceptId; chain?: ConceptId[] }) {
  const xy = (c: ConceptId) => ({ x: PAD + CONCEPTS[c].pos.col * GX, y: PAD + CONCEPTS[c].pos.row * GY });
  const width = PAD * 2 + 4 * GX + W;
  const height = PAD * 2 + 3 * GY + H;
  const onChain = (a: ConceptId, b: ConceptId) => chain.includes(a) && chain.includes(b);
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="cmap" role="img" aria-label="Concept dependency map with mastery per concept">
      <defs>
        <marker id="cm-arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M0 0L8 4L0 8z" fill="var(--line-strong)" />
        </marker>
      </defs>
      {CONCEPT_ORDER.flatMap((c) =>
        CONCEPTS[c].prereqs.map((p) => {
          const a = xy(p);
          const b = xy(c);
          const x1 = a.x + W;
          const y1 = a.y + H / 2;
          const x2 = b.x - 2;
          const y2 = b.y + H / 2;
          const mx = (x1 + x2) / 2;
          return (
            <path
              key={p + c}
              d={`M${x1} ${y1} C${mx} ${y1} ${mx} ${y2} ${x2} ${y2}`}
              className={"cm-edge" + (onChain(p, c) ? " chain" : "")}
              markerEnd="url(#cm-arrow)"
            />
          );
        }),
      )}
      {CONCEPT_ORDER.map((c) => {
        const { x, y } = xy(c);
        const b = band(learner, c);
        const p = masteryOf(learner, c);
        const seen = !!learner.observations[c];
        return (
          <g
            key={c}
            transform={`translate(${x} ${y})`}
            className={`cm-node b-${b}` + (c === focus ? " focus" : "") + (chain.includes(c) ? " on-chain" : "")}
          >
            <title>{`${CONCEPTS[c].name.en}: ${seen ? Math.round(p * 100) + "%" : "not observed"}`}</title>
            <rect width={W} height={H} rx={10} className="cm-box" />
            <rect x={8} y={H - 11} width={W - 16} height={4} rx={2} className="cm-track" />
            {seen && <rect x={8} y={H - 11} width={(W - 16) * p} height={4} rx={2} className="cm-fill" />}
            <text x={10} y={19} className="cm-label">
              {SHORT[c]}
            </text>
            <text x={W - 10} y={19} textAnchor="end" className="cm-pct">
              {seen ? Math.round(p * 100) + "%" : "n/a"}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
