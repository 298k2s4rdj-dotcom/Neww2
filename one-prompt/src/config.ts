/**
 * ONE PROMPT – timing config.
 *
 * Every time value is in SECONDS. Scene beats are relative to the start of
 * their scene. Change a scene's `duration` and the whole film re-flows
 * (later scenes shift automatically). Keep beats inside their scene's duration.
 */

export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;

/** seconds → frames */
export const f = (seconds: number) => Math.round(seconds * FPS);

/** Length of every title card (fade in + hold + fade out). */
export const TITLE_CARD = 3;
/** Typewriter speed for bubbles and screens (characters per second). */
export const TYPE_CPS = 32;

export const SCENES = {
  /** 0:00–0:40 */
  scene1: {
    duration: 40,
    title: { at: 0, text: "Motivation is loud. Habits are quiet." },
    cafe: { from: 3, to: 22 },
    lines: [
      { who: "max", at: 4.5, to: 9, text: "I'm learning AI. ALL of it." },
      { who: "lena", at: 9.5, to: 12.5, text: "All of it?" },
      { who: "max", at: 13, to: 20.5, text: "30-day course. 3 hours a day. Starting Monday." },
    ],
    apartment: { from: 22, to: 31 }, // MAX pins the wall chart
    pinAt: 25.5,
    chartCloseup: { from: 31, to: 34.5 },
    laptopCloseup: { from: 34.5, to: 40 }, // tabs + "Course $199"
  },

  /** 0:40–1:40 */
  scene2: {
    duration: 60,
    moduleCloseup: { from: 0, to: 4 }, // "Module 1 of 47 – 2h 38min"
    sigh: { from: 4, to: 8 },
    montageStart: 8,
    /** each beat: MAX shot (`shot` s) then chart closeup adding X's (`chart` s) */
    beatShot: 5,
    beatChart: 2.5,
    beats: [
      { thought: "Too tired.", place: "sofa", time: "night" },
      { thought: "Tomorrow.", place: "desk", time: "evening" },
      { thought: "Need a better laptop first.", place: "desk", time: "day" },
      { thought: "Watched 3 videos about it. Counts?", place: "sofa", time: "night" },
      { thought: "Weekend. Fresh start.", place: "fridge", time: "day" },
    ],
    crumple: { from: 45.5, to: 60, grabAt: 1, crumpleAt: 2, throwAt: 4.5, thoughtAt: 7, thoughtTo: 12.5 },
    thought: "AI just isn't for me.",
  },

  /** 1:40–2:20 */
  scene3: {
    duration: 40,
    title: { at: 0, text: "Every expert was once a beginner who didn't quit." },
    cafe: { from: 3, to: 27 },
    caption: { at: 3.3, to: 6.5, text: "1 MONTH LATER" },
    lines: [
      { who: "max", at: 4.5, to: 9, text: "Took me an hour to write one email to my landlord." },
      { who: "lena", at: 9.3, to: 12.3, text: "Did you ever finish the course?" },
      { who: "max", at: 12.6, to: 15, text: "Never even started." },
      { who: "lena", at: 15.8, to: 20.6, text: "Forget the course. Paste the email. Ask for help. One prompt." },
      { who: "max", at: 20.9, to: 22.8, text: "That's it?" },
      { who: "lena", at: 23, to: 27, text: "One prompt a day. That's the whole plan." },
    ],
    phoneSlide: 15,
    apartment: { from: 27, to: 32, pullAt: 0.6, flipAt: 3 },
    marker: { from: 32, to: 40, writeFrom: 0.6, writeTo: 4.5 },
  },

  /** 2:20–3:30 – music fades up here */
  scene4: {
    duration: 70,
    morning: { from: 0, to: 10, alarmAt: 0.4, thoughtAt: 4, thoughtTo: 8.5 },
    chat: {
      from: 10, to: 21,
      prompt: "Make this email polite but firm.",
      reply:
        "Dear Mr. Becker,\nThe kitchen tap has been leaking for three weeks. Please arrange a repair by Friday. Thank you for taking care of this quickly.",
      replyAt: 4.5,
    },
    smile: { from: 21, to: 24 },
    firstCheck: { from: 24, to: 26 },
    montageStart: 26,
    /** each beat: shot, then laptop closeup with prompt, then chart check */
    beats: [
      {
        place: "fridge",
        prompt: "Recipe from what's in my fridge",
        reply: "Veggie omelette: 3 eggs, spinach, tomato, cheese. Ready in 10 minutes.",
        shot: 2.5, screen: 3.5, check: 1.5,
      },
      {
        place: "desk",
        prompt: "Summarize this PDF",
        reply: "3 key points:\n• Rent rises 2% in March\n• Repairs within 14 days\n• Notice period: 3 months",
        shot: 2, screen: 3.5, check: 1.5,
      },
      {
        place: "sofa",
        prompt: "Explain taxes like I'm 12",
        reply: "Imagine your paycheck is a pizza. Taxes are the slices that pay for roads, schools and parks.",
        shot: 2, screen: 3.5, check: 1.5,
      },
      { place: "office", prompt: "", reply: "", shot: 5, screen: 0, check: 1.5 },
    ],
    /** prompts/day counter: [secondsIntoScene, value] */
    counter: [
      [26, 1],
      [33.5, 2],
      [40.5, 5],
      [47.5, 7],
      [54, 10],
    ] as [number, number][],
    fillUp: { from: 54, to: 70, chartFrom: 62 },
  },

  /** 3:30–4:10 */
  scene5: {
    duration: 40,
    goal: { from: 0, to: 12, text: "MASTER 10 AI TOOLS THIS MONTH", lookFrom: 5.5, lookTo: 8.5, deleteAt: 9 },
    rain: { from: 12, to: 37, thoughtAt: 3, thoughtTo: 7, typeAt: 8, checkAt: 12.5 },
    thought: "Just one.",
    title: { at: 37, text: "Small enough to start. Consistent enough to win." },
  },

  /** 4:10–4:40 */
  scene6: {
    duration: 30,
    cafe: { from: 0, to: 19 },
    lines: [
      { who: "friend", at: 2.5, to: 6.5, text: "How did you get so good at AI?" },
      { who: "max", at: 7, to: 13, text: "I didn't try to get good. I just did one prompt a day." },
    ],
    phoneSlide: 13.2,
    lenaSmile: 15,
    finalCard: { from: 19, to: 26 },
    endCard: { from: 26, to: 30, handle: "@howtowithai" },
  },
} as const;

export type SceneKey = keyof typeof SCENES;
export const SCENE_ORDER: SceneKey[] = ["scene1", "scene2", "scene3", "scene4", "scene5", "scene6"];

/** Start (in seconds) of each scene in the film. */
export const sceneStart = (key: SceneKey) => {
  let t = 0;
  for (const k of SCENE_ORDER) {
    if (k === key) return t;
    t += SCENES[k].duration;
  }
  return t;
};

export const TOTAL_SECONDS = SCENE_ORDER.reduce((a, k) => a + SCENES[k].duration, 0);

/** Music: quiet bed in scenes 1–3, fades up over the first seconds of scene 4. */
export const MUSIC = {
  baseVolume: 0.12,
  fullVolume: 0.5,
  fadeUpSeconds: 6,
  fadeOutSeconds: 4,
};
