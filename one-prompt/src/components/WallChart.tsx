import React from "react";
import { MARKER, SANS } from "../fonts";

export const CHART_W = 300;
export const CHART_H = 390;

const COLS = 6;
const ROWS = 5;
const CELL = 40;
const GAP = 6;
const GRID_X = (CHART_W - (COLS * CELL + (COLS - 1) * GAP)) / 2;

const cellPos = (i: number, gridY: number) => ({
  cx: GRID_X + (i % COLS) * (CELL + GAP) + CELL / 2,
  cy: gridY + Math.floor(i / COLS) * (CELL + GAP) + CELL / 2,
});

/** Draws a stroke progressively (0..1) using pathLength normalisation. */
const Stroke: React.FC<{ d: string; p: number; color: string; w: number }> = ({ d, p, color, w }) =>
  p <= 0 ? null : (
    <path
      d={d}
      pathLength={1}
      strokeDasharray={1}
      strokeDashoffset={1 - Math.min(1, p)}
      stroke={color}
      strokeWidth={w}
      strokeLinecap="round"
      strokeLinejoin="round"
      fill="none"
    />
  );

/**
 * The habit chart on the wall.
 * front: "30 DAYS TO AI MASTERY" with `xs` red crosses (fractional = drawing).
 * back:  hand-written red "1 PROMPT" (`marker` 0..1 write-on) with `checks` green ticks.
 * Local coordinates: (0,0) top-left, CHART_W x CHART_H.
 */
export const WallChart: React.FC<{
  x: number;
  y: number;
  scale?: number;
  side?: "front" | "back";
  xs?: number;
  checks?: number;
  marker?: number;
  rotate?: number;
  /** horizontal squash for the flip animation, -1..1 */
  flipX?: number;
  pin?: boolean;
  id: string;
  opacity?: number;
}> = ({ x, y, scale = 1, side = "front", xs = 0, checks = 0, marker = 1, rotate = 0, flipX = 1, pin = true, id, opacity = 1 }) => {
  const front = side === "front";
  const clip = `marker-clip-${id}`;
  const gridY = front ? 132 : 150;
  return (
    <g
      transform={`translate(${x} ${y}) rotate(${rotate}) scale(${scale * flipX} ${scale}) translate(${-CHART_W / 2} 0)`}
      opacity={opacity}
    >
      <rect x={4} y={6} width={CHART_W} height={CHART_H} fill="#000" opacity={0.18} />
      <rect x={0} y={0} width={CHART_W} height={CHART_H} fill={front ? "#fbf8f1" : "#f1ece0"} />
      {front ? (
        <>
          <text x={CHART_W / 2} y={52} textAnchor="middle" fontFamily={SANS} fontWeight={800} fontSize={27} fill="#1b1b1b">
            30 DAYS TO
          </text>
          <text x={CHART_W / 2} y={88} textAnchor="middle" fontFamily={SANS} fontWeight={800} fontSize={30} fill="#1b1b1b">
            AI MASTERY
          </text>
          <rect x={GRID_X} y={102} width={CHART_W - GRID_X * 2} height={5} fill="#3d7bfd" />
          {Array.from({ length: COLS * ROWS }).map((_, i) => {
            const { cx, cy } = cellPos(i, gridY);
            const p = Math.max(0, Math.min(1, xs - i));
            return (
              <g key={i}>
                <rect x={cx - CELL / 2} y={cy - CELL / 2} width={CELL} height={CELL} fill="none" stroke="#9aa0a8" strokeWidth={2} rx={3} />
                <text x={cx - CELL / 2 + 4} y={cy - CELL / 2 + 12} fontFamily={SANS} fontSize={10} fill="#9aa0a8">
                  {i + 1}
                </text>
                <Stroke d={`M ${cx - 13} ${cy - 13} L ${cx + 13} ${cy + 13}`} p={p * 2} color="#e02424" w={6} />
                <Stroke d={`M ${cx + 13} ${cy - 13} L ${cx - 13} ${cy + 13}`} p={p * 2 - 1} color="#e02424" w={6} />
              </g>
            );
          })}
        </>
      ) : (
        <>
          {/* creases from being crumpled */}
          <path d="M 0 120 L 90 160 L 170 110 L 300 170 M 60 0 L 110 140 L 80 390 M 230 0 L 200 200 L 250 390 M 0 300 L 140 270 L 300 320" stroke="#d8d0bf" strokeWidth={2} fill="none" />
          <defs>
            <clipPath id={clip}>
              <rect x={0} y={0} width={CHART_W * marker} height={CHART_H} />
            </clipPath>
          </defs>
          <g clipPath={`url(#${clip})`}>
            <text x={CHART_W / 2} y={108} textAnchor="middle" fontFamily={MARKER} fontSize={54} fill="#e02424" transform="rotate(-3 150 90)" textLength={262} lengthAdjust="spacingAndGlyphs">
              1 PROMPT
            </text>
          </g>
          {/* hand-drawn grid fades in after the title */}
          <g opacity={Math.max(0, Math.min(1, (marker - 0.85) / 0.15))}>
            {Array.from({ length: COLS * ROWS }).map((_, i) => {
              const { cx, cy } = cellPos(i, gridY);
              const jitter = ((i * 37) % 7) - 3;
              return (
                <rect key={i} x={cx - CELL / 2 + jitter * 0.3} y={cy - CELL / 2} width={CELL - 2} height={CELL - 2} fill="none" stroke="#e02424" strokeOpacity={0.45} strokeWidth={2.5} rx={6} transform={`rotate(${jitter * 0.6} ${cx} ${cy})`} />
              );
            })}
          </g>
          {Array.from({ length: COLS * ROWS }).map((_, i) => {
            const p = Math.max(0, Math.min(1, checks - i));
            if (p <= 0) return null;
            const { cx, cy } = cellPos(i, gridY);
            const s = 0.6 + Math.min(1, p * 1.6) * 0.4 + Math.sin(Math.min(1, p) * Math.PI) * 0.25;
            return (
              <g key={`c${i}`} transform={`translate(${cx} ${cy}) scale(${s})`}>
                <Stroke d="M -13 1 L -4 11 L 15 -12" p={p * 1.3} color="#16a34a" w={7} />
              </g>
            );
          })}
          {marker > 0 && marker < 1 && (
            <g transform={`translate(${CHART_W * marker - 8} 70) rotate(28)`}>
              <rect x={-9} y={0} width={18} height={110} rx={6} fill="#222" />
              <rect x={-9} y={0} width={18} height={26} rx={6} fill="#e02424" />
              <path d="M -6 0 L 0 -16 L 6 0 Z" fill="#e02424" />
            </g>
          )}
        </>
      )}
      {pin && (
        <g>
          <circle cx={CHART_W / 2} cy={14} r={11} fill="#d63031" />
          <circle cx={CHART_W / 2 - 3} cy={11} r={3.5} fill="white" opacity={0.6} />
        </g>
      )}
    </g>
  );
};
