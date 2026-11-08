import type { Arm } from "./Character";

/** Both hands typing on a laptop in front of a seated character. */
export const typing = (frame: number, active = true): { armFront: Arm; armBack: Arm } => ({
  armFront: { s: 55, e: 40 + (active ? Math.sin(frame * 1.1) * 8 : 0) },
  armBack: { s: 50, e: 46 + (active ? Math.cos(frame * 1.3) * 8 : 0) },
});

/** Arms resting on the lap. */
export const lap: { armFront: Arm; armBack: Arm } = {
  armFront: { s: 30, e: 50 },
  armBack: { s: 25, e: 55 },
};

/** Arms hanging. */
export const hang: { armFront: Arm; armBack: Arm } = {
  armFront: { s: -4, e: 6 },
  armBack: { s: 4, e: 6 },
};

/** Hands on hips (proud). */
export const hips: { armFront: Arm; armBack: Arm } = {
  armFront: { s: -20, e: 120 },
  armBack: { s: -40, e: -110 },
};

/** Lerp between two arm poses. */
export const lerpArm = (a: Arm, b: Arm, t: number): Arm => ({ s: a.s + (b.s - a.s) * t, e: a.e + (b.e - a.e) * t });
