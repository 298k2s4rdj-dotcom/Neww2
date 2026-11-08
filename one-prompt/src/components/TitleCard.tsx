import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { SERIF } from "../fonts";
import { ease, fadeInOut } from "../util";
import { Sound } from "./Sound";

/** Full-screen black card with centered white serif text. */
export const TitleCard: React.FC<{ text: string; sub?: string; size?: number; fadeOut?: boolean }> = ({
  text,
  sub,
  size = 78,
  fadeOut = true,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const o = fadeOut ? fadeInOut(frame, durationInFrames, 18, 18) : Math.min(1, frame / 18);
  const rise = (1 - ease(frame, 0, 30)) * 14;
  return (
    <AbsoluteFill style={{ background: "#000", justifyContent: "center", alignItems: "center" }}>
      <Sound name="title-swell" volume={0.22} />
      <div style={{ opacity: o, transform: `translateY(${rise}px)`, textAlign: "center", padding: "0 180px" }}>
        <div style={{ fontFamily: SERIF, color: "white", fontSize: size, lineHeight: 1.3, textWrap: "balance" }}>{text}</div>
        {sub && (
          <div
            style={{
              fontFamily: SERIF,
              fontStyle: "italic",
              color: "rgba(255,255,255,0.82)",
              fontSize: size * 0.55,
              marginTop: 34,
              opacity: ease(frame, 24, 48),
            }}
          >
            {sub}
          </div>
        )}
      </div>
    </AbsoluteFill>
  );
};
