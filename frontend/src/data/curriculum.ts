import type { Concept, ConceptId, Module, Question } from "../api/types";

/**
 * Electrician (domestic) track: demo curriculum.
 * The concept graph is a DAG: an edge A → B means "A is a prerequisite of B".
 * Mirrors the cumulative structure described in the Design Doc (you can't read circuit
 * diagrams without symbols and basic wiring).
 */
export const CONCEPTS: Record<ConceptId, Concept> = {
  safety: { id: "safety", name: { en: "Electrical safety", hi: "बिजली से सुरक्षा" }, prereqs: [], pos: { col: 0, row: 1.5 } },
  quantities: {
    id: "quantities",
    name: { en: "Voltage, current & resistance", hi: "वोल्टेज, करंट और रेज़िस्टेंस" },
    prereqs: ["safety"],
    pos: { col: 1, row: 1.5 },
  },
  ohm: { id: "ohm", name: { en: "Ohm's law", hi: "ओम का नियम" }, prereqs: ["quantities"], pos: { col: 2, row: 0 } },
  symbols: { id: "symbols", name: { en: "Circuit symbols", hi: "सर्किट के चिह्न" }, prereqs: ["quantities"], pos: { col: 2, row: 1 } },
  wiring: {
    id: "wiring",
    name: { en: "Switch & lamp wiring", hi: "स्विच और बल्ब की वायरिंग" },
    prereqs: ["safety", "quantities"],
    pos: { col: 2, row: 2 },
  },
  multimeter: {
    id: "multimeter",
    name: { en: "Using a multimeter", hi: "मल्टीमीटर का उपयोग" },
    prereqs: ["safety", "quantities"],
    pos: { col: 2, row: 3 },
  },
  series_parallel: {
    id: "series_parallel",
    name: { en: "Series & parallel circuits", hi: "सीरीज़ और पैरेलल सर्किट" },
    prereqs: ["ohm"],
    pos: { col: 3, row: 0 },
  },
  diagrams: {
    id: "diagrams",
    name: { en: "Reading circuit diagrams", hi: "सर्किट डायग्राम" },
    prereqs: ["symbols", "wiring"],
    pos: { col: 3, row: 1.5 },
  },
  earthing: {
    id: "earthing",
    name: { en: "Earthing, MCB & fuse", hi: "अर्थिंग, MCB और फ्यूज़" },
    prereqs: ["safety", "wiring"],
    pos: { col: 3, row: 3 },
  },
  fault: {
    id: "fault",
    name: { en: "Fault finding", hi: "फॉल्ट की पहचान" },
    prereqs: ["diagrams", "multimeter", "series_parallel"],
    pos: { col: 4, row: 1.5 },
  },
};

export const CONCEPT_ORDER: ConceptId[] = [
  "safety",
  "quantities",
  "ohm",
  "symbols",
  "wiring",
  "multimeter",
  "series_parallel",
  "diagrams",
  "earthing",
  "fault",
];

export const MODULES: Module[] = [
  { id: "m1", number: 1, title: { en: "Safety first", hi: "पहले सुरक्षा" }, concepts: ["safety"], quiz: ["q_s1", "q_s2", "q_s3"], minutes: 2 },
  {
    id: "m2",
    number: 2,
    title: { en: "Electricity basics", hi: "बिजली की बुनियादी बातें" },
    concepts: ["quantities", "ohm"],
    quiz: ["q_q1", "q_q2", "q_o1"],
    minutes: 2,
  },
  {
    id: "m3",
    number: 3,
    title: { en: "Wiring basics", hi: "वायरिंग की बुनियादी बातें" },
    concepts: ["symbols", "wiring", "diagrams"],
    quiz: ["q_w1", "q_w2", "q_w3", "q_w4", "q_w5"],
    minutes: 3,
  },
  {
    id: "m4",
    number: 4,
    title: { en: "Series & parallel", hi: "सीरीज़ और पैरेलल" },
    concepts: ["series_parallel", "diagrams"],
    quiz: ["q_p1", "q_p2", "q_p3"],
    minutes: 2,
  },
  {
    id: "m5",
    number: 5,
    title: { en: "Measuring with a multimeter", hi: "मल्टीमीटर से नापना" },
    concepts: ["multimeter"],
    quiz: ["q_m1", "q_m2", "q_m3"],
    minutes: 2,
  },
  {
    id: "m6",
    number: 6,
    title: { en: "Protection & fault finding", hi: "सुरक्षा उपकरण और फॉल्ट ढूँढना" },
    concepts: ["earthing", "fault"],
    quiz: ["q_e1", "q_f1", "q_f2"],
    minutes: 2,
  },
];

