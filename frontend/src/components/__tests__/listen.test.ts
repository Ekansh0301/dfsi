/** The listen button picks a voice for the learner's language, or hides when there is none. */
import { describe, expect, it } from "vitest";
import { pickVoice } from "../ListenButton";

const v = (lang: string, name = lang, localService = true) => ({ lang, name, localService });

describe("voice choice for the listen button", () => {
  it("prefers an Indian English voice, then other English voices", () => {
    expect(pickVoice([v("en-US"), v("en-IN"), v("hi-IN")], "en")?.lang).toBe("en-IN");
    expect(pickVoice([v("en-US"), v("fr-FR")], "en")?.lang).toBe("en-US");
  });

  it("finds a Hindi voice, written with a dash or an underscore", () => {
    expect(pickVoice([v("en-IN"), v("hi_IN")], "hi")?.lang).toBe("hi_IN");
  });

  it("prefers a natural voice among several for the same language", () => {
    expect(pickVoice([v("hi-IN", "Basic"), v("hi-IN", "Microsoft Swara Online (Natural)", false)], "hi")?.name).toContain("Natural");
  });

  it("has no voice to offer when the device has none for the language, so the button hides", () => {
    expect(pickVoice([v("en-US"), v("en-GB")], "hi")).toBeUndefined();
    expect(pickVoice([], "en")).toBeUndefined();
  });
});
