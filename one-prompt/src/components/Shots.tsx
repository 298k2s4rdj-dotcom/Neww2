import React from "react";
import { AbsoluteFill, Sequence, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { f, FPS } from "../config";
import { SANS } from "../fonts";
import { Bubble } from "./Bubble";
import { Sound } from "./Sound";
import { Camera, Stage } from "./Camera";
import { PALETTE, TimeOfDay } from "./palette";
import { WallChart } from "./WallChart";

/** Sequence expressed in seconds: [from, to). */
export const Shot: React.FC<{ from: number; to: number; children: React.ReactNode; name?: string }> = ({ from, to, children, name }) => (
  <Sequence from={f(from)} durationInFrames={Math.max(1, f(to) - f(from))} name={name}>
    {children}
  </Sequence>
);

/** Bubble shown between two times (seconds, relative to the parent sequence). */
export const Say: React.FC<{
  at: number;
  to: number;
  x: number;
  y: number;
  text: string;
  kind?: "speech" | "thought";
  tail?: number;
  maxWidth?: number;
}> = ({ at, to, ...rest }) => (
  <Sequence from={f(at)} durationInFrames={f(to) - f(at)} layout="none" name={`“${rest.text}”`}>
    <AbsoluteFill>
      <Bubble durationInFrames={f(to) - f(at)} {...rest} />
    </AbsoluteFill>
    <Sound name="pop" volume={rest.kind === "thought" ? 0.12 : 0.18} />
  </Sequence>
);

/** Full-screen closeup of the wall chart. */
export const ChartCloseup: React.FC<{
  time?: TimeOfDay;
  side: "front" | "back";
  xs?: (frame: number) => number;
  checks?: (frame: number) => number;
  marker?: (frame: number) => number;
  id: string;
}> = ({ time = "day", side, xs, checks, marker, id }) => {
  const frame = useCurrentFrame();
  const pal = PALETTE[time];
  return (
    <Camera from={1} to={1.04} originY={500}>
      <Stage background={pal.wall[1]}>
        <defs>
          <radialGradient id={`cc-${id}`} cx="0.5" cy="0.45" r="0.7">
            <stop offset="0" stopColor={pal.wall[0]} />
            <stop offset="1" stopColor={pal.wall[1]} />
          </radialGradient>
        </defs>
        <rect width={1920} height={1080} fill={`url(#cc-${id})`} />
        <WallChart
          id={id}
          x={960}
          y={110}
          scale={2.18}
          side={side}
          xs={xs ? xs(frame) : 0}
          checks={checks ? checks(frame) : 0}
          marker={marker ? marker(frame) : 1}
        />
      </Stage>
    </Camera>
  );
};

/** "prompts/day" counter pill, top-right. */
export const PromptCounter: React.FC<{ steps: [number, number][]; offset: number }> = ({ steps, offset }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / FPS + offset;
  let idx = 0;
  steps.forEach(([at], i) => {
    if (t >= at) idx = i;
  });
  const [stepAt, value] = steps[idx];
  const pop = spring({ frame: frame - (stepAt - offset) * FPS, fps, config: { damping: 8, stiffness: 200 } });
  const appear = spring({ frame, fps, config: { damping: 14 } });
  return (
    <div
      style={{
        position: "absolute",
        top: 50,
        right: 60,
        transform: `scale(${appear * (1 + (1 - pop) * 0.25)})`,
        transformOrigin: "100% 0",
        background: "rgba(255,255,255,0.95)",
        borderRadius: 40,
        padding: "14px 30px",
        fontFamily: SANS,
        fontWeight: 800,
        fontSize: 36,
        color: "#111",
        boxShadow: "0 10px 30px rgba(0,0,0,0.25)",
        display: "flex",
        alignItems: "center",
        gap: 14,
      }}
    >
      <span style={{ color: "#16a34a", fontSize: 40 }}>✓</span>
      <span style={{ fontSize: 46 }}>{value}</span>
      <span style={{ fontWeight: 600, color: "#555" }}>{value === 1 ? "prompt/day" : "prompts/day"}</span>
    </div>
  );
};
