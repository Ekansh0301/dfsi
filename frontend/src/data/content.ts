import type { ConceptId, ContentItem } from "../api/types";

/**
 * Remedial content library (content-to-concept mapping, Design Doc §5 input).
 * Every item is bite-sized (4 minutes or less). In the field, short localized clips from the NGO would sit alongside these.
 */
const ITEMS: ContentItem[] = [
  // ── Reading circuit diagrams ──────────────────────────────────────────
  {
    id: "ct_diag_walk",
    concept: "diagrams",
    kind: "walkthrough",
    title: { en: "Reading circuit diagrams", hi: "सर्किट डायग्राम कैसे पढ़ें" },
    minutes: 3,
    figure: "circuit-simple",
    steps: [
      {
        text: {
          en: "Every circuit starts at the source. Here it is a cell. The long line is +, the short line is −.",
          hi: "हर सर्किट सोर्स से शुरू होता है। यहाँ सोर्स एक सेल है। लंबी लाइन + है, छोटी लाइन − है।",
        },
        highlight: ["src"],
      },
      {
        text: {
          en: "Put your finger on + and follow the line. Lines are just wires.",
          hi: "+ पर उँगली रखें और लाइन के साथ चलें। लाइनें बस तार हैं।",
        },
        highlight: ["w-top"],
      },
      {
        text: {
          en: "You reach the switch. A gap means it is open (OFF), so current cannot cross.",
          hi: "अब स्विच आता है। गैप का मतलब है स्विच खुला (OFF) है, करंट पार नहीं कर सकता।",
        },
        highlight: ["sw"],
      },
      {
        text: {
          en: "Next is the lamp: a circle with a cross. It is the load that uses the current.",
          hi: "आगे बल्ब है: क्रॉस वाला गोला। यह लोड है जो करंट इस्तेमाल करता है।",
        },
        highlight: ["lamp", "w-right"],
      },
      {
        text: {
          en: "Follow the wire back to −. Close the switch and the loop is complete, so the lamp lights.",
          hi: "तार के साथ वापस − तक जाएँ। स्विच बंद करें तो लूप पूरा होता है, और बल्ब जलता है।",
        },
        highlight: ["w-bottom", "sw", "lamp"],
        closed: true,
      },
    ],
  },
  {
    id: "ct_diag_practice",
    concept: "diagrams",
    kind: "practice",
    title: { en: "Trace 3 circuits", hi: "3 सर्किट ट्रेस करें" },
    minutes: 4,
    steps: [
      {
        figure: "circuit-series",
        text: {
          en: "The switch is closed. Trace the loop with your finger. Do both lamps light?",
          hi: "स्विच बंद है। उँगली से लूप ट्रेस करें। क्या दोनों बल्ब जलेंगे?",
        },
        answer: {
          en: "Yes. There is one loop and it passes through both lamps (series).",
          hi: "हाँ। एक ही लूप है और वह दोनों बल्बों से गुज़रता है (सीरीज़)।",
        },
        closed: true,
      },
      {
        figure: "circuit-parallel",
        text: { en: "Each lamp has its own path. Can you find both loops?", hi: "हर बल्ब का अपना रास्ता है। क्या आप दोनों लूप ढूँढ सकते हैं?" },
        answer: {
          en: "Loop 1 goes through the top lamp, loop 2 through the bottom lamp. Both share the cell.",
          hi: "लूप 1 ऊपर वाले बल्ब से, लूप 2 नीचे वाले बल्ब से। दोनों एक ही सेल से जुड़े हैं।",
        },
        highlight: ["l1", "l2"],
      },
      {
        figure: "circuit-two-switch",
        text: { en: "Close only S2. Which lamp lights?", hi: "सिर्फ़ S2 बंद करें। कौन-सा बल्ब जलेगा?" },
        answer: { en: "Only L2, because S2 is in L2's branch.", hi: "सिर्फ़ L2, क्योंकि S2, L2 की शाखा में है।" },
        highlight: ["s2", "l2"],
        closed: ["s2"],
      },
    ],
  },
  {
    id: "ct_diag_example",
    concept: "diagrams",
    kind: "walkthrough",
    title: { en: "A worked example", hi: "हल किया हुआ उदाहरण" },
    minutes: 2,
    figure: "circuit-two-switch",
    steps: [
      {
        text: { en: "This board has one cell, two switches and two lamps.", hi: "इस बोर्ड पर एक सेल, दो स्विच और दो बल्ब हैं।" },
        highlight: ["src"],
      },
      { text: { en: "The top branch has S1 and L1.", hi: "ऊपर की शाखा में S1 और L1 हैं।" }, highlight: ["s1", "l1"] },
      { text: { en: "The bottom branch has S2 and L2.", hi: "नीचे की शाखा में S2 और L2 हैं।" }, highlight: ["s2", "l2"] },
      {
        text: { en: "Each switch controls only the lamp in its own branch.", hi: "हर स्विच सिर्फ़ अपनी शाखा वाले बल्ब को चलाता है।" },
        highlight: ["s1", "l1", "s2", "l2"],
        closed: true,
      },
    ],
  },
  // ── Circuit symbols ───────────────────────────────────────────────────
  {
    id: "ct_sym_cards",
    concept: "symbols",
    kind: "walkthrough",
    title: { en: "The 4 symbols you need", hi: "4 ज़रूरी चिह्न" },
    minutes: 2,
    steps: [
      {
        figure: "sym-cell",
        text: { en: "Cell or battery: the long line is +, the short line is −.", hi: "सेल या बैटरी: लंबी लाइन + है, छोटी लाइन − है।" },
      },
      { figure: "sym-switch", text: { en: "Switch: a line with a gap. Open means OFF.", hi: "स्विच: गैप वाली लाइन। खुला मतलब OFF।" } },
      { figure: "sym-lamp", text: { en: "Lamp: a circle with a cross inside.", hi: "बल्ब: गोला, जिसके अंदर क्रॉस हो।" } },
      {
        figure: "sym-resistor",
        text: { en: "Resistor: a small rectangle (old books draw a zig-zag).", hi: "रेज़िस्टर: छोटा आयत (पुरानी किताबों में ज़िग-ज़ैग)।" },
      },
      {
        figure: "circuit-simple",
        text: { en: "Now spot the cell, switch and lamp together in one circuit.", hi: "अब एक ही सर्किट में सेल, स्विच और बल्ब पहचानें।" },
        highlight: ["src", "sw", "lamp"],
      },
    ],
  },
  {
    id: "ct_sym_practice",
    concept: "symbols",
    kind: "practice",
    title: { en: "Name that symbol", hi: "चिह्न पहचानें" },
    minutes: 2,
    steps: [
      { figure: "sym-lamp", text: { en: "What is this?", hi: "यह क्या है?" }, answer: { en: "A lamp.", hi: "बल्ब।" } },
      { figure: "sym-cell", text: { en: "Which side is +?", hi: "+ कौन-सी तरफ़ है?" }, answer: { en: "The long line.", hi: "लंबी लाइन।" } },
      {
        figure: "sym-switch",
        text: { en: "Is this switch ON or OFF?", hi: "यह स्विच ON है या OFF?" },
        answer: { en: "OFF, because there is a gap.", hi: "OFF, क्योंकि गैप है।" },
      },
    ],
  },
  // ── Wiring ────────────────────────────────────────────────────────────
  {
    id: "ct_wiring_walk",
    concept: "wiring",
    kind: "walkthrough",
    title: { en: "Where the switch goes", hi: "स्विच कहाँ लगता है" },
    minutes: 3,
    figure: "circuit-simple",
    steps: [
      {
        text: {
          en: "Mains has 3 wires: phase (red or brown), neutral (black or blue) and earth (green).",
          hi: "मेन्स में 3 तार होते हैं: फेज़ (लाल या भूरा), न्यूट्रल (काला या नीला) और अर्थ (हरा)।",
        },
      },
      { text: { en: "The switch always breaks the phase wire.", hi: "स्विच हमेशा फेज़ तार में लगता है।" }, highlight: ["w-top", "sw"] },
      {
        text: {
          en: "Why: when the switch is OFF, the lamp holder has no live voltage, so changing the bulb is safe.",
          hi: "क्यों: स्विच OFF होने पर होल्डर में लाइव वोल्टेज नहीं रहता, इसलिए बल्ब बदलना सुरक्षित है।",
        },
        highlight: ["lamp"],
      },
      {
        text: {
          en: "Neutral goes straight back from the lamp. Earth goes to metal bodies.",
          hi: "न्यूट्रल बल्ब से सीधा वापस जाता है। अर्थ धातु के ढाँचे से जुड़ता है।",
        },
        highlight: ["w-bottom"],
      },
    ],
  },
  {
    id: "ct_wiring_practice",
    concept: "wiring",
    kind: "practice",
    title: { en: "Spot the wiring mistake", hi: "वायरिंग की गलती पकड़ें" },
    minutes: 3,
    steps: [
      {
        text: { en: "A switch is fitted in the neutral wire. Is that safe?", hi: "स्विच न्यूट्रल तार में लगा है। क्या यह सुरक्षित है?" },
        answer: { en: "No. The holder stays live even when the switch is OFF.", hi: "नहीं। स्विच OFF होने पर भी होल्डर में करंट रहता है।" },
      },
      {
        text: { en: "A green wire is used as phase. What is wrong?", hi: "हरा तार फेज़ के लिए लगाया गया है। क्या गलत है?" },
        answer: {
          en: "Green is only for earth. The next electrician will be misled.",
          hi: "हरा सिर्फ़ अर्थ के लिए है। अगला इलेक्ट्रीशियन धोखा खा सकता है।",
        },
      },
    ],
  },
  // ── Series & parallel ─────────────────────────────────────────────────
  {
    id: "ct_sp_walk",
    concept: "series_parallel",
    kind: "walkthrough",
    title: { en: "Series vs parallel", hi: "सीरीज़ बनाम पैरेलल" },
    minutes: 3,
    steps: [
      {
        figure: "circuit-series",
        text: {
          en: "Series: one single path. The current goes through every lamp in turn.",
          hi: "सीरीज़: एक ही रास्ता। करंट बारी-बारी हर बल्ब से गुज़रता है।",
        },
        closed: true,
      },
      {
        figure: "circuit-series",
        text: {
          en: "If one lamp breaks, the path breaks and all lamps go off.",
          hi: "एक बल्ब टूटे तो रास्ता टूटता है और सारे बल्ब बंद हो जाते हैं।",
        },
        highlight: ["l1"],
      },
      {
        figure: "circuit-parallel",
        text: {
          en: "Parallel: each lamp has its own branch and gets the full voltage.",
          hi: "पैरेलल: हर बल्ब की अपनी शाखा है और उसे पूरा वोल्टेज मिलता है।",
        },
        highlight: ["l1", "l2"],
        closed: true,
      },
      {
        figure: "circuit-parallel",
        text: { en: "That is why house lamps are wired in parallel.", hi: "इसीलिए घर के बल्ब पैरेलल में जोड़े जाते हैं।" },
      },
    ],
  },
  {
    id: "ct_sp_example",
    concept: "series_parallel",
    kind: "walkthrough",
    title: { en: "Two lamps, two ways", hi: "दो बल्ब, दो तरीके" },
    minutes: 2,
    steps: [
      { figure: "circuit-series", text: { en: "Watch the current take a single path.", hi: "देखें, करंट एक ही रास्ते से जाता है।" }, closed: true },
      { figure: "circuit-parallel", text: { en: "Now it splits into two branches.", hi: "अब यह दो शाखाओं में बँट जाता है।" }, closed: true },
    ],
  },
  // ── Other concepts: one core item each ────────────────────────────────
  {
    id: "ct_safety_walk",
    concept: "safety",
    kind: "walkthrough",
    title: { en: "Safe isolation in 4 steps", hi: "सुरक्षित आइसोलेशन के 4 कदम" },
    minutes: 2,
    steps: [
      { text: { en: "1. Switch off the MCB for that circuit.", hi: "1. उस सर्किट का MCB बंद करें।" } },
      { text: { en: "2. Lock it or tag it so nobody switches it back on.", hi: "2. उस पर ताला या टैग लगाएँ, ताकि कोई वापस चालू न करे।" } },
      { text: { en: "3. Test with a tester that the wire is dead.", hi: "3. टेस्टर से जाँचें कि तार में करंट नहीं है।" } },
      { text: { en: "4. Only then start work, wearing insulated gloves.", hi: "4. उसके बाद ही इंसुलेटेड दस्ताने पहनकर काम शुरू करें।" } },
    ],
  },
  {
    id: "ct_quant_walk",
    concept: "quantities",
    kind: "walkthrough",
    title: { en: "V, A and Ω: the water-pipe idea", hi: "V, A और Ω: पानी के पाइप से समझें" },
    minutes: 2,
    steps: [
      { text: { en: "Voltage (V) is like water pressure: the push.", hi: "वोल्टेज (V) पानी के दबाव जैसा है: धक्का।" } },
      { text: { en: "Current (A) is like the flow of water.", hi: "करंट (A) पानी के बहाव जैसा है।" } },
      { text: { en: "Resistance (Ω) is like a narrow pipe that slows the flow.", hi: "रेज़िस्टेंस (Ω) पतले पाइप जैसा है, जो बहाव धीमा करता है।" } },
    ],
  },
  {
    id: "ct_ohm_walk",
    concept: "ohm",
    kind: "walkthrough",
    title: { en: "Ohm's law with one triangle", hi: "एक त्रिकोण से ओम का नियम" },
    minutes: 2,
    steps: [
      { text: { en: "V = I × R. Cover the one you want to find.", hi: "V = I × R। जो निकालना है, उसे ढकें।" } },
      { text: { en: "Cover I and you get I = V ÷ R.", hi: "I ढकें, तो मिलेगा I = V ÷ R।" } },
      { text: { en: "Example: 12 V ÷ 6 Ω = 2 A.", hi: "उदाहरण: 12 V ÷ 6 Ω = 2 A।" } },
    ],
  },
  {
    id: "ct_mm_walk",
    concept: "multimeter",
    kind: "walkthrough",
    title: { en: "Pick the right dial setting", hi: "सही डायल सेटिंग चुनें" },
    minutes: 2,
    figure: "meter-dial",
    steps: [
      { text: { en: "V~ is for AC: sockets and mains.", hi: "V~ AC के लिए है: सॉकेट और मेन्स।" }, highlight: ["vac"] },
      { text: { en: "V⎓ is for DC: batteries and cells.", hi: "V⎓ DC के लिए है: बैटरी और सेल।" }, highlight: ["vdc"] },
      {
        text: {
          en: "Ω and the beep are for continuity. Use them only with the power OFF.",
          hi: "Ω और बीप कंटिन्युटी के लिए हैं। सिर्फ़ पावर OFF होने पर।",
        },
        highlight: ["ohm"],
      },
    ],
  },
  {
    id: "ct_earth_walk",
    concept: "earthing",
    kind: "walkthrough",
    title: { en: "What MCBs and earthing protect", hi: "MCB और अर्थिंग किससे बचाते हैं" },
    minutes: 2,
    steps: [
      {
        text: {
          en: "MCB: trips on overload or short circuit, and protects the wiring.",
          hi: "MCB: ओवरलोड या शॉर्ट सर्किट पर ट्रिप होता है और वायरिंग बचाता है।",
        },
      },
      {
        text: {
          en: "Earthing: gives fault current a safe path, and protects people.",
          hi: "अर्थिंग: फॉल्ट करंट को सुरक्षित रास्ता देती है और लोगों को बचाती है।",
        },
      },
    ],
  },
  {
    id: "ct_fault_walk",
    concept: "fault",
    kind: "walkthrough",
    title: { en: "Find a fault in 3 checks", hi: "3 जाँच में फॉल्ट ढूँढें" },
    minutes: 3,
    steps: [
      { text: { en: "1. Source: is there supply at the board?", hi: "1. सोर्स: बोर्ड पर सप्लाई है?" } },
      { text: { en: "2. Load: is the lamp or appliance good?", hi: "2. लोड: बल्ब या उपकरण ठीक है?" } },
      { text: { en: "3. Path: check the switch and wires for continuity.", hi: "3. रास्ता: स्विच और तारों की कंटिन्युटी जाँचें।" } },
    ],
  },
];

export const CONTENT: Record<string, ContentItem> = Object.fromEntries(ITEMS.map((c) => [c.id, c]));

/** Content items for a concept, in recommendation order (core item first). */
export const contentFor = (c: ConceptId) => ITEMS.filter((i) => i.concept === c);
