import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { f, SCENES } from "../config";
import { Camera, Fade, Stage } from "../components/Camera";
import { Character } from "../components/Character";
import { MAX_ANCHOR, MaxAt } from "../components/MaxAt";
import { AlarmClock, Laptop } from "../components/Props";
import { ChatScreen, LaptopCloseup } from "../components/Screens";
import { APT, ApartmentBackground, BedroomBackground, OfficeBackground } from "../components/Sets";
import { ChartCloseup, PromptCounter, Say, Shot } from "../components/Shots";
import { Sound } from "../components/Sound";
import { WallChart } from "../components/WallChart";
import { typing } from "../components/poses";
import type { TimeOfDay } from "../components/palette";
import { ease, lerpF } from "../util";

const C = SCENES.scene4;

const Morning: React.FC = () => {
  const frame = useCurrentFrame();
  const m = C.morning;
  const ringing = frame >= f(m.alarmAt) && frame < f(m.alarmAt + 2.2);
  const awake = ease(frame, f(m.alarmAt + 1.6), f(m.alarmAt + 2.4));
  const resolve = frame > f(m.thoughtTo - 0.3);
  return (
    <Fade inF={14}>
      <Camera from={1} to={1.08} originX={1100} originY={600}>
        <Stage>
          <BedroomBackground time="morning" />
          <AlarmClock x={1580} y={700} ringing={ringing} />
          <Laptop x={1680} y={700} scale={0.8} dir={-1} glow={0.1} open={0.1} />
          <Character
            look="max"
            x={880}
            y={875}
            sitting
            mood={resolve ? "determined" : awake > 0.5 ? "neutral" : "tired"}
            eyesClosed={1 - awake}
            slump={0.6 - awake * 0.4}
            lookX={1}
            lookY={frame > f(m.thoughtAt) && !resolve ? 0.6 : 0}
            armFront={resolve ? { s: 40, e: 30 } : { s: 30, e: 50 }}
            armBack={{ s: 25, e: 55 }}
            seed={1}
          />
        </Stage>
      </Camera>
      <Say at={m.thoughtAt} to={m.thoughtTo} x={900} y={420} tail={0.4} kind="thought" text="It's just one prompt." />
    </Fade>
  );
};

/** MAX at the desk, smiling at the screen. */
const DeskShot: React.FC<{ time?: TimeOfDay; checks: number; zoom?: boolean; typingOn?: boolean; cycle?: boolean }> = ({ time = "morning", checks, zoom = true, typingOn = false, cycle = false }) => {
  const frame = useCurrentFrame();
  const times: TimeOfDay[] = ["morning", "day", "evening", "night"];
  const tod = cycle ? times[Math.floor(frame / 20) % times.length] : time;
  return (
    <Fade inF={5}>
      <Camera from={zoom ? 1.25 : 1} to={zoom ? 1.32 : 1.06} originX={700} originY={500}>
        <Stage>
          <ApartmentBackground time={tod} />
          <WallChart id={`s4-desk-${checks}`} x={APT.chart.x} y={APT.chart.y} scale={APT.chartScale} side="back" checks={cycle ? checks + frame / 30 : checks} />
          <MaxAt place="desk" mood="happy" typingOn={typingOn} />
        </Stage>
      </Camera>
    </Fade>
  );
};

const PlaceShot: React.FC<{ place: string; checks: number; dur: number }> = ({ place, checks, dur }) => {
  const frame = useCurrentFrame();
  if (place === "office") {
    const enter = ease(frame, 0, f(1.6));
    const nod = frame > f(2) ? Math.sin((frame - f(2)) / 4) * 6 * (frame < f(3.6) ? 1 : 0) : 0;
    return (
      <Fade inF={6}>
        <Camera from={1} to={1.05} originX={900} originY={560}>
          <Stage>
            <OfficeBackground />
            <Character look="max" x={505} y={900} sitting mood={frame > f(2.2) ? "happy" : "determined"} {...typing(frame, frame < f(2))} lookX={frame > f(1.8) ? 1 : 0.6} seed={1} />
            <Character look="boss" x={1500 - enter * 260} y={900} dir={-1} walk={enter < 1 ? frame / 4.5 : undefined} mood={frame > f(2) ? "happy" : "neutral"} headTilt={nod} lookX={1} lookY={0.4} armFront={enter >= 1 ? { s: 60, e: 60 } : undefined} seed={5} />
          </Stage>
        </Camera>
        <Say at={2.2} to={dur - 0.2} x={1200} y={400} tail={0.7} text="Nice work!" />
      </Fade>
    );
  }
  const p = place as "fridge" | "desk" | "sofa";
  const fridgeOpen = p === "fridge" ? ease(frame, f(0.2), f(1)) : 0;
  return (
    <Fade inF={5}>
      <Camera from={1} to={1.05} originX={p === "sofa" ? 1500 : p === "fridge" ? 1200 : 700} originY={560}>
        <Stage>
          <ApartmentBackground time={p === "sofa" ? "evening" : "day"} fridgeOpen={fridgeOpen} />
          <WallChart id={`s4-pl-${place}`} x={APT.chart.x} y={APT.chart.y} scale={APT.chartScale} side="back" checks={checks} />
          <MaxAt place={p} mood={p === "fridge" ? "neutral" : "happy"} typingOn={p === "desk"} phone={p === "sofa"} lookX={p === "fridge" ? 1 : 0.8} />
        </Stage>
      </Camera>
      {p === "fridge" && <Say at={0.9} to={dur - 0.1} x={MAX_ANCHOR.fridge.x} y={MAX_ANCHOR.fridge.y} tail={0.5} kind="thought" text="Hmm…" />}
    </Fade>
  );
};

