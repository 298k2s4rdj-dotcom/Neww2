import React from "react";
import { useCurrentFrame } from "remotion";
import { Character, Mood } from "./Character";
import { hang, lap, typing } from "./poses";
import { APT } from "./Sets";

export type Place = "desk" | "sofa" | "fridge";

/** Bubble anchor (tail tip) above MAX for each apartment place. */
export const MAX_ANCHOR: Record<Place, { x: number; y: number; tail: number }> = {
  desk: { x: APT.deskSeatX + 40, y: APT.floor - 500, tail: 0.25 },
  sofa: { x: APT.sofaSeatX + 20, y: APT.sofaGround - 505, tail: 0.75 },
  fridge: { x: 1120, y: APT.floor - 505, tail: 0.5 },
};

/** MAX in a typical apartment spot. */
export const MaxAt: React.FC<{
  place: Place;
  mood?: Mood;
  slump?: number;
  typingOn?: boolean;
  phone?: boolean;
  lookX?: number;
  lookY?: number;
}> = ({ place, mood = "neutral", slump = 0, typingOn = false, phone = false, lookX = 0.8, lookY = 0 }) => {
  const frame = useCurrentFrame();
  if (place === "desk") {
    return (
      <Character look="max" x={APT.deskSeatX} y={APT.floor} sitting mood={mood} slump={slump} lookX={lookX} lookY={lookY} {...typing(frame, typingOn)} seed={1} />
    );
  }
  if (place === "sofa") {
    return (
      <Character
        look="max"
        x={APT.sofaSeatX}
        y={APT.sofaGround}
        sitting
        mood={mood}
        slump={slump}
        lean={-8}
        lookX={lookX}
        lookY={phone ? 0.8 : lookY}
        armFront={phone ? { s: 60, e: 85 } : lap.armFront}
        armBack={phone ? { s: 50, e: 90 } : lap.armBack}
        holding={phone ? <rect x={-6} y={-38} width={22} height={40} rx={5} fill="#111" stroke="#9fd8ff" strokeWidth={3} /> : undefined}
        seed={1}
      />
    );
  }
  return (
    <Character look="max" x={1120} y={APT.floor} mood={mood} slump={slump} lookX={lookX} lookY={lookY} armFront={{ s: 70, e: 20 }} armBack={hang.armBack} seed={1} />
  );
};
