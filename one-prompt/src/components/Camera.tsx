import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { ease } from "../util";

/** Slow eased push-in / pan for the whole shot. */
export const Camera: React.FC<{
  children: React.ReactNode;
  from?: number;
  to?: number;
  originX?: number;
  originY?: number;
  panX?: number;
}> = ({ children, from = 1, to = 1.05, originX = 960, originY = 600, panX = 0 }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const t = ease(frame, 0, durationInFrames);
  const s = from + (to - from) * t;
  return (
    <AbsoluteFill
      style={{
        transform: `translateX(${panX * t}px) scale(${s})`,
        transformOrigin: `${originX}px ${originY}px`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

/** Short fade from/to black at the edges of a Sequence. */
export const Fade: React.FC<{ children: React.ReactNode; inF?: number; outF?: number }> = ({
  children,
  inF = 8,
  outF = 0,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const a = inF > 0 ? Math.min(1, frame / inF) : 1;
  const b = outF > 0 ? Math.min(1, (durationInFrames - frame) / outF) : 1;
  return <AbsoluteFill style={{ opacity: Math.max(0, Math.min(a, b)), background: "transparent" }}>{children}</AbsoluteFill>;
};

/** Full 1920x1080 SVG stage. */
export const Stage: React.FC<{ children: React.ReactNode; background?: string }> = ({ children, background = "#000" }) => (
  <AbsoluteFill style={{ background }}>
    <svg viewBox="0 0 1920 1080" width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
      {children}
    </svg>
  </AbsoluteFill>
);
