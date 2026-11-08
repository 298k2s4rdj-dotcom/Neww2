import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { f, SCENES, TITLE_CARD } from "../config";
import { Camera, Fade, Stage } from "../components/Camera";
import { Character } from "../components/Character";
import { cafeAnchor, isTalking, secs, talkArm } from "../components/cafe";
import { Laptop, Phone } from "../components/Props";
import { CourseScreen, LaptopCloseup } from "../components/Screens";
import { APT, CAFE, ApartmentBackground, CafeBackground, CafeChairs, CafeTable } from "../components/Sets";
import { ChartCloseup, Say, Shot } from "../components/Shots";
import { TitleCard } from "../components/TitleCard";
import { WallChart } from "../components/WallChart";
import { ease, mix } from "../util";

const C = SCENES.scene1;

const Cafe: React.FC = () => {
  const frame = useCurrentFrame();
  const t = secs(frame) + C.cafe.from; // scene time
  const lines = C.lines;
  const maxTalk = isTalking(lines, "max", t);
  const lenaTalk = isTalking(lines, "lena", t);
  // MAX turns the laptop towards LENA when he starts talking
  const turn = ease(frame, f(C.lines[0].at - C.cafe.from - 0.2), f(C.lines[0].at - C.cafe.from + 0.6));
  const laptopFlip = Math.cos(turn * Math.PI);
  const lenaMood = t > C.lines[2].at + 1 ? "surprised" : t > C.lines[1].at - 0.3 ? "skeptical" : "neutral";
  const reach = ease(frame, f(C.lines[0].at - C.cafe.from - 0.4), f(C.lines[0].at - C.cafe.from + 0.3)) -
    ease(frame, f(C.lines[0].at - C.cafe.from + 1.2), f(C.lines[0].at - C.cafe.from + 1.8));
  const left = cafeAnchor("left");
  const right = cafeAnchor("right");
  return (
    <Fade inF={10} outF={6}>
      <Camera from={1} to={1.06} originY={560}>
        <Stage>
          <CafeBackground />
          <CafeChairs />
          <Character
            look="max"
            x={CAFE.maxX}
            y={CAFE.ground}
            scale={CAFE.scale}
            sitting
            mood={t > C.lines[0].at - 0.5 ? "happy" : "neutral"}
            lean={maxTalk ? 6 : 2}
            armFront={reach > 0.01 ? { s: mix(-6, 80, reach), e: mix(10, 10, reach) } : talkArm(frame, maxTalk, { s: 40, e: 60 })}
            armBack={{ s: 35, e: 55 }}
            lookX={1}
            seed={1}
          />
          <Character
            look="lena"
            x={CAFE.lenaX}
            y={CAFE.ground}
            scale={CAFE.scale}
            dir={-1}
            sitting
            mood={lenaMood}
            lean={lenaTalk ? 5 : 0}
            armFront={talkArm(frame, lenaTalk, { s: 40, e: 60 })}
            armBack={{ s: 30, e: 60 }}
            lookX={1}
            seed={2}
          />
          <CafeTable />
          <g transform={`translate(${900} ${CAFE.tableTop}) scale(${laptopFlip} 1) translate(${-900} ${-CAFE.tableTop})`}>
            <Laptop x={900} y={CAFE.tableTop} scale={1.25} dir={-1} glow={0.9} />
          </g>
          <Phone x={1070} y={CAFE.tableTop - 2} lit={false} />
        </Stage>
      </Camera>
      {lines.map((l, i) => {
        const a = l.who === "max" ? left : right;
        return <Say key={i} at={l.at - C.cafe.from} to={l.to - C.cafe.from} x={a.x} y={a.y} tail={a.tail} text={l.text} />;
      })}
    </Fade>
  );
};

const Apartment: React.FC = () => {
  const frame = useCurrentFrame();
  const pin = f(C.pinAt - C.apartment.from);
  const walkEnd = pin - f(1);
  const x = mix(560, 930, ease(frame, 0, walkEnd));
  const walking = frame < walkEnd;
  const raise = ease(frame, walkEnd, pin);
  const stepBack = ease(frame, pin + f(0.8), pin + f(2.2));
  const mx = x - stepBack * 120;
  // chart travels with MAX's hand, then onto the wall
  const handX = mx + 120;
  const handY = APT.floor - 360;
  const cx = mix(handX, APT.chart.x, raise);
  const cy = mix(handY, APT.chart.y, raise);
  const onWall = frame >= pin;
  const pinPop = onWall ? 1 + Math.sin(Math.min(1, (frame - pin) / 8) * Math.PI) * 0.06 : 1;
  return (
    <Fade inF={6}>
      <Camera from={1.02} to={1.1} originX={1000} originY={520}>
        <Stage>
          <ApartmentBackground time="evening" />
          <WallChart id="s1-wall" x={cx} y={cy} scale={APT.chartScale * pinPop * mix(0.8, 1, raise)} rotate={onWall ? 0 : mix(-8, 0, raise)} pin={onWall} />
          <Character
            look="max"
            x={mx}
            y={APT.floor}
            walk={walking ? frame / 4.5 : undefined}
            mood={stepBack > 0.5 ? "happy" : "determined"}
            armFront={stepBack > 0 ? { s: mix(mix(70, 150, raise), -20, stepBack), e: mix(30, 120, stepBack) } : { s: mix(70, 150, raise), e: mix(30, 20, raise) }}
            armBack={stepBack > 0 ? { s: mix(10, -40, stepBack), e: mix(10, -110, stepBack) } : undefined}
            lookX={1}
            lookY={onWall ? -0.6 : 0}
            seed={1}
          />
        </Stage>
      </Camera>
    </Fade>
  );
};

export const Scene1: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    <Shot from={C.title.at} to={C.title.at + TITLE_CARD} name="Title">
      <TitleCard text={C.title.text} />
    </Shot>
    <Shot from={C.cafe.from} to={C.cafe.to} name="Café">
      <Cafe />
    </Shot>
    <Shot from={C.apartment.from} to={C.apartment.to} name="Apartment – pin chart">
      <Apartment />
    </Shot>
    <Shot from={C.chartCloseup.from} to={C.chartCloseup.to} name="Chart closeup">
      <ChartCloseup id="s1-cc" time="evening" side="front" />
    </Shot>
    <Shot from={C.laptopCloseup.from} to={C.laptopCloseup.to} name="Laptop – tabs + $199">
      <Fade inF={4} outF={14}>
        <LaptopCloseup ambient="#5a3d3a">
          <CourseScreen />
        </LaptopCloseup>
      </Fade>
    </Shot>
  </AbsoluteFill>
);

