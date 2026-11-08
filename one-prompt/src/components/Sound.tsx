import React from "react";
import { Audio, Sequence, interpolate, staticFile } from "remotion";
import assets from "../generated/assets.json";
import { f } from "../config";

/** Base name of a file in public/sfx (e.g. "rain" → public/sfx/rain.mp3), or "music". */
export type SoundName =
  | "music"
  | "alarm" | "bin" | "cafe" | "click" | "cup" | "ding" | "footsteps" | "fridge"
  | "keyboard" | "laptop-turn" | "marker-check" | "marker-write" | "marker-x"
  | "morning-birds" | "office" | "paper-crumple" | "paper-flip" | "paper-rip"
  | "paper-unfold" | "phone-slide" | "pin" | "pop" | "rain" | "room-evening"
  | "room-night" | "send" | "sigh" | "sofa" | "thunder" | "title-swell";

const lookup = assets as Record<string, string | undefined>;

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
  /** fade in / out in seconds (only with `dur`) */
  fadeIn?: number;
  fadeOut?: number;
  playbackRate?: number;
}> = ({ name, at = 0, dur, volume = 1, loop = false, fadeIn = 0, fadeOut = 0, playbackRate = 1 }) => {
  const file = lookup[name];
  if (!file) return null;
  const total = dur ? f(dur) : undefined;
  const vol =
    typeof volume === "function" || (!fadeIn && !fadeOut)
      ? volume
      : (fr: number) => {
          const a = fadeIn ? interpolate(fr, [0, f(fadeIn)], [0, 1], { extrapolateRight: "clamp" }) : 1;
          const b = fadeOut && total ? interpolate(fr, [total - f(fadeOut), total], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 1;
          return (volume as number) * Math.min(a, b);
        };
  return (
    <Sequence from={f(at)} durationInFrames={total} layout="none" name={`sfx:${name}`}>
      <Audio src={staticFile(file)} volume={vol} loop={loop} playbackRate={playbackRate} />
    </Sequence>
  );
};

/** Looping room tone / ambience with soft fades, from `at` for `dur` seconds. */
export const Ambience: React.FC<{ name: SoundName; at?: number; dur: number; volume?: number; fade?: number }> = ({
  name,
  at = 0,
  dur,
  volume = 0.4,
  fade = 0.6,
}) => <Sound name={name} at={at} dur={dur} volume={volume} loop fadeIn={fade} fadeOut={fade} />;

/** The same one-shot repeated at several times (e.g. one marker squeak per X). */
export const Repeat: React.FC<{ name: SoundName; times: number[]; volume?: number; dur?: number }> = ({
  name,
  times,
  volume = 1,
  dur,
}) => (
  <>
    {times.map((t, i) => (
      <Sound key={i} name={name} at={t} volume={volume * (0.85 + ((i * 37) % 10) / 66)} dur={dur} playbackRate={0.94 + ((i * 53) % 12) / 100} />
    ))}
  </>
);
