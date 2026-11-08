import React from "react";
import { useCurrentFrame } from "remotion";
import { PALETTE, TimeOfDay } from "./palette";
import { Rain } from "./Rain";

/** Apartment window showing day / evening / night / morning / rain. */
export const Window: React.FC<{ x: number; y: number; w: number; h: number; time: TimeOfDay; id: string }> = ({
  x,
  y,
  w,
  h,
  time,
  id,
}) => {
  const frame = useCurrentFrame();
  const pal = PALETTE[time];
  const drift = (frame * 0.4) % (w + 300);
  const clip = `win-clip-${id}`;
  const grad = `win-sky-${id}`;
  return (
    <g>
      <defs>
        <linearGradient id={grad} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={pal.sky[0]} />
          <stop offset="1" stopColor={pal.sky[1]} />
        </linearGradient>
        <clipPath id={clip}>
          <rect x={x} y={y} width={w} height={h} />
        </clipPath>
      </defs>
      <rect x={x - 18} y={y - 18} width={w + 36} height={h + 36} rx={6} fill="#f6f1e8" opacity={time === "night" || time === "rain" ? 0.55 : 0.95} />
      <rect x={x} y={y} width={w} height={h} fill={`url(#${grad})`} />
      <g clipPath={`url(#${clip})`}>
        {time === "day" && (
          <>
            <circle cx={x + w * 0.75} cy={y + h * 0.25} r={40} fill="#fff6c9" />
            {[0, 1].map((i) => (
              <g key={i} transform={`translate(${x - 150 + ((drift + i * 260) % (w + 300))} ${y + 70 + i * 90})`} fill="white" opacity={0.9}>
                <ellipse cx={0} cy={0} rx={60} ry={20} />
                <ellipse cx={30} cy={-14} rx={36} ry={22} />
              </g>
            ))}
          </>
        )}
        {time === "morning" && <circle cx={x + w * 0.3} cy={y + h * 0.78} r={52} fill="#fff1c4" opacity={0.95} />}
        {time === "evening" && <circle cx={x + w * 0.6} cy={y + h * 0.82} r={46} fill="#ffd27a" opacity={0.9} />}
        {time === "night" && (
          <>
            <circle cx={x + w * 0.72} cy={y + h * 0.26} r={30} fill="#f3f0d8" />
            <circle cx={x + w * 0.72 + 12} cy={y + h * 0.26 - 8} r={27} fill={pal.sky[0]} />
            {Array.from({ length: 14 }).map((_, i) => (
              <circle
                key={i}
                cx={x + ((i * 97) % w)}
                cy={y + ((i * 53) % (h * 0.7))}
                r={1.8}
                fill="white"
                opacity={0.5 + 0.5 * Math.sin(frame / 12 + i)}
              />
            ))}
          </>
        )}
        {/* skyline silhouette */}
        <path
          d={`M ${x} ${y + h} L ${x} ${y + h * 0.78} L ${x + w * 0.15} ${y + h * 0.78} L ${x + w * 0.15} ${y + h * 0.66} L ${x + w * 0.32} ${y + h * 0.66} L ${x + w * 0.32} ${y + h * 0.82} L ${x + w * 0.5} ${y + h * 0.82} L ${x + w * 0.5} ${y + h * 0.6} L ${x + w * 0.62} ${y + h * 0.6} L ${x + w * 0.62} ${y + h * 0.74} L ${x + w * 0.85} ${y + h * 0.74} L ${x + w * 0.85} ${y + h * 0.68} L ${x + w} ${y + h * 0.68} L ${x + w} ${y + h} Z`}
          fill="#000"
          opacity={time === "day" || time === "morning" ? 0.18 : 0.45}
        />
        {(time === "night" || time === "rain" || time === "evening") &&
          [0.2, 0.38, 0.55, 0.7, 0.9].map((fx, i) => (
            <rect key={i} x={x + w * fx} y={y + h * (0.7 + (i % 2) * 0.08)} width={7} height={9} fill="#ffd98a" opacity={0.7} />
          ))}
        {time === "rain" && <Rain x={x} y={y} width={w} height={h} count={70} opacity={0.8} seed={`win-${id}`} />}
      </g>
      <rect x={x + w / 2 - 5} y={y} width={10} height={h} fill="#f6f1e8" opacity={0.9} />
      <rect x={x} y={y + h * 0.45 - 5} width={w} height={10} fill="#f6f1e8" opacity={0.9} />
      <rect x={x - 30} y={y + h + 14} width={w + 60} height={16} rx={4} fill="#efe7da" opacity={0.85} />
    </g>
  );
};
