import React from "react";
import { useCurrentFrame } from "remotion";

/** Side-view laptop. (x, y) = bottom center of the base. Screen faces `dir`. */
export const Laptop: React.FC<{ x: number; y: number; scale?: number; dir?: 1 | -1; glow?: number; open?: number }> = ({
  x,
  y,
  scale = 1,
  dir = -1,
  glow = 0.8,
  open = 1,
}) => {
  const angle = -12 - (1 - open) * 78; // degrees from vertical
  return (
    <g transform={`translate(${x} ${y}) scale(${scale * -dir} ${scale})`}>
      {/* soft screen glow on the screen side */}
      <ellipse cx={20} cy={-70} rx={90} ry={70} fill="#bfe4ff" opacity={0.07 * glow} />
      <rect x={-75} y={-10} width={150} height={10} rx={4} fill="#1d1f24" />
      <g transform={`translate(70 -8) rotate(${angle})`}>
        <rect x={-8} y={-118} width={9} height={118} rx={3} fill="#1d1f24" />
        <rect x={-10} y={-112} width={3} height={104} fill="#bfe4ff" opacity={glow} />
      </g>
    </g>
  );
};

/** Smartphone lying flat (seen from above at an angle) */
export const Phone: React.FC<{ x: number; y: number; scale?: number; lit?: boolean }> = ({ x, y, scale = 1, lit = true }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-46} y={-12} width={92} height={18} rx={7} fill="#111" />
    <rect x={-40} y={-11} width={80} height={8} rx={3} fill={lit ? "#9fd8ff" : "#333"} opacity={0.9} />
  </g>
);

/** Waste bin. (x, y) bottom center */
export const Bin: React.FC<{ x: number; y: number; scale?: number }> = ({ x, y, scale = 1 }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -50 -110 L 50 -110 L 40 0 L -40 0 Z" fill="#5d6470" />
    <rect x={-56} y={-118} width={112} height={12} rx={5} fill="#717887" />
    {[-25, 0, 25].map((dx) => (
      <line key={dx} x1={dx} y1={-96} x2={dx * 0.8} y2={-12} stroke="#4a505a" strokeWidth={4} />
    ))}
  </g>
);

/** Crumpled paper ball */
export const PaperBall: React.FC<{ x: number; y: number; r?: number; rot?: number }> = ({ x, y, r = 34, rot = 0 }) => (
  <g transform={`translate(${x} ${y}) rotate(${rot})`}>
    <path
      d={`M ${-r} 0 L ${-r * 0.7} ${-r * 0.75} L ${-r * 0.1} ${-r} L ${r * 0.6} ${-r * 0.8} L ${r} ${-r * 0.1} L ${r * 0.75} ${r * 0.7} L ${r * 0.05} ${r} L ${-r * 0.7} ${r * 0.72} Z`}
      fill="#f4f0e6"
      stroke="#cfc8b8"
      strokeWidth={2}
    />
    <path d={`M ${-r * 0.6} ${-r * 0.2} L ${r * 0.1} ${r * 0.1} L ${r * 0.5} ${-r * 0.5} M ${-r * 0.2} ${r * 0.6} L ${r * 0.1} ${r * 0.1}`} stroke="#c9c1b0" strokeWidth={2} fill="none" />
    <path d={`M ${-r * 0.4} ${-r * 0.4} L ${-r * 0.5} ${-r * 0.1}`} stroke="#d33" strokeWidth={4} opacity={0.7} />
  </g>
);

