import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { TYPE_CPS } from "../config";
import { SANS } from "../fonts";
import { lerpF, typed } from "../util";

type BubbleProps = {
  /** tail tip position (px, 1920x1080 space) */
  x: number;
  y: number;
  text: string;
  /** total frames the bubble is visible */
  durationInFrames: number;
  kind?: "speech" | "thought";
  /** where the tail sits along the bubble's width, 0..1 */
  tail?: number;
  maxWidth?: number;
  fontSize?: number;
};

/**
 * White rounded speech bubble (with tail) or thought bubble (with trailing
 * circles). Pops in with a spring, types its text, fades out at the end.
 * Untyped characters are rendered transparent so the bubble never resizes.
 */
export const Bubble: React.FC<BubbleProps> = ({
  x,
  y,
  text,
  durationInFrames,
  kind = "speech",
  tail = 0.5,
  maxWidth = 620,
  fontSize = 40,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 13, stiffness: 170, mass: 0.7 } });
  const out = lerpF(frame, [durationInFrames - 8, durationInFrames], [1, 0]);
  const n = typed(Math.max(0, frame - 5), TYPE_CPS);
  const shown = text.slice(0, n);
  const hidden = text.slice(n);
  const thought = kind === "thought";
  const lift = thought ? 70 : 34;

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: 0,
        height: 0,
        opacity: out,
        transform: `scale(${0.4 + pop * 0.6})`,
        transformOrigin: "0 0",
      }}
    >
      <div
        style={{
          position: "absolute",
          bottom: lift,
          left: 0,
          transform: `translateX(${-tail * 100}%)`,
          background: "white",
          color: "#111",
          fontFamily: SANS,
          fontWeight: 600,
          fontSize,
          lineHeight: 1.25,
          padding: thought ? "30px 44px" : "24px 34px",
          borderRadius: thought ? 999 : 36,
          width: "max-content",
          maxWidth,
          textAlign: "left",
          boxShadow: "0 10px 30px rgba(0,0,0,0.25)",
          whiteSpace: "pre-wrap",
        }}
      >
        <span>{shown}</span>
        <span style={{ color: "transparent" }}>{hidden}</span>
      </div>
      {thought ? (
        <>
          <div style={dot(26, -13, -58)} />
          <div style={dot(17, -8, -30)} />
          <div style={dot(10, -5, -10)} />
        </>
      ) : (
        <svg width={60} height={42} style={{ position: "absolute", left: -18, top: -lift - 2, overflow: "visible" }}>
          <path d="M 0 0 L 40 0 Q 26 22 18 42 Q 14 20 0 0 Z" fill="white" />
        </svg>
      )}
    </div>
  );
};

const dot = (size: number, left: number, top: number): React.CSSProperties => ({
  position: "absolute",
  width: size,
  height: size,
  left,
  top,
  borderRadius: "50%",
  background: "white",
  boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
});
