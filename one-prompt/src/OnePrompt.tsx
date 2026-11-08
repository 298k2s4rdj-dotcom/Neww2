import React from "react";
import { AbsoluteFill, Sequence, interpolate } from "remotion";
import { FPS, MUSIC, SCENES, SCENE_ORDER, SceneKey, TOTAL_SECONDS, f, sceneStart } from "./config";
import { Sound } from "./components/Sound";
import { Scene1 } from "./scenes/Scene1";
import { Scene2 } from "./scenes/Scene2";
import { Scene3 } from "./scenes/Scene3";
import { Scene4 } from "./scenes/Scene4";
import { Scene5 } from "./scenes/Scene5";
import { Scene6 } from "./scenes/Scene6";

const COMPONENTS: Record<SceneKey, React.FC> = {
  scene1: Scene1,
  scene2: Scene2,
  scene3: Scene3,
  scene4: Scene4,
  scene5: Scene5,
  scene6: Scene6,
};

/** Music: quiet bed for scenes 1–3, fades up at the start of scene 4, fades out at the end. */
const musicVolume = (frame: number) => {
  const up = sceneStart("scene4") * FPS;
  const end = TOTAL_SECONDS * FPS;
  return interpolate(
    frame,
    [0, FPS, up, up + MUSIC.fadeUpSeconds * FPS, end - MUSIC.fadeOutSeconds * FPS, end],
    [0, MUSIC.baseVolume, MUSIC.baseVolume, MUSIC.fullVolume, MUSIC.fullVolume, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
};

export const OnePrompt: React.FC = () => (
  <AbsoluteFill style={{ background: "#000" }}>
    {SCENE_ORDER.map((key) => {
      const Comp = COMPONENTS[key];
      return (
        <Sequence key={key} from={f(sceneStart(key))} durationInFrames={f(SCENES[key].duration)} name={key}>
          <Comp />
        </Sequence>
      );
    })}
    <Sound name="music" loop volume={musicVolume} />
  </AbsoluteFill>
);
