import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { SANS } from "../fonts";
import { fadeInOut, typed } from "../util";

/** Small on-screen caption, e.g. "1 MONTH LATER". */
export const Caption: React.FC<{ text: string; top?: number }> = ({ text, top = 70 }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const n = typed(frame, 22);
  return (
    <div
      style={{
        position: "absolute",
        top,
        left: 0,
        right: 0,
        textAlign: "center",
        opacity: fadeInOut(frame, durationInFrames, 8, 12),
      }}
    >
      <span
        style={{
          fontFamily: SANS,
          fontWeight: 800,
          letterSpacing: 10,
          fontSize: 38,
          color: "white",
          background: "rgba(0,0,0,0.55)",
          padding: "14px 28px",
          borderRadius: 8,
        }}
      >
        {text.slice(0, n)}
        <span style={{ color: "transparent" }}>{text.slice(n)}</span>
      </span>
    </div>
  );
};
