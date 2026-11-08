import React from "react";
import { Composition, Still } from "remotion";
import "./fonts";
import { FPS, HEIGHT, TOTAL_SECONDS, WIDTH } from "./config";
import { OnePrompt } from "./OnePrompt";
import { Thumbnail } from "./Thumbnail";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="OnePrompt"
      component={OnePrompt}
      durationInFrames={Math.round(TOTAL_SECONDS * FPS)}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
    <Still id="Thumbnail" component={Thumbnail} width={1280} height={720} />
  </>
);