/** Placement quiz for cold-start onboarding (Secondary workflow B). Uses pool items, not module items. */
export const PLACEMENT: string[] = ["q_x_saf4", "q_x_q3", "q_x_ohm2", "q_x_sym2", "q_x_wir2", "q_x_mm2"];

const Q: Question[] = [
  // ── Module 1 · Safety ────────────────────────────────────────────────
  {
    id: "q_s1",
    concepts: ["safety"],
    prompt: { en: "Before touching a wire, what should you do first?", hi: "किसी तार को छूने से पहले सबसे पहले क्या करना चाहिए?" },
    options: [
      { text: { en: "Switch off the supply at the MCB", hi: "MCB से सप्लाई बंद करें" } },
      { text: { en: "Touch it quickly with dry hands", hi: "सूखे हाथों से जल्दी से छू लें" } },
      { text: { en: "Ask someone to hold the other end", hi: "किसी से दूसरा सिरा पकड़वाएँ" } },
    ],
    correct: 0,
    why: {
      en: "Always isolate the supply first. Dry hands do not make a live wire safe.",
      hi: "हमेशा पहले सप्लाई बंद करें। सूखे हाथ होने से भी चालू तार सुरक्षित नहीं होता।",
    },
  },
  {
    id: "q_s2",
    concepts: ["safety"],
    prompt: { en: "Which tool is safest for working on a switch board?", hi: "स्विच बोर्ड पर काम करने के लिए कौन-सा औज़ार सबसे सुरक्षित है?" },
    options: [
      { text: { en: "Screwdriver with an insulated handle", hi: "इंसुलेटेड हैंडल वाला पेचकस" } },
      { text: { en: "Any metal screwdriver", hi: "कोई भी धातु का पेचकस" } },
      { text: { en: "A kitchen knife", hi: "रसोई का चाकू" } },
    ],
    correct: 0,
    why: { en: "The insulated handle stops current from reaching your hand.", hi: "इंसुलेटेड हैंडल करंट को आपके हाथ तक पहुँचने से रोकता है।" },
  },
  {
    id: "q_s3",
    concepts: ["safety"],
    prompt: {
      en: "Someone is getting a shock and is stuck to a wire. What do you do first?",
      hi: "किसी को करंट लग रहा है और वह तार से चिपका है। सबसे पहले क्या करेंगे?",
    },
    options: [
      { text: { en: "Switch off the supply, or push them away with dry wood", hi: "सप्लाई बंद करें, या सूखी लकड़ी से उन्हें अलग करें" } },
      { text: { en: "Pull them away with your hands", hi: "अपने हाथों से उन्हें खींचें" } },
      { text: { en: "Pour water on them", hi: "उन पर पानी डालें" } },
    ],
    correct: 0,
    why: {
      en: "Touching them passes the current to you. Break the circuit first.",
      hi: "उन्हें छूने से करंट आपको भी लगेगा। पहले सर्किट तोड़ें।",
    },
  },
  // ── Module 2 · Basics ────────────────────────────────────────────────
  {
    id: "q_q1",
    concepts: ["quantities"],
    prompt: { en: "What is measured in volts (V)?", hi: "वोल्ट (V) में क्या नापा जाता है?" },
    options: [
      { text: { en: "Voltage: the push that moves current", hi: "वोल्टेज: वह दबाव जो करंट को चलाता है" } },
      { text: { en: "Current: the flow itself", hi: "करंट: खुद बहाव" } },
      { text: { en: "Resistance", hi: "रेज़िस्टेंस" } },
    ],
    correct: 0,
    why: { en: "Voltage is the electrical push, like water pressure in a pipe.", hi: "वोल्टेज बिजली का दबाव है, जैसे पाइप में पानी का दबाव।" },
  },
  {
    id: "q_q2",
    concepts: ["quantities"],
    prompt: { en: "Current is measured in…", hi: "करंट किसमें नापा जाता है?" },
    options: [
      { text: { en: "Amperes (A)", hi: "एम्पियर (A)" } },
      { text: { en: "Ohms (Ω)", hi: "ओम (Ω)" } },
      { text: { en: "Watts (W)", hi: "वाट (W)" } },
    ],
    correct: 0,
    why: { en: "Current (flow) is in amperes. Ohms are for resistance.", hi: "करंट (बहाव) एम्पियर में नापा जाता है। ओम रेज़िस्टेंस के लिए है।" },
  },
  {
    id: "q_o1",
    concepts: ["ohm", "quantities"],
    prompt: {
      en: "A 12 V battery is connected to a 6 Ω resistor. How much current flows?",
      hi: "12 V की बैटरी 6 Ω के रेज़िस्टर से जुड़ी है। कितना करंट बहेगा?",
    },
    options: [{ text: { en: "2 A", hi: "2 A" } }, { text: { en: "72 A", hi: "72 A" } }, { text: { en: "0.5 A", hi: "0.5 A" } }],
    correct: 0,
    why: { en: "Current = Voltage ÷ Resistance = 12 ÷ 6 = 2 A.", hi: "करंट = वोल्टेज ÷ रेज़िस्टेंस = 12 ÷ 6 = 2 A।" },
  },
  // ── Module 3 · Wiring basics ─────────────────────────────────────────
  {
    id: "q_w1",
    concepts: ["symbols"],
    figure: "sym-switch",
    prompt: { en: "What does this symbol show?", hi: "यह चिह्न क्या दिखाता है?" },
    options: [{ text: { en: "A switch", hi: "स्विच" } }, { text: { en: "A lamp", hi: "बल्ब" } }, { text: { en: "A resistor", hi: "रेज़िस्टर" } }],
    correct: 0,
    why: { en: "A switch is drawn as a line with a gap that can close.", hi: "स्विच को गैप वाली लाइन से दिखाते हैं, जो बंद हो सकती है।" },
  },
  {
    id: "q_w2",
    concepts: ["wiring", "safety"],
    prompt: {
      en: "In a switch-and-lamp circuit, the switch must break which wire?",
      hi: "स्विच और बल्ब के सर्किट में स्विच किस तार में लगाया जाता है?",
    },
    options: [
      { text: { en: "Phase (live) wire", hi: "फेज़ (लाइव) तार" } },
      { text: { en: "Neutral wire", hi: "न्यूट्रल तार" } },
      { text: { en: "Earth wire", hi: "अर्थ तार" } },
    ],
    correct: 0,
    why: {
      en: "With the switch in the phase wire, the lamp holder is dead when the switch is off.",
      hi: "फेज़ में स्विच लगाने से, स्विच बंद होने पर होल्डर में करंट नहीं रहता।",
    },
  },
  {
    id: "q_w3",
    concepts: ["diagrams", "symbols"],
    figure: "circuit-simple",
    prompt: { en: "Look at the diagram. Is the lamp on or off?", hi: "डायग्राम देखें। बल्ब जल रहा है या बंद है?" },
    options: [
      { text: { en: "Off: the switch is open", hi: "बंद: स्विच खुला है" } },
      { text: { en: "On: the battery is connected", hi: "जल रहा है: बैटरी जुड़ी है" } },
      { text: { en: "You can't tell from a diagram", hi: "डायग्राम से पता नहीं चलता" } },
    ],
    correct: 0,
    why: { en: "The gap in the switch breaks the loop, so no current flows.", hi: "स्विच का गैप लूप तोड़ देता है, इसलिए करंट नहीं बहता।" },
  },
  {
    id: "q_w4",
    concepts: ["diagrams"],
    figure: "circuit-two-switch",
    figureClosed: ["s1"],
    prompt: { en: "Only switch S1 is closed (ON). Which lamp lights?", hi: "सिर्फ़ स्विच S1 बंद (ON) है। कौन-सा बल्ब जलेगा?" },
    options: [
      { text: { en: "L1 only", hi: "सिर्फ़ L1" } },
      { text: { en: "L2 only", hi: "सिर्फ़ L2" } },
      { text: { en: "Both L1 and L2", hi: "L1 और L2 दोनों" } },
    ],
    correct: 0,
    why: { en: "S1 sits in L1's branch. L2's branch is still open at S2.", hi: "S1, L1 की शाखा में है। L2 की शाखा S2 पर अभी भी खुली है।" },
  },
  {
    id: "q_w5",
    concepts: ["wiring"],
    prompt: { en: "What colour is the earth wire in Indian house wiring?", hi: "भारत में घर की वायरिंग में अर्थ तार किस रंग का होता है?" },
    options: [
      { text: { en: "Green (or green-yellow)", hi: "हरा (या हरा-पीला)" } },
      { text: { en: "Red", hi: "लाल" } },
      { text: { en: "Black", hi: "काला" } },
    ],
    correct: 0,
    why: {
      en: "Earth is green or green-yellow. Phase is red or brown, neutral is black or blue.",
      hi: "अर्थ हरा या हरा-पीला होता है। फेज़ लाल या भूरा, न्यूट्रल काला या नीला।",
    },
  },
  // ── Module 4 · Series & parallel ─────────────────────────────────────
  {
    id: "q_p1",
    concepts: ["series_parallel", "diagrams"],
    figure: "circuit-series",
    prompt: { en: "How are these two lamps connected?", hi: "ये दोनों बल्ब किस तरह जुड़े हैं?" },
    options: [
      { text: { en: "In series", hi: "सीरीज़ में" } },
      { text: { en: "In parallel", hi: "पैरेलल में" } },
      { text: { en: "They are not connected", hi: "जुड़े ही नहीं हैं" } },
    ],
    correct: 0,
    why: { en: "There is only one path, and it goes through both lamps.", hi: "सिर्फ़ एक ही रास्ता है, और वह दोनों बल्बों से होकर जाता है।" },
  },
  {
    id: "q_p2",
    concepts: ["series_parallel"],
    prompt: { en: "Why are lamps in a house connected in parallel?", hi: "घर में बल्ब पैरेलल में क्यों जोड़े जाते हैं?" },
    options: [
      { text: { en: "Each lamp gets full voltage and works on its own", hi: "हर बल्ब को पूरा वोल्टेज मिलता है और वह अलग से चलता है" } },
      { text: { en: "It uses less wire", hi: "इसमें कम तार लगता है" } },
      { text: { en: "So that all lamps go off together", hi: "ताकि सारे बल्ब एक साथ बंद हों" } },
    ],
    correct: 0,
    why: { en: "In parallel, one lamp failing does not switch off the others.", hi: "पैरेलल में एक बल्ब खराब होने पर बाकी बंद नहीं होते।" },
  },
  {
    id: "q_p3",
    concepts: ["series_parallel", "ohm"],
    prompt: {
      en: "Two 5 Ω resistors are in series. What is the total resistance?",
      hi: "दो 5 Ω रेज़िस्टर सीरीज़ में हैं। कुल रेज़िस्टेंस कितना है?",
    },
    options: [{ text: { en: "10 Ω", hi: "10 Ω" } }, { text: { en: "2.5 Ω", hi: "2.5 Ω" } }, { text: { en: "25 Ω", hi: "25 Ω" } }],
    correct: 0,
    why: { en: "In series, resistances add: 5 + 5 = 10 Ω.", hi: "सीरीज़ में रेज़िस्टेंस जुड़ते हैं: 5 + 5 = 10 Ω।" },
  },
  // ── Module 5 · Multimeter ────────────────────────────────────────────
  {
    id: "q_m1",
    concepts: ["multimeter"],
    figure: "meter-dial",
    prompt: {
      en: "To check if a wall socket is live, where do you set the dial?",
      hi: "दीवार का सॉकेट चालू है या नहीं, यह जाँचने के लिए डायल कहाँ रखें?",
    },
    options: [
      { text: { en: "V~ (AC voltage)", hi: "V~ (AC वोल्टेज)" } },
      { text: { en: "V⎓ (DC voltage)", hi: "V⎓ (DC वोल्टेज)" } },
      { text: { en: "Ω (resistance)", hi: "Ω (रेज़िस्टेंस)" } },
    ],
    correct: 0,
    why: { en: "House supply is AC, so use the AC voltage range.", hi: "घर की सप्लाई AC होती है, इसलिए AC वोल्टेज रेंज लें।" },
  },
  {
    id: "q_m2",
    concepts: ["multimeter", "safety"],
    prompt: { en: "Before measuring resistance (Ω), the circuit must be…", hi: "रेज़िस्टेंस (Ω) नापने से पहले सर्किट को…" },
    options: [
      { text: { en: "Switched off", hi: "बंद करना चाहिए" } },
      { text: { en: "Switched on", hi: "चालू रखना चाहिए" } },
      { text: { en: "Connected to earth", hi: "अर्थ से जोड़ना चाहिए" } },
    ],
    correct: 0,
    why: {
      en: "The meter supplies its own small current. Live voltage can damage it.",
      hi: "मीटर अपना छोटा करंट देता है। चालू वोल्टेज से मीटर खराब हो सकता है।",
    },
  },
  {
    id: "q_m3",
    concepts: ["multimeter", "quantities"],
    prompt: { en: "A continuity test beeps. What does that mean?", hi: "कंटिन्युटी टेस्ट में बीप आती है। इसका मतलब क्या है?" },
    options: [
      { text: { en: "There is a complete path", hi: "रास्ता पूरा (जुड़ा हुआ) है" } },
      { text: { en: "The wire is broken", hi: "तार टूटा हुआ है" } },
      { text: { en: "The voltage is too high", hi: "वोल्टेज बहुत ज़्यादा है" } },
    ],
    correct: 0,
    why: { en: "A beep means very low resistance: the path is complete.", hi: "बीप का मतलब है बहुत कम रेज़िस्टेंस: रास्ता पूरा है।" },
  },
  // ── Module 6 · Protection & faults ───────────────────────────────────
  {
    id: "q_e1",
    concepts: ["earthing"],
    prompt: { en: "What does an MCB do?", hi: "MCB क्या करता है?" },
    options: [
      { text: { en: "Cuts the supply by itself on overload or short circuit", hi: "ओवरलोड या शॉर्ट सर्किट पर अपने आप सप्लाई काट देता है" } },
      { text: { en: "Increases the voltage", hi: "वोल्टेज बढ़ाता है" } },
      { text: { en: "Stores electricity", hi: "बिजली जमा करता है" } },
    ],
    correct: 0,
    why: {
      en: "MCB = miniature circuit breaker. It trips to protect the wiring.",
      hi: "MCB यानी मिनिएचर सर्किट ब्रेकर। यह ट्रिप होकर वायरिंग को बचाता है।",
    },
  },
  {
    id: "q_f1",
    concepts: ["fault", "multimeter", "diagrams"],
    prompt: {
      en: "A lamp does not light. The supply is fine and the bulb is good. What do you check next?",
      hi: "बल्ब नहीं जल रहा। सप्लाई ठीक है और बल्ब भी सही है। अब क्या जाँचेंगे?",
    },
    options: [
      { text: { en: "The switch and wires for a break (continuity)", hi: "स्विच और तारों में टूट (कंटिन्युटी)" } },
      { text: { en: "Replace the MCB", hi: "MCB बदल दें" } },
      { text: { en: "Change the earth wire", hi: "अर्थ तार बदल दें" } },
    ],
    correct: 0,
    why: {
      en: "Trace the loop: if source and load are fine, the path is broken somewhere.",
      hi: "लूप को ट्रेस करें: सोर्स और लोड ठीक हैं, तो रास्ता कहीं टूटा है।",
    },
  },
  {
    id: "q_f2",
    concepts: ["fault", "series_parallel"],
    prompt: { en: "Three lamps are in series and one lamp fuses. What happens?", hi: "तीन बल्ब सीरीज़ में हैं और एक फ्यूज़ हो जाता है। क्या होगा?" },
    options: [
      { text: { en: "All the lamps go off", hi: "सारे बल्ब बंद हो जाएँगे" } },
      { text: { en: "Only that lamp goes off", hi: "सिर्फ़ वही बल्ब बंद होगा" } },
      { text: { en: "The others get brighter", hi: "बाकी और तेज़ जलेंगे" } },
    ],
    correct: 0,
    why: {
      en: "A series circuit has one path. Break it anywhere and everything stops.",
      hi: "सीरीज़ में एक ही रास्ता होता है। कहीं भी टूटे तो सब बंद।",
    },
  },
  // ── Pool: placement and spaced re-checks ─────────────────────────────
  {
    id: "q_x_saf4",
    concepts: ["safety"],
    prompt: { en: "What should you wear for panel work?", hi: "पैनल पर काम करते समय क्या पहनना चाहिए?" },
    options: [
      { text: { en: "Insulated gloves and rubber-soled shoes", hi: "इंसुलेटेड दस्ताने और रबर सोल वाले जूते" } },
      { text: { en: "A metal watch and ring", hi: "धातु की घड़ी और अंगूठी" } },
      { text: { en: "Wet cloth gloves", hi: "गीले कपड़े के दस्ताने" } },
    ],
    correct: 0,
    why: {
      en: "Insulation between you and the ground keeps current out of your body.",
      hi: "आपके और ज़मीन के बीच इंसुलेशन, करंट को शरीर से दूर रखता है।",
    },
  },
  {
    id: "q_x_q3",
    concepts: ["quantities"],
    prompt: { en: "Resistance is measured in…", hi: "रेज़िस्टेंस किसमें नापा जाता है?" },
    options: [
      { text: { en: "Ohms (Ω)", hi: "ओम (Ω)" } },
      { text: { en: "Volts (V)", hi: "वोल्ट (V)" } },
      { text: { en: "Amperes (A)", hi: "एम्पियर (A)" } },
    ],
    correct: 0,
    why: { en: "Resistance, the opposition to current, is measured in ohms.", hi: "रेज़िस्टेंस, यानी करंट का विरोध, ओम में नापा जाता है।" },
  },
  {
    id: "q_x_ohm2",
    concepts: ["ohm"],
    prompt: {
      en: "The voltage stays the same and the resistance goes up. What happens to the current?",
      hi: "वोल्टेज वही रहता है और रेज़िस्टेंस बढ़ता है। करंट का क्या होगा?",
    },
    options: [
      { text: { en: "It goes down", hi: "कम होगा" } },
      { text: { en: "It goes up", hi: "बढ़ेगा" } },
      { text: { en: "It stays the same", hi: "वही रहेगा" } },
    ],
    correct: 0,
    why: { en: "Current = V ÷ R. A bigger R means a smaller current.", hi: "करंट = V ÷ R। R बड़ा होगा तो करंट छोटा होगा।" },
  },
  {
    id: "q_x_sym2",
    concepts: ["symbols"],
    figure: "sym-cell",
    prompt: { en: "What does this symbol show?", hi: "यह चिह्न क्या दिखाता है?" },
    options: [
      { text: { en: "A cell or battery", hi: "सेल या बैटरी" } },
      { text: { en: "A lamp", hi: "बल्ब" } },
      { text: { en: "A switch", hi: "स्विच" } },
    ],
    correct: 0,
    why: { en: "Long line (+) and short line (−) show a cell.", hi: "लंबी लाइन (+) और छोटी लाइन (−) सेल दिखाती हैं।" },
  },
  {
    id: "q_x_sym3",
    concepts: ["symbols"],
    figure: "sym-resistor",
    prompt: { en: "What does this symbol show?", hi: "यह चिह्न क्या दिखाता है?" },
    options: [{ text: { en: "A resistor", hi: "रेज़िस्टर" } }, { text: { en: "A lamp", hi: "बल्ब" } }, { text: { en: "A cell", hi: "सेल" } }],
    correct: 0,
    why: { en: "A small rectangle is a resistor (older books draw a zig-zag).", hi: "छोटा आयत रेज़िस्टर है (पुरानी किताबों में ज़िग-ज़ैग)।" },
  },
  {
    id: "q_x_wir2",
    concepts: ["wiring"],
    prompt: { en: "The neutral wire is usually which colour?", hi: "न्यूट्रल तार आमतौर पर किस रंग का होता है?" },
    options: [
      { text: { en: "Black (or blue)", hi: "काला (या नीला)" } },
      { text: { en: "Green", hi: "हरा" } },
      { text: { en: "Yellow", hi: "पीला" } },
    ],
    correct: 0,
    why: { en: "Neutral is black or blue. Green is kept for earth.", hi: "न्यूट्रल काला या नीला होता है। हरा अर्थ के लिए है।" },
  },
  {
    id: "q_x_wir3",
    concepts: ["wiring", "earthing"],
    prompt: { en: "Which wire should the fuse or MCB be in?", hi: "फ्यूज़ या MCB किस तार में लगना चाहिए?" },
    options: [
      { text: { en: "The phase wire", hi: "फेज़ तार में" } },
      { text: { en: "The neutral wire", hi: "न्यूट्रल तार में" } },
      { text: { en: "The earth wire", hi: "अर्थ तार में" } },
    ],
    correct: 0,
    why: {
      en: "Protection goes in the phase so a trip removes the live voltage.",
      hi: "सुरक्षा उपकरण फेज़ में लगता है, ताकि ट्रिप होने पर लाइव वोल्टेज हट जाए।",
    },
  },
  {
    id: "q_x_diag2",
    concepts: ["diagrams"],
    figure: "circuit-parallel",
    prompt: { en: "If switch S is closed (ON), how many lamps light?", hi: "अगर स्विच S बंद (ON) हो, तो कितने बल्ब जलेंगे?" },
    options: [
      { text: { en: "Both lamps", hi: "दोनों बल्ब" } },
      { text: { en: "Only the first lamp", hi: "सिर्फ़ पहला बल्ब" } },
      { text: { en: "None", hi: "एक भी नहीं" } },
    ],
    correct: 0,
    why: { en: "S is in the main line, so both branches get current.", hi: "S मुख्य लाइन में है, इसलिए दोनों शाखाओं में करंट जाएगा।" },
  },
  {
    id: "q_x_mm2",
    concepts: ["multimeter"],
    prompt: { en: "Which setting measures a torch battery?", hi: "टॉर्च की बैटरी नापने के लिए कौन-सी सेटिंग?" },
    options: [
      { text: { en: "V⎓ (DC voltage)", hi: "V⎓ (DC वोल्टेज)" } },
      { text: { en: "V~ (AC voltage)", hi: "V~ (AC वोल्टेज)" } },
      { text: { en: "A (current)", hi: "A (करंट)" } },
    ],
    correct: 0,
    why: { en: "Batteries give DC, so use the DC voltage range.", hi: "बैटरी DC देती है, इसलिए DC वोल्टेज रेंज लें।" },
  },
  {
    id: "q_x_sp2",
    concepts: ["series_parallel"],
    figure: "circuit-parallel",
    prompt: { en: "How are these two lamps connected?", hi: "ये दोनों बल्ब किस तरह जुड़े हैं?" },
    options: [
      { text: { en: "In parallel", hi: "पैरेलल में" } },
      { text: { en: "In series", hi: "सीरीज़ में" } },
      { text: { en: "Neither", hi: "दोनों में से कोई नहीं" } },
    ],
    correct: 0,
    why: { en: "Each lamp has its own branch back to the cell.", hi: "हर बल्ब की सेल तक अपनी अलग शाखा है।" },
  },
];

export const QUESTIONS: Record<string, Question> = Object.fromEntries(Q.map((q) => [q.id, q]));

export const moduleById = (id: string) => MODULES.find((m) => m.id === id)!;
export const moduleForConcept = (c: ConceptId) => MODULES.find((m) => m.concepts.includes(c))!;
