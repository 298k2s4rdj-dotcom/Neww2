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

/** Music volume: per-scene levels with glides, slower fade-up into scene 4, fade in/out at the edges. */
const musicVolume = (frame: number) => {
  const t = frame / FPS;
  let level = MUSIC.levels.scene1;
  for (const key of SCENE_ORDER) {
    const start = sceneStart(key);
    if (t < start) break;
    const glide = key === "scene4" ? MUSIC.scene4FadeUpSeconds : MUSIC.glideSeconds;
    const prev = level;
    level = interpolate(t, [start, start + glide], [prev, MUSIC.levels[key]], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  }
  const edge = interpolate(
    t,
    [0, MUSIC.fadeInSeconds, TOTAL_SECONDS - MUSIC.fadeOutSeconds, TOTAL_SECONDS],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  return level * edge;
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
