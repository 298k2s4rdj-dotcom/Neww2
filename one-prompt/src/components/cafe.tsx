import { FPS } from "../config";
import type { Arm } from "./Character";
import { CAFE } from "./Sets";

export type Line = { who: string; at: number; to: number; text: string };

/** Is `who` currently talking (typing phase of their bubble)? t in seconds. */
export const isTalking = (lines: readonly Line[], who: string, t: number) =>
  lines.some((l) => l.who === who && t >= l.at && t < Math.min(l.to, l.at + 0.3 + l.text.length / 32));

/** Small gesturing arm while talking. */
export const talkArm = (frame: number, talking: boolean, rest: Arm): Arm =>
  talking ? { s: rest.s + 25 + Math.sin(frame / 5) * 12, e: rest.e + 35 + Math.sin(frame / 4) * 10 } : rest;

/** Bubble anchor above each café seat. */
export const cafeAnchor = (side: "left" | "right") =>
  side === "left"
    ? { x: CAFE.maxX + 40, y: CAFE.ground - 470 * CAFE.scale - 25, tail: 0.22 }
    : { x: CAFE.lenaX - 40, y: CAFE.ground - 470 * CAFE.scale - 25, tail: 0.78 };

export const secs = (frame: number) => frame / FPS;
