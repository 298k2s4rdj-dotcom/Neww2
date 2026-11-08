import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { f, SCENES, TITLE_CARD } from "../config";
import { Camera, Fade, Stage } from "../components/Camera";
import { Caption } from "../components/Caption";
import { Character, Mood } from "../components/Character";
import { cafeAnchor, isTalking, secs, talkArm } from "../components/cafe";
import { Laptop, PaperBall, Phone } from "../components/Props";
import { APT, CAFE, ApartmentBackground, CafeBackground, CafeChairs, CafeTable } from "../components/Sets";
import { ChartCloseup, Say, Shot } from "../components/Shots";
import { Sound } from "../components/Sound";
import { TitleCard } from "../components/TitleCard";
import { WallChart } from "../components/WallChart";
import { ease, mix } from "../util";

const C = SCENES.scene3;

const Cafe: React.FC = () => {
  const frame = useCurrentFrame();
  const t = secs(frame) + C.cafe.from;
  const L = C.lines;
  const maxTalk = isTalking(L, "max", t);
  const lenaTalk = isTalking(L, "lena", t);
  const slide = ease(frame, f(C.phoneSlide - C.cafe.from), f(C.phoneSlide - C.cafe.from + 1.2));
  const maxMood: Mood = t >= L[4].at - 0.3 && t < L[5].at ? "surprised" : t >= L[5].at + 1.5 ? "happy" : t >= L[2].at ? "sad" : "tired";
  const lenaMood: Mood = t >= L[3].at ? (t >= L[5].at ? "happy" : "determined") : t >= L[1].at ? "neutral" : "sad";
  const lenaReach = slide > 0 && slide < 1 ? 1 : ease(frame, f(C.phoneSlide - C.cafe.from - 0.4), f(C.phoneSlide - C.cafe.from)) * (1 - ease(frame, f(C.phoneSlide - C.cafe.from + 1.3), f(C.phoneSlide - C.cafe.from + 1.8)));
  const left = cafeAnchor("left");
  const right = cafeAnchor("right");
  return (
    <Fade inF={10} outF={6}>
      <Camera from={1} to={1.07} originY={560}>
        <Stage>
          <CafeBackground />
          <CafeChairs />
          <Character look="max" x={CAFE.maxX} y={CAFE.ground} scale={CAFE.scale} sitting mood={maxMood} slump={t < L[3].at ? 0.4 : 0} lean={maxTalk ? 5 : 0} armFront={talkArm(frame, maxTalk, { s: 40, e: 60 })} armBack={{ s: 35, e: 55 }} lookX={1} lookY={slide > 0.2 && t < L[4].at ? 0.8 : 0} seed={1} />
          <Character look="lena" x={CAFE.lenaX} y={CAFE.ground} scale={CAFE.scale} dir={-1} sitting mood={lenaMood} lean={lenaTalk ? 5 : 0} armFront={lenaReach > 0.01 ? { s: mix(40, 82, lenaReach), e: mix(60, 8, lenaReach) } : talkArm(frame, lenaTalk, { s: 40, e: 60 })} armBack={{ s: 30, e: 60 }} lookX={1} seed={2} />
          <CafeTable />
          <Laptop x={830} y={CAFE.tableTop} scale={1.1} dir={-1} glow={0.2} open={0.25} />
          <Phone x={mix(1150, 930, slide)} y={CAFE.tableTop - 2} lit={slide > 0} />
        </Stage>
      </Camera>
      <AbsoluteFill>
        <ShotCaption />
      </AbsoluteFill>
      {L.map((l, i) => {
        const a = l.who === "max" ? left : right;
        return <Say key={i} at={l.at - C.cafe.from} to={l.to - C.cafe.from} x={a.x} y={a.y} tail={a.tail} text={l.text} maxWidth={l.text.length > 40 ? 680 : 620} />;
      })}
    </Fade>
  );
};

const ShotCaption: React.FC = () => (
  <Shot from={C.caption.at - C.cafe.from} to={C.caption.to - C.cafe.from}>
    <Caption text={C.caption.text} />
  </Shot>
);

const Apartment: React.FC = () => {
  const frame = useCurrentFrame();
  const a = C.apartment;
  const bend = ease(frame, 0, f(a.pullAt)) * (1 - ease(frame, f(a.pullAt + 0.8), f(a.pullAt + 1.4)));
  const rise = ease(frame, f(a.pullAt), f(a.pullAt + 1));
  const unfold = ease(frame, f(a.pullAt + 1.1), f(a.pullAt + 2));
  const flipT = ease(frame, f(a.flipAt), f(a.flipAt + 0.8));
  const flip = Math.cos(flipT * Math.PI);
  const mx = 990;
  const ballX = mix(APT.bin.x, mx + 120, rise);
  const ballY = mix(APT.bin.y - 70, APT.floor - 380, rise);
  return (
    <Fade inF={8} outF={4}>
      <Camera from={1.1} to={1.2} originX={1050} originY={560}>
        <Stage>
          <ApartmentBackground time="evening" />
          {unfold < 0.5 && <PaperBall x={ballX} y={ballY} r={30 * (1 + unfold)} rot={rise * 90} />}
          <Character
            look="max"
            x={mx}
            y={APT.floor}
            mood={flipT > 0.3 ? "determined" : unfold > 0.5 ? "neutral" : "sad"}
            lean={bend * 28}
            armFront={{ s: mix(mix(30, 80, rise), 70, bend), e: mix(30, 10, bend) }}
            armBack={{ s: mix(10, 70, unfold), e: 30 }}
            lookX={1}
            lookY={bend > 0.3 ? 1 : 0}
            seed={1}
          />
          {unfold >= 0.5 && (
            <WallChart id="s3-flip" x={mx + 150} y={APT.floor - 520} scale={0.75 * mix(0.6, 1, unfold)} side={flip >= 0 ? "front" : "back"} flipX={Math.max(0.03, Math.abs(flip))} xs={30} marker={0} pin={false} rotate={-4} />
          )}
        </Stage>
      </Camera>
    </Fade>
  );
};

export const Scene3: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Shot from={C.title.at} to={C.title.at + TITLE_CARD} name="Title">
      <TitleCard text={C.title.text} />
    </Shot>
    <Shot from={C.cafe.from} to={C.cafe.to} name="Café – 1 month later">
      <Cafe />
    </Shot>
    <Shot from={C.apartment.from} to={C.apartment.to} name="Chart from the bin">
      <Apartment />
      <Sound name="crumple" at={C.apartment.pullAt + 1.1} dur={1} volume={0.7} />
    </Shot>
    <Shot from={C.marker.from} to={C.marker.to} name="1 PROMPT marker">
      <Fade inF={4} outF={12}>
        <ChartCloseup
          id="s3-marker"
          time="evening"
          side="back"
          marker={(fr) => ease(fr, f(C.marker.writeFrom), f(C.marker.writeTo))}
        />
      </Fade>
    </Shot>
  </AbsoluteFill>
);
