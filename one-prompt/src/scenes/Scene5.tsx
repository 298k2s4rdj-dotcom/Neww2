import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { f, SCENES, TITLE_CARD } from "../config";
import { Camera, Fade, Stage } from "../components/Camera";
import { Character } from "../components/Character";
import { MaxAt } from "../components/MaxAt";
import { Laptop } from "../components/Props";
import { LaptopCloseup, NotesScreen } from "../components/Screens";
import { APT, ApartmentBackground } from "../components/Sets";
import { ChartCloseup, Say, Shot } from "../components/Shots";
import { Sound } from "../components/Sound";
import { TitleCard } from "../components/TitleCard";
import { WallChart } from "../components/WallChart";
import { typing } from "../components/poses";
import { ease, lerpF, mix } from "../util";

const C = SCENES.scene5;
const BASE_CHECKS = 26; // where scene 4 left the chart

const LookAtChart: React.FC = () => {
  const frame = useCurrentFrame();
  const turn = ease(frame, f(0.3), f(0.9));
  return (
    <Fade inF={4}>
      <Camera from={1.05} to={1.12} originX={850} originY={480}>
        <Stage>
          <ApartmentBackground time="evening" />
          <WallChart id="s5-look" x={APT.chart.x} y={APT.chart.y} scale={APT.chartScale} side="back" checks={BASE_CHECKS} />
          <MaxAt place="desk" mood={frame > f(1.6) ? "determined" : "neutral"} lookX={mix(0.6, 1, turn)} lookY={mix(0.2, -0.8, turn)} />
        </Stage>
      </Camera>
    </Fade>
  );
};

const RainyNight: React.FC = () => {
  const frame = useCurrentFrame();
  const r = C.rain;
  const sitUp = ease(frame, f(r.thoughtTo), f(r.typeAt));
  const typingOn = frame >= f(r.typeAt) && frame < f(r.checkAt - 0.4);
  const checks = BASE_CHECKS + lerpF(frame, [f(r.checkAt), f(r.checkAt + 0.6)], [0, 1]);
  const smile = frame > f(r.checkAt + 0.8);
  const laptopX = mix(1770, 1720, sitUp);
  return (
    <Fade inF={10} outF={14}>
      <Camera from={1.0} to={1.08} originX={1450} originY={560}>
        <Stage>
          <ApartmentBackground time="rain" laptopGlow={0.1} />
          <WallChart id="s5-rain" x={APT.chart.x} y={APT.chart.y} scale={APT.chartScale} side="back" checks={checks} />
          {sitUp < 0.5 && <Laptop x={laptopX} y={712} scale={0.9} dir={-1} glow={0} open={0.05} />}
          <Character
            look="max"
            x={APT.sofaSeatX}
            y={APT.sofaGround}
            sitting
            mood={smile ? "happy" : sitUp > 0.5 ? "determined" : "tired"}
            slump={mix(1, 0.2, sitUp)}
            lean={mix(-12, 2, sitUp)}
            lookX={mix(0.2, 0.9, sitUp)}
            lookY={mix(0.6, 0.5, sitUp)}
            {...(sitUp > 0.5 ? typing(frame, typingOn) : { armFront: { s: 25, e: 40 }, armBack: { s: 20, e: 45 } })}
            seed={1}
          />
          {sitUp >= 0.5 && <Laptop x={APT.sofaSeatX + 175} y={APT.sofaGround - 190} scale={0.9} dir={-1} glow={0.9} />}
          {/* moody dim */}
          <rect width={1920} height={1080} fill="#081028" opacity={0.18} />
        </Stage>
      </Camera>
      <Say at={r.thoughtAt} to={r.thoughtTo} x={APT.sofaSeatX + 10} y={APT.sofaGround - 505} tail={0.7} kind="thought" text={C.thought} />
    </Fade>
  );
};

export const Scene5: React.FC = () => {
  const g = C.goal;
  const r = C.rain;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Shot from={g.from} to={g.lookFrom} name="New goal typed">
        <Fade inF={10}>
          <LaptopCloseup ambient="#5a4a3a">
            <NotesScreen text={g.text} typeFrom={0.4} deleteAt={999} />
          </LaptopCloseup>
        </Fade>
        <Sound name="keyboard" at={0.4} dur={g.text.length / 14} volume={0.6} />
      </Shot>
      <Shot from={g.lookFrom} to={g.lookTo} name="Looks at the chart">
        <LookAtChart />
      </Shot>
      <Shot from={g.lookTo} to={g.to} name="Delete the goal">
        <LaptopCloseup ambient="#5a4a3a">
          <NotesScreen text={g.text} typeFrom={0.4 - g.lookTo} deleteAt={g.deleteAt - g.lookTo} />
        </LaptopCloseup>
        <Sound name="keyboard" at={g.deleteAt - g.lookTo} dur={g.text.length / 24} volume={0.5} />
      </Shot>
      <Shot from={r.from} to={r.from + r.checkAt} name="Rainy night">
        <RainyNight />
      </Shot>
      <Shot from={r.from + r.checkAt} to={r.from + r.checkAt + 2} name="Check in the rain">
        <ChartCloseup id="s5-cc" time="rain" side="back" checks={(fr) => BASE_CHECKS + lerpF(fr, [f(0.3), f(0.9)], [0, 1])} />
        <Sound name="ding" at={0.3} dur={1.2} volume={0.5} />
      </Shot>
      <Shot from={r.from + r.checkAt + 2} to={r.to} name="Small smile">
        <ContinueRain offset={r.checkAt + 2} />
      </Shot>
      <Shot from={r.from} to={r.to} name="Rain audio">
        <Sound name="rain" loop volume={(fr) => Math.min(1, fr / 20, (f(r.to - r.from) - fr) / 20) * 0.5} />
        <Sound name="keyboard" at={r.typeAt} dur={r.checkAt - r.typeAt - 0.4} volume={0.5} />
      </Shot>
      <Shot from={C.title.at} to={C.title.at + TITLE_CARD} name="Title">
        <TitleCard text={C.title.text} />
      </Shot>
    </AbsoluteFill>
  );
};

/** Continue the rainy-night shot after the closeup cut, with time offset. */
const ContinueRain: React.FC<{ offset: number }> = ({ offset }) => (
  <Shot from={-offset} to={C.rain.to - C.rain.from}>
    <RainyNight />
  </Shot>
);
