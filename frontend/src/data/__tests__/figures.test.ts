/** Screen-reader descriptions of quiz figures say what the figure shows, never the answer. */
import { describe, expect, it } from "vitest";
import { QUESTIONS } from "../curriculum";

const withFigure = Object.values(QUESTIONS).filter((q) => q.figure);

describe("quiz figure descriptions", () => {
  it("every question with a figure has a description in both languages", () => {
    expect(withFigure.length).toBeGreaterThan(0);
    for (const q of withFigure) {
      expect(q.figureAlt?.en, q.id).toBeTruthy();
      expect(q.figureAlt?.hi, q.id).toBeTruthy();
    }
  });

  it("no description contains an answer option's text", () => {
    for (const q of withFigure)
      for (const lang of ["en", "hi"] as const) {
        const alt = q.figureAlt![lang].toLowerCase();
        for (const o of q.options) {
          const core = o.text[lang].toLowerCase().replace(/^an? /, "");
          expect(alt.includes(core), `${q.id} (${lang}) mentions "${o.text[lang]}"`).toBe(false);
        }
      }
  });
});
