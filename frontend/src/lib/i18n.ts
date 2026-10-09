import type { L, Lang } from "../api/types";
import { useMe } from "./store";

/**
 * Learner-facing UI strings. Every learner string exists in English and Hindi.
 * Copy rules: short sentences, no scores or jargon, and one idea per line
 * (moderate-to-low digital literacy, see the Design Doc §1).
 */
const S = {
  app_name: { en: "Circuit Coach", hi: "सर्किट कोच" },
  welcome_title: { en: "Learn wiring, one small step at a time.", hi: "वायरिंग सीखें, एक-एक छोटा कदम।" },
  welcome_body: {
    en: "After every quick check, we show you one thing to practise next. If you're still stuck, your trainer helps.",
    hi: "हर छोटी जाँच के बाद हम आपको अभ्यास के लिए एक चीज़ बताते हैं। फिर भी समझ न आए, तो आपके ट्रेनर मदद करते हैं।",
  },
  choose_lang: { en: "Choose your language", hi: "अपनी भाषा चुनें" },
  continue: { en: "Continue", hi: "आगे बढ़ें" },
  track_title: { en: "What are you training in?", hi: "आप किसकी ट्रेनिंग ले रहे हैं?" },
  track_electrical: { en: "Electrician", hi: "इलेक्ट्रीशियन" },
  track_electrical_sub: { en: "House wiring, circuits, safety", hi: "घर की वायरिंग, सर्किट, सुरक्षा" },
  track_solar: { en: "Solar technician", hi: "सोलर टेक्नीशियन" },
  track_plumbing: { en: "Plumber", hi: "प्लंबर" },
  coming_soon: { en: "Coming soon", hi: "जल्द आ रहा है" },
  exp_title: { en: "How much have you done before?", hi: "आपने पहले कितना काम किया है?" },
  exp_new: { en: "This is my first time", hi: "पहली बार सीख रहा/रही हूँ" },
  exp_some: { en: "I know a little", hi: "थोड़ा-बहुत जानता/जानती हूँ" },
  exp_experienced: { en: "I have worked on sites", hi: "साइट पर काम किया है" },
  placement_title: { en: "6 quick questions", hi: "6 छोटे सवाल" },
  placement_body: {
    en: "No marks. This only helps us find where you should start.",
    hi: "कोई नंबर नहीं। इससे बस यह पता चलता है कि आपको कहाँ से शुरू करना है।",
  },
  start: { en: "Start", hi: "शुरू करें" },
  finding_start: { en: "Finding your starting point…", hi: "आपकी शुरुआत ढूँढ रहे हैं…" },
  start_title: { en: "Start with", hi: "यहाँ से शुरू करें" },
  start_reason_skip: { en: "You already know {x}, so we've skipped ahead.", hi: "आप {x} पहले से जानते हैं, इसलिए हमने आगे से शुरू किया है।" },
  start_reason_first: { en: "We'll start from the beginning, so nothing is missed.", hi: "हम शुरुआत से चलेंगे, ताकि कुछ न छूटे।" },
  begin_module: { en: "Begin Module {n}", hi: "मॉड्यूल {n} शुरू करें" },
  hello: { en: "Namaste, {name}", hi: "नमस्ते, {name}" },
  your_next_step: { en: "Your next step", hi: "आपका अगला कदम" },
  module_n: { en: "Module {n}", hi: "मॉड्यूल {n}" },
  quick_check: { en: "Quick check", hi: "छोटी जाँच" },
  questions_min: { en: "{q} questions · about {m} min", hi: "{q} सवाल · लगभग {m} मिनट" },
  quiz_intro: {
    en: "Answer what you can. It just helps us find the right next step for you.",
    hi: "जो आता है, वो बताइए। इससे बस आपके लिए सही अगला कदम मिलता है।",
  },
  home_card_body: { en: "Finished the class or video? Take the quick check.", hi: "क्लास या वीडियो पूरा हुआ? अब छोटी जाँच दें।" },
  start_check: { en: "Start quick check", hi: "छोटी जाँच शुरू करें" },
  not_sure: { en: "I'm not sure", hi: "पता नहीं" },
  next: { en: "Next", hi: "आगे" },
  submit: { en: "Submit answers", hi: "जवाब जमा करें" },
  q_of: { en: "Question {i} of {n}", hi: "सवाल {i} / {n}" },
  from_earlier: { en: "Quick one from earlier", hi: "पहले वाला एक छोटा सवाल" },
  analysing: { en: "Checking your answers…", hi: "आपके जवाब देख रहे हैं…" },
  results_great: { en: "Great effort on Module {n}!", hi: "मॉड्यूल {n} में बढ़िया कोशिश!" },
  results_clean_title: { en: "Nice work on Module {n}!", hi: "मॉड्यूल {n} में शाबाश!" },
  results_clean: { en: "No gaps found. You're ready for the next module.", hi: "कोई कमी नहीं मिली। आप अगले मॉड्यूल के लिए तैयार हैं।" },
  results_gap: {
    en: "We looked at your answers. One thing is worth a quick review before you move on.",
    hi: "हमने आपके जवाब देखे। आगे बढ़ने से पहले एक चीज़ को जल्दी से दोहराना अच्छा रहेगा।",
  },
  results_recheck_gap: {
    en: "All right this time! One topic from earlier needs another look before you move on.",
    hi: "इस बार सब सही! पहले का एक विषय आगे बढ़ने से पहले एक बार और देखना होगा।",
  },
  results_score: { en: "{c} of {t} right", hi: "{t} में से {c} सही" },
  see_next: { en: "See my next step", hi: "मेरा अगला कदम देखें" },
  continue_module: { en: "Continue to Module {n}", hi: "मॉड्यूल {n} पर आगे बढ़ें" },
  review_answers: { en: "See my answers", hi: "मेरे जवाब देखें" },
  hide_answers: { en: "Hide answers", hi: "जवाब छिपाएँ" },
  recheck_pass: { en: "{c}: confirmed. You remembered it!", hi: "{c}: पक्का हो गया। आपको याद रहा!" },
  recheck_fail: { en: "{c} needs one more look.", hi: "{c} को एक बार और देखना होगा।" },
  rec_label: { en: "Recommended for you", hi: "आपके लिए सुझाव" },
  rec_from_trainer: { en: "From your trainer", hi: "आपके ट्रेनर की ओर से" },
  repeat_gap: { en: "Second try, a new way", hi: "दूसरी कोशिश, नया तरीका" },
  start_x: { en: "Start: {title}", hi: "शुरू करें: {title}" },
  min: { en: "{m} min", hi: "{m} मिनट" },
  why_this: { en: "Why this?", hi: "यही क्यों?" },
  why_chain: {
    en: "{A} builds on {b}. Get {b} right first, and {a} will be much easier.",
    hi: "{A}, {b} पर टिका है। पहले {b} पक्का करें, फिर {a} बहुत आसान हो जाएगा।",
  },
  why_direct: {
    en: "Your answers on {a} showed a gap. This short lesson covers exactly that.",
    hi: "{a} वाले जवाबों में कमी दिखी। यह छोटा पाठ बस उसी के बारे में है।",
  },
  why_start: { en: "Start here", hi: "यहाँ से शुरू" },
  why_then: { en: "Then this gets easier", hi: "फिर यह आसान होगा" },
  why_repeat: {
    en: "You said \"Got it\", but a later question showed it isn't solid yet. This time you'll practise it. Your trainer can see this too.",
    hi: 'आपने "समझ आ गया" कहा था, लेकिन बाद के सवाल से पता चला कि यह अभी पक्का नहीं है। इस बार अभ्यास करेंगे। आपके ट्रेनर भी यह देख सकते हैं।',
  },
  why_trainer: { en: "Your trainer chose this after reading your message.", hi: "आपका मैसेज पढ़कर ट्रेनर ने यह चुना है।" },
  step_of: { en: "Step {i} of {n}", hi: "कदम {i} / {n}" },
  back: { en: "Back", hi: "पीछे" },
  show_answer: { en: "Show answer", hi: "जवाब दिखाएँ" },
  kind_walkthrough: { en: "Step-by-step", hi: "कदम-दर-कदम" },
  kind_practice: { en: "Practice", hi: "अभ्यास" },
  feedback_q: { en: "Did this help?", hi: "क्या इससे मदद मिली?" },
  got_it: { en: "Got it!", hi: "समझ आ गया!" },
  still_stuck: { en: "I'm still stuck", hi: "अभी भी समझ नहीं आया" },
  gotit_title: { en: "Nice! We'll check back later.", hi: "बढ़िया! हम बाद में एक बार फिर पूछेंगे।" },
  gotit_body: {
    en: "A quick question on {c} will pop up in a later module, just to make sure it sticks.",
    hi: "{c} पर एक छोटा सवाल आगे किसी मॉड्यूल में आएगा, ताकि पक्का हो जाए कि याद रहा।",
  },
  continue_learning: { en: "Continue learning", hi: "सीखना जारी रखें" },
  stuck_title: { en: "That's okay. What would help most?", hi: "कोई बात नहीं। किस चीज़ से सबसे ज़्यादा मदद मिलेगी?" },
  stuck_body: { en: "Your trainer will see this and help you.", hi: "आपके ट्रेनर यह देखेंगे और आपकी मदद करेंगे।" },
  reason_unclear: { en: "The lesson wasn't clear", hi: "पाठ समझ नहीं आया" },
  reason_need_example: { en: "I need a real example", hi: "असली उदाहरण चाहिए" },
  reason_language: { en: "Explain in my language", hi: "मेरी भाषा में समझाएँ" },
  reason_other: { en: "Something else", hi: "कुछ और" },
  note_placeholder: { en: "Want to add anything? (optional)", hi: "कुछ और बताना है? (ज़रूरी नहीं)" },
  send_trainer: { en: "Ask my trainer", hi: "ट्रेनर से पूछें" },
  sending: { en: "Sending…", hi: "भेज रहे हैं…" },
  help_sent_title: { en: "{trainer} has been told", hi: "{trainer} को बता दिया गया है" },
  help_sent_body: {
    en: "Trainers usually reply within a day. You can keep learning meanwhile. This topic is saved for later.",
    hi: "ट्रेनर आमतौर पर एक दिन में जवाब देते हैं। तब तक आप सीखना जारी रख सकते हैं। यह विषय बाद के लिए सहेजा गया है।",
  },
  waiting_title: { en: "{trainer} will help with this", hi: "{trainer} इसमें मदद करेंगे" },
  waiting_body: { en: "{c}. Their reply will show up in Messages.", hi: "{c}। उनका जवाब मैसेज में दिखेगा।" },
  nav_home: { en: "Home", hi: "होम" },
  nav_progress: { en: "Progress", hi: "प्रगति" },
  nav_messages: { en: "Messages", hi: "मैसेज" },
  progress_title: { en: "My skill path", hi: "मेरा स्किल रास्ता" },
  progress_body: {
    en: "Your modules, and how strong each topic is. Keep going from Home.",
    hi: "आपके मॉड्यूल, और हर विषय कितना पक्का है। आगे बढ़ने के लिए होम पर जाएँ।",
  },
  band_strong: { en: "Strong", hi: "पक्का" },
  band_getting: { en: "Getting there", hi: "लगभग" },
  band_practice: { en: "Needs practice", hi: "अभ्यास चाहिए" },
  band_new: { en: "Not started", hi: "शुरू नहीं" },
  confirmed: { en: "Confirmed", hi: "पक्का हुआ" },
  st_done: { en: "Done", hi: "पूरा" },
  st_now: { en: "Now", hi: "अभी" },
  st_next: { en: "Coming up", hi: "आगे" },
  st_skipped: { en: "Already known", hi: "पहले से आता है" },
  messages_title: { en: "Messages", hi: "मैसेज" },
  no_messages: {
    en: "No messages yet. When you ask for help, your trainer's reply will appear here.",
    hi: "अभी कोई मैसेज नहीं। मदद माँगने पर ट्रेनर का जवाब यहाँ आएगा।",
  },
  open_x: { en: "Open: {title}", hi: "खोलें: {title}" },
  checkin: { en: "Meet: {x}", hi: "मुलाकात: {x}" },
  all_done: { en: "You've finished every module in this track!", hi: "आपने इस ट्रैक के सारे मॉड्यूल पूरे कर लिए!" },
  correct_answer: { en: "Right answer", hi: "सही जवाब" },
  you_chose: { en: "You chose", hi: "आपने चुना" },
  you_unsure: { en: "You weren't sure", hi: "आपको पता नहीं था" },
  new_message: { en: "New message from {trainer}", hi: "{trainer} का नया मैसेज" },
  read: { en: "Read", hi: "पढ़ें" },
  lang_switch: { en: "हिंदी", hi: "English" },
  about_topic: { en: "About: {c}", hi: "विषय: {c}" },
} satisfies Record<string, L>;

export type StrKey = keyof typeof S;

export function format(s: string, vars?: Record<string, string | number>) {
  return vars ? s.replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? "")) : s;
}

export function translate(lang: Lang) {
  return {
    lang,
    t: (k: StrKey, vars?: Record<string, string | number>) => format(S[k][lang], vars),
    tx: (l: L, vars?: Record<string, string | number>) => format(l[lang], vars),
  };
}

export function useT() {
  const me = useMe();
  return translate(me.lang);
}