export const Scene4: React.FC = () => {
  // pre-compute montage beat start times
  let t = C.montageStart;
  const beats = C.beats.map((b, i) => {
    const start = t;
    t += b.shot + b.screen + b.check;
    return { ...b, start, index: i };
  });
  const firstChecks = 1;
  return (
    <AbsoluteFill style={{ background: "#000" }}>
      <Shot from={C.morning.from} to={C.morning.to} name="Morning">
        <Morning />
        <Sound name="alarm" at={C.morning.alarmAt} dur={2.2} volume={0.6} />
      </Shot>
      <Shot from={C.chat.from} to={C.chat.to} name="First prompt">
        <Fade inF={4}>
          <LaptopCloseup ambient="#c9a77a">
            <ChatScreen prompt={C.chat.prompt} reply={C.chat.reply} replyAt={C.chat.replyAt} />
          </LaptopCloseup>
        </Fade>
        <Sound name="keyboard" at={0.4} dur={C.chat.prompt.length / 20} volume={0.6} />
        <Sound name="ding" at={C.chat.replyAt + 2} dur={1.5} volume={0.5} />
      </Shot>
      <Shot from={C.smile.from} to={C.smile.to} name="Smile">
        <DeskShot checks={0} />
      </Shot>
      <Shot from={C.firstCheck.from} to={C.firstCheck.to} name="First check">
        <ChartCloseup id="s4-first" time="morning" side="back" checks={(fr) => lerpF(fr, [f(0.3), f(0.9)], [0, 1])} />
        <Sound name="ding" at={0.3} dur={1.2} volume={0.5} />
      </Shot>
      {beats.map((b) => {
        const before = firstChecks + b.index;
        return (
          <React.Fragment key={b.index}>
            <Shot from={b.start} to={b.start + b.shot} name={`Beat ${b.place}`}>
              <PlaceShot place={b.place} checks={before} dur={b.shot} />
            </Shot>
            {b.screen > 0 && (
              <Shot from={b.start + b.shot} to={b.start + b.shot + b.screen} name={`Prompt: ${b.prompt}`}>
                <Fade inF={3}>
                  <LaptopCloseup ambient="#7a8aa0">
                    <ChatScreen prompt={b.prompt} reply={b.reply} cps={30} typeFrom={0.2} replyAt={0.2 + b.prompt.length / 30 + 0.7} />
                  </LaptopCloseup>
                </Fade>
                <Sound name="keyboard" at={0.2} dur={b.prompt.length / 30} volume={0.5} />
              </Shot>
            )}
            <Shot from={b.start + b.shot + b.screen} to={b.start + b.shot + b.screen + b.check} name="Check">
              <ChartCloseup id={`s4-c${b.index}`} time="day" side="back" checks={(fr) => before + lerpF(fr, [f(0.2), f(0.8)], [0, 1])} />
              <Sound name="ding" at={0.2} dur={1.2} volume={0.45} />
            </Shot>
          </React.Fragment>
        );
      })}
      <Shot from={C.fillUp.from} to={C.fillUp.chartFrom} name="Days pass">
        <DeskShot checks={firstChecks + beats.length} zoom={false} typingOn cycle />
      </Shot>
      <Shot from={C.fillUp.chartFrom} to={C.fillUp.to} name="Checks fill up">
        <Fade inF={4} outF={16}>
          <ChartCloseup
            id="s4-fill"
            time="day"
            side="back"
            checks={(fr) => lerpF(fr, [0, f(5)], [firstChecks + beats.length + f(C.fillUp.chartFrom - C.fillUp.from) / 30, 26])}
          />
        </Fade>
      </Shot>
      <Sequence from={f(C.montageStart)} durationInFrames={f(C.duration - C.montageStart)} name="Counter">
        <PromptCounter steps={C.counter} offset={C.montageStart} />
      </Sequence>
    </AbsoluteFill>
  );
};
