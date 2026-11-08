import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { f, SCENES } from "../config";
import { Camera, Fade, Stage } from "../components/Camera";
import { Character } from "../components/Character";
import { cafeAnchor, isTalking, secs, talkArm } from "../components/cafe";
import { Laptop, Phone } from "../components/Props";
import { CAFE, CafeBackground, CafeChairs, CafeTable } from "../components/Sets";
import { Say, Shot } from "../components/Shots";
import { Sound } from "../components/Sound";
import { TitleCard } from "../components/TitleCard";
import { typing } from "../components/poses";
import { ease, mix } from "../util";

const C = SCENES.scene6;

const Cafe: React.FC = () => {
  const frame = useCurrentFrame();
  const t = secs(frame);
  const L = C.lines;
  const friendTalk = isTalking(L, "friend", t);
  const maxTalk = isTalking(L, "max", t);
  const slide = ease(frame, f(C.phoneSlide), f(C.phoneSlide + 1.2));
  const reach = ease(frame, f(C.phoneSlide - 0.4), f(C.phoneSlide)) * (1 - ease(frame, f(C.phoneSlide + 1.3), f(C.phoneSlide + 1.8)));
  const lenaHappy = t >= C.lenaSmile;
  const left = cafeAnchor("left");
  const right = cafeAnchor("right");
  return (
    <Fade inF={10} outF={14}>
      <Camera from={1} to={1.06} originY={560}>
        <Stage>
          <CafeBackground />
          {/* LENA in the background, by the shelf */}
          <Character look="lena" x={1730} y={880} scale={0.7} dir={-1} mood={lenaHappy ? "happy" : "neutral"} lookX={lenaHappy ? 1 : 0.2} armFront={{ s: 60, e: 70 }} holding={<rect x={-10} y={-26} width={22} height={26} rx={4} fill="#f4efe6" />} seed={3} />
          <rect x={1560} y={880} width={360} height={200} fill="#2b1a14" />
          <rect x={1550} y={870} width={380} height={18} fill="#3b2730" />
          <CafeChairs />
          <Character
            look="friend"
            x={CAFE.maxX}
            y={CAFE.ground}
            scale={CAFE.scale}
            sitting
            mood={t > L[1].at + 2 ? "surprised" : "stressed"}
            lean={friendTalk ? 4 : 8}
            {...(t < L[0].at ? typing(frame, true) : { armFront: talkArm(frame, friendTalk, { s: 45, e: 50 }), armBack: { s: 40, e: 55 } })}
            lookX={t < L[0].at ? 0.6 : 1}
            lookY={slide > 0.2 ? 0.8 : 0}
            seed={4}
          />
          <Character
            look="max"
            x={CAFE.lenaX}
            y={CAFE.ground}
            scale={CAFE.scale}
            dir={-1}
            sitting
            mood={t > L[1].at ? "happy" : "neutral"}
            lean={maxTalk ? 5 : 0}
            armFront={reach > 0.01 ? { s: mix(40, 82, reach), e: mix(60, 8, reach) } : talkArm(frame, maxTalk, { s: 40, e: 60 })}
            armBack={{ s: 30, e: 60 }}
            lookX={1}
            seed={1}
          />
          <CafeTable />
          <Laptop x={830} y={CAFE.tableTop} scale={1.15} dir={-1} glow={0.9} />
          <Phone x={mix(1150, 960, slide)} y={CAFE.tableTop - 2} lit={slide > 0} />
        </Stage>
      </Camera>
      {L.map((l, i) => {
        const a = l.who === "friend" ? left : right;
        return <Say key={i} at={l.at} to={l.to} x={a.x} y={a.y} tail={a.tail} text={l.text} />;
      })}
    </Fade>
  );
};

export const Scene6: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Shot from={C.cafe.from} to={C.cafe.to} name="Café – full circle">
      <Cafe />
      <Sound name="keyboard" at={0.3} dur={2} volume={0.4} />
    </Shot>
    <Shot from={C.finalCard.from} to={C.finalCard.to} name="Final card">
      <TitleCard text="ONE PROMPT." sub="Just start. See where it takes you." size={110} />
    </Shot>
    <Shot from={C.endCard.from} to={C.endCard.to} name="End card">
      <TitleCard text={C.endCard.handle} size={84} />
    </Shot>
  </AbsoluteFill>
);
