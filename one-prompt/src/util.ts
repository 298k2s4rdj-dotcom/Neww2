import { Easing, interpolate, random } from "remotion";
import { FPS } from "./config";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** Eased 0→1 progress between two frames. */
export const ease = (frame: number, from: number, to: number, easing = Easing.inOut(Easing.cubic)) =>
  interpolate(frame, [from, to], [0, 1], { ...clamp, easing });

/** Linear clamped interpolation shortcut. */
export const lerpF = (frame: number, input: number[], output: number[]) =>
  interpolate(frame, input, output, clamp);

export const mix = (a: number, b: number, t: number) => a + (b - a) * t;

/** Fade in over `inF` frames, fade out over the last `outF` frames of `dur`. */
export const fadeInOut = (frame: number, dur: number, inF = 10, outF = 10) =>
  Math.min(lerpF(frame, [0, inF], [0, 1]), lerpF(frame, [dur - outF, dur], [1, 0]));

/** Deterministic blink amount 0..1 (1 = eyes closed). */
export const blinkAt = (frame: number, seed: number) => {
  const period = 95 + Math.floor(random(`blink-${seed}`) * 50);
  const phase = (frame + Math.floor(random(`blink-o-${seed}`) * period)) % period;
  if (phase >= 7) return 0;
  return phase < 3 ? phase / 3 : phase < 4 ? 1 : (7 - phase) / 3;
};

/** Idle breathing value in -1..1. */
export const breath = (frame: number, seed = 0) => Math.sin((frame / FPS) * 2.1 + seed * 1.7);

/** Characters typed so far. */
export const typed = (frame: number, cps: number) => Math.max(0, Math.floor((frame / FPS) * cps));
