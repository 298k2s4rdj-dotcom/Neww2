import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { f, SCENES } from "../config";
import { Camera, Fade, Stage } from "../components/Camera";
import { Character } from "../components/Character";
import { MAX_ANCHOR, MaxAt, Place } from "../components/MaxAt";
import { PaperBall } from "../components/Props";
import { LaptopCloseup, ModuleScreen } from "../components/Screens";
import { APT, ApartmentBackground } from "../components/Sets";
import { ChartCloseup, Say, Shot } from "../components/Shots";
import { Ambience, Repeat, Sound } from "../components/Sound";
import { WallChart } from "../components/WallChart";
import type { TimeOfDay } from "../components/palette";
import { ease, lerpF, mix } from "../util";

const C = SCENES.scene2;
const X_PER_BEAT = 30 / C.beats.length;

const Sigh: React.FC = () => {
  const frame = useCurrentFrame();
  const slump = ease(frame, f(0.6), f(1.8)) * 0.9;
  return (
    <Fade inF={4}>
      <Camera from={1.15} to={1.22} originX={620} originY={520}>
        <Stage>
          <ApartmentBackground time="evening" />
          <WallChart id="s2-sigh" x={APT.chart.x} y={APT.chart.y} scale={APT.chartScale} />
          <MaxAt place="desk" mood={frame > f(0.8) ? "tired" : "neutral"} slump={slump} />
        </Stage>
      </Camera>
      <Say at={1} to={3.8} x={MAX_ANCHOR.desk.x + 30} y={MAX_ANCHOR.desk.y + 40} tail={0.2} text="*sigh*" />
    </Fade>
  );
};

const Beat: React.FC<{ place: Place; time: TimeOfDay; thought: string; index: number }> = ({ place, time, thought, index }) => {
  const frame = useCurrentFrame();
  const done = index * X_PER_BEAT;
  const fridgeOpen = place === "fridge" ? ease(frame, f(0.3), f(1.2)) : 0;
  const mood = place === "fridge" ? "happy" : index === 2 ? "skeptical" : index === 3 ? "neutral" : "tired";
  return (
    <Fade inF={6}>
      <Camera from={1.0} to={1.05} originX={place === "sofa" ? 1500 : place === "fridge" ? 1200 : 700} originY={560}>
        <Stage>
          <ApartmentBackground time={time} fridgeOpen={fridgeOpen} laptopGlow={place === "desk" ? 0.9 : 0.15} />
          <WallChart id={`s2-b${index}`} x={APT.chart.x} y={APT.chart.y} scale={APT.chartScale} xs={done} />
          <MaxAt
            place={place}
            mood={mood}
            slump={place === "sofa" ? 0.8 : index === 1 ? 0.5 : 0}
            phone={index === 3}
            lookY={index === 0 ? 0.3 : 0}
          />
        </Stage>
      </Camera>
      <Say at={0.6} to={C.beatShot - 0.2} x={MAX_ANCHOR[place].x} y={MAX_ANCHOR[place].y} tail={MAX_ANCHOR[place].tail} kind="thought" text={thought} />
    </Fade>
  );
};

const Crumple: React.FC = () => {
  const frame = useCurrentFrame();
  const k = C.crumple;
  const grab = ease(frame, f(k.grabAt - 0.5), f(k.grabAt));
  const crum = ease(frame, f(k.crumpleAt), f(k.crumpleAt + 1.2));
  const thr = lerpF(frame, [f(k.throwAt), f(k.throwAt + 0.75)], [0, 1]);
  const turn = ease(frame, f(k.throwAt + 1), f(k.throwAt + 1.8));
  const mx = 905;
  // chart pulled off the wall into his hands, then crumpled
  const chartX = mix(APT.chart.x, mx + 120, crum);
  const chartY = mix(APT.chart.y, APT.floor - 420, crum);
  const handPos = { x: mx + 130, y: APT.floor - 360 };
  const ballStart = handPos;
  const binTop = { x: APT.bin.x, y: APT.bin.y - 80 };
  const bx = mix(ballStart.x, binTop.x, thr);
  const by = mix(ballStart.y, binTop.y, thr) - Math.sin(thr * Math.PI) * 170;
  const armUp = frame < f(k.throwAt) ? mix(20, 150, grab) * (1 - crum) + crum * 70 : mix(70, 120, Math.sin(Math.min(1, thr * 1.5) * Math.PI));
  return (
    <Fade inF={6} outF={18}>
      <Camera from={1.05} to={1.15} originX={1000} originY={560}>
        <Stage>
          <ApartmentBackground time="night" laptopGlow={0.2} />
          {crum < 0.6 && (
            <WallChart
              id="s2-crumple"
              x={chartX}
              y={chartY}
              scale={APT.chartScale * mix(1, 0.25, crum)}
              rotate={crum * 40}
              flipX={1 - crum * 0.5}
              xs={30}
              pin={crum === 0}
              opacity={1 - Math.max(0, (crum - 0.4) / 0.2)}
            />
          )}
          {crum >= 0.4 && thr < 1 && (
            <PaperBall x={frame < f(k.throwAt) ? handPos.x : bx} y={frame < f(k.throwAt) ? handPos.y : by} r={mix(10, 30, Math.min(1, (crum - 0.4) / 0.6))} rot={frame * 12 * thr} />
          )}
          <Character
            look="max"
            x={mx}
            y={APT.floor}
            dir={turn > 0.5 ? -1 : 1}
            mood={frame > f(k.thoughtAt - 1) ? "sad" : frame > f(k.crumpleAt) ? "determined" : "tired"}
            slump={frame > f(k.thoughtAt - 1) ? ease(frame, f(k.thoughtAt - 1), f(k.thoughtAt)) : 0}
            armFront={{ s: armUp, e: 20 }}
            armBack={{ s: frame < f(k.throwAt) ? mix(10, 130, Math.max(grab * (1 - crum), crum)) : 6, e: 30 }}
            lookX={turn > 0.5 ? -0.2 : 1}
            lookY={turn > 0.5 ? 0.7 : -0.3 * (1 - crum)}
            seed={1}
          />
        </Stage>
      </Camera>
      <Say at={k.thoughtAt} to={k.thoughtTo} x={mx - 10} y={APT.floor - 520} tail={0.5} kind="thought" text={C.thought} />
    </Fade>
  );
};

