import React from "react";
import { AbsoluteFill } from "remotion";
import { Stage } from "./components/Camera";
import { Character } from "./components/Character";
import { ApartmentBackground } from "./components/Sets";
import { WallChart } from "./components/WallChart";
import { SANS } from "./fonts";

/** 1280x720 YouTube thumbnail: MAX looking at the red "1 PROMPT" chart. */
export const Thumbnail: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <AbsoluteFill style={{ transform: "scale(0.6667)", transformOrigin: "0 0", width: 1920, height: 1080 }}>
      <AbsoluteFill style={{ transform: "scale(1.55)", transformOrigin: "1400px 420px" }}>
        <Stage>
          <ApartmentBackground time="evening" />
          <WallChart id="thumb" x={1150} y={250} scale={1.05} side="back" checks={3} />
          <Character look="max" x={960} y={930} mood="happy" lookX={1} lookY={-0.7} armFront={{ s: 120, e: 20 }} seed={9} />
        </Stage>
      </AbsoluteFill>
    </AbsoluteFill>
    <div
      style={{
        position: "absolute",
        left: 46,
        bottom: 36,
        fontFamily: SANS,
        fontWeight: 800,
        fontSize: 150,
        lineHeight: 0.92,
        color: "white",
        WebkitTextStroke: "6px black",
        paintOrder: "stroke fill",
        textShadow: "0 10px 30px rgba(0,0,0,0.5)",
      }}
    >
      ONE
      <br />
      PROMPT
    </div>
  </AbsoluteFill>
);
