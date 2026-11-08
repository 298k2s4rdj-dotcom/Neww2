import React from "react";
import { Audio, Sequence, staticFile } from "remotion";
import assets from "../generated/assets.json";
import { f } from "../config";

export type SoundName = "alarm" | "keyboard" | "rain" | "crumple" | "ding" | "music";

const lookup = assets as Record<string, string | null>;

export const hasSound = (name: SoundName) => Boolean(lookup[name]);

/**
 * Plays an optional audio file from /public. If the file is missing
 * (see scripts/scan-assets.ts) nothing is rendered, so the film stays silent
 * instead of failing.
 */
export const Sound: React.FC<{
  name: SoundName;
  /** start, seconds relative to parent sequence */
  at?: number;
  /** length in seconds (cuts the sound) */
  dur?: number;
  volume?: number | ((frame: number) => number);
  loop?: boolean;
}> = ({ name, at = 0, dur, volume = 1, loop = false }) => {
  const file = lookup[name];
  if (!file) return null;
  return (
    <Sequence from={f(at)} durationInFrames={dur ? f(dur) : undefined} layout="none" name={`sfx:${name}`}>
      <Audio src={staticFile(file)} volume={volume} loop={loop} />
    </Sequence>
  );
};