export const Scene2: React.FC = () => {
  const beatLen = C.beatShot + C.beatChart;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Shot from={C.moduleCloseup.from} to={C.moduleCloseup.to} name="Module 1 of 47">
        <LaptopCloseup ambient="#3a2f3a">
          <ModuleScreen />
        </LaptopCloseup>
      </Shot>
      <Shot from={C.sigh.from} to={C.sigh.to} name="Sigh">
        <Sigh />
      </Shot>
      {C.beats.map((b, i) => {
        const start = C.montageStart + i * beatLen;
        return (
          <React.Fragment key={i}>
            <Shot from={start} to={start + C.beatShot} name={`Excuse: ${b.thought}`}>
              <Beat place={b.place} time={b.time} thought={b.thought} index={i} />
            </Shot>
            <Shot from={start + C.beatShot} to={start + beatLen} name={`X's ${i + 1}`}>
              <ChartCloseup
                id={`s2-cc${i}`}
                time={b.time}
                side="front"
                xs={(fr) => i * X_PER_BEAT + lerpF(fr, [f(0.2), f(C.beatChart - 0.3)], [0, X_PER_BEAT])}
              />
            </Shot>
          </React.Fragment>
        );
      })}
      <Shot from={C.crumple.from} to={C.crumple.to} name="Crumple + throw">
        <Crumple />
      </Shot>
      <Scene2Sound />
    </AbsoluteFill>
  );
};

/** Sound design – all times in scene seconds. */
const Scene2Sound: React.FC = () => {
  const beatLen = C.beatShot + C.beatChart;
  const k = C.crumple;
  return (
    <>
      {/* module + sigh */}
      <Ambience name="room-evening" at={0} dur={C.montageStart} volume={0.4} />
      <Sound name="click" at={0.5} volume={0.45} />
      <Sound name="sigh" at={C.sigh.from + 0.7} volume={0.8} />
      {C.beats.map((b, i) => {
        const start = C.montageStart + i * beatLen;
        const room = b.time === "night" ? "room-night" : "room-evening";
        const xTimes = Array.from({ length: X_PER_BEAT }, (_, j) => start + C.beatShot + 0.2 + ((C.beatChart - 0.5) / X_PER_BEAT) * j);
        return (
          <React.Fragment key={i}>
            <Ambience name={room} at={start} dur={beatLen} volume={0.45} fade={0.3} />
            {b.place === "fridge" && <Sound name="fridge" at={start + 0.25} volume={0.6} />}
            {b.place === "sofa" && <Sound name="sofa" at={start + 0.2} dur={1.2} volume={0.3} fadeOut={0.4} />}
            {i === 1 && <Sound name="sigh" at={start + 1.2} volume={0.5} />}
            <Repeat name="marker-x" times={xTimes} volume={0.5} />
          </React.Fragment>
        );
      })}
      {/* crumple + throw */}
      <Ambience name="room-night" at={k.from} dur={k.to - k.from} volume={0.45} />
      <Sound name="paper-rip" at={k.from + k.grabAt + 0.4} volume={0.7} />
      <Sound name="paper-crumple" at={k.from + k.crumpleAt} volume={0.8} />
      <Sound name="bin" at={k.from + k.throwAt + 0.7} volume={0.8} />
      <Sound name="sigh" at={k.from + k.thoughtAt - 0.6} volume={0.6} />
    </>
  );
};