/** Alarm clock that shakes when ringing */
export const AlarmClock: React.FC<{ x: number; y: number; ringing?: boolean }> = ({ x, y, ringing }) => {
  const frame = useCurrentFrame();
  const shake = ringing ? Math.sin(frame * 2.2) * 6 : 0;
  return (
    <g transform={`translate(${x} ${y}) rotate(${shake})`}>
      <circle cx={-22} cy={-62} r={12} fill="#c0392b" />
      <circle cx={22} cy={-62} r={12} fill="#c0392b" />
      <circle cx={0} cy={-38} r={36} fill="#e74c3c" />
      <circle cx={0} cy={-38} r={27} fill="#fdf6e3" />
      <line x1={0} y1={-38} x2={0} y2={-56} stroke="#222" strokeWidth={4} strokeLinecap="round" />
      <line x1={0} y1={-38} x2={12} y2={-34} stroke="#222" strokeWidth={4} strokeLinecap="round" />
      <line x1={-20} y1={-6} x2={-26} y2={4} stroke="#c0392b" strokeWidth={6} strokeLinecap="round" />
      <line x1={20} y1={-6} x2={26} y2={4} stroke="#c0392b" strokeWidth={6} strokeLinecap="round" />
      {ringing &&
        [-1, 1].map((s) => (
          <g key={s} stroke="#fff" strokeWidth={4} strokeLinecap="round" opacity={0.6 + 0.4 * Math.sin(frame)}>
            <line x1={s * 50} y1={-70} x2={s * 64} y2={-82} />
            <line x1={s * 54} y1={-44} x2={s * 72} y2={-46} />
          </g>
        ))}
    </g>
  );
};

/** Fridge. (x, y) = bottom-left corner. `open` 0..1 swings the door. */
export const Fridge: React.FC<{ x: number; y: number; w?: number; h?: number; open?: number }> = ({
  x,
  y,
  w = 190,
  h = 480,
  open = 0,
}) => (
  <g transform={`translate(${x} ${y - h})`}>
    <rect x={0} y={0} width={w} height={h} rx={14} fill="#dfe4ea" />
    {open > 0 && (
      <g>
        <rect x={8} y={8} width={w - 16} height={h * 0.62} rx={8} fill="#fff9e0" />
        {[0.2, 0.4].map((fy) => (
          <line key={fy} x1={12} x2={w - 12} y1={h * fy} y2={h * fy} stroke="#d8d1b5" strokeWidth={4} />
        ))}
        <circle cx={50} cy={h * 0.17} r={16} fill="#e67e22" />
        <rect x={90} y={h * 0.08} width={26} height={44} rx={6} fill="#ecf0f1" stroke="#bbb" />
        <ellipse cx={130} cy={h * 0.36} rx={30} ry={14} fill="#27ae60" />
        <rect x={40} y={h * 0.44} width={60} height={30} rx={6} fill="#f1c40f" />
      </g>
    )}
    {/* door: hinge on the left, scales towards hinge as it opens */}
    <g transform={`translate(0 0) scale(${1 - open * 1.25} 1)`}>
      <rect x={0} y={0} width={w} height={h * 0.64} rx={14} fill="#e9edf1" stroke="#c7cdd4" strokeWidth={3} />
      <rect x={w - 24} y={h * 0.18} width={10} height={90} rx={5} fill="#aab2bc" />
    </g>
    <rect x={0} y={h * 0.64} width={w} height={h * 0.36} rx={14} fill="#e9edf1" stroke="#c7cdd4" strokeWidth={3} />
    <rect x={w - 24} y={h * 0.7} width={10} height={60} rx={5} fill="#aab2bc" />
  </g>
);

/** Chair, side view. (x, y) = floor point at the back of the seat; seat extends towards `dir`. */
export const Chair: React.FC<{ x: number; y: number; scale?: number; color?: string; dir?: 1 | -1 }> = ({
  x,
  y,
  scale = 1,
  color = "#3a2a20",
  dir = 1,
}) => (
  <g transform={`translate(${x} ${y}) scale(${scale * dir} ${scale})`} fill={color}>
    <rect x={-30} y={-182} width={170} height={16} rx={6} />
    <rect x={-34} y={-370} width={18} height={204} rx={7} />
    <rect x={-22} y={-170} width={12} height={170} />
    <rect x={122} y={-170} width={12} height={170} />
  </g>
);
