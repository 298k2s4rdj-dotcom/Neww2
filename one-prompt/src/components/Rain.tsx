import React from "react";
import { random, useCurrentFrame } from "remotion";

/** Deterministic falling rain streaks, drawn inside an SVG. */
export const Rain: React.FC<{
  x?: number;
  y?: number;
  width: number;
  height: number;
  count?: number;
  opacity?: number;
  seed?: string;
  slant?: number;
}> = ({ x = 0, y = 0, width, height, count = 160, opacity = 0.55, seed = "rain", slant = 0.18 }) => {
  const frame = useCurrentFrame();
  const drops = [];
  for (let i = 0; i < count; i++) {
    const r1 = random(`${seed}-x-${i}`);
    const r2 = random(`${seed}-y-${i}`);
    const r3 = random(`${seed}-s-${i}`);
    const len = 18 + r3 * 26;
    const speed = 22 + r3 * 18;
    const travel = height + len;
    const dy = (r2 * travel + frame * speed) % travel;
    const dx = (r1 * (width + 200) - 100 - dy * slant + width * 10) % (width + 200) - 100;
    drops.push(
      <line
        key={i}
        x1={x + dx}
        y1={y + dy - len}
        x2={x + dx - len * slant}
        y2={y + dy}
        stroke="#cfe3ff"
        strokeWidth={1.5 + r3 * 1.5}
        strokeLinecap="round"
        opacity={opacity * (0.5 + r3 * 0.5)}
      />,
    );
  }
  return <g>{drops}</g>;
};
