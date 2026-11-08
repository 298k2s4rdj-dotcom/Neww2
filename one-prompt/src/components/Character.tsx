import React from "react";
import { useCurrentFrame } from "remotion";
import { blinkAt, breath } from "../util";

export type Mood =
  | "neutral"
  | "happy"
  | "tired"
  | "sad"
  | "surprised"
  | "skeptical"
  | "determined"
  | "stressed";

export type Look = "max" | "lena" | "friend" | "boss";

export type Arm = { s: number; e: number };

export type CharacterProps = {
  look: Look;
  /** ground position (feet) in scene coordinates */
  x: number;
  y: number;
  scale?: number;
  /** 1 = facing right, -1 = facing left */
  dir?: 1 | -1;
  mood?: Mood;
  /** pupil offset, -1..1 */
  lookX?: number;
  lookY?: number;
  sitting?: boolean;
  /** shoulder angle (deg, 0 = hanging, + = towards facing side) and elbow bend */
  armBack?: Arm;
  armFront?: Arm;
  /** body lean in degrees (+ = forward) */
  lean?: number;
  headTilt?: number;
  /** walking cycle phase in radians, undefined = standing still */
  walk?: number;
  /** 0..1 slump of shoulders / head (sigh, tiredness) */
  slump?: number;
  /** extra vertical offset of the body (e.g. jump) */
  bob?: number;
  seed?: number;
  /** force eyes closed amount */
  eyesClosed?: number;
  /** render something in the front hand (local coords at the hand) */
  holding?: React.ReactNode;
};

const HIP_Y = -185;
const SHOULDER_Y = -330;
const HEAD_Y = -405;
const HEAD_R = 60;
const UPPER = 80;
const FORE = 78;

const rad = (d: number) => (d * Math.PI) / 180;

const armPoints = (sx: number, sy: number, a: Arm) => {
  const ex = sx + Math.sin(rad(a.s)) * UPPER;
  const ey = sy + Math.cos(rad(a.s)) * UPPER;
  const hx = ex + Math.sin(rad(a.s + a.e)) * FORE;
  const hy = ey + Math.cos(rad(a.s + a.e)) * FORE;
  return { ex, ey, hx, hy };
};

/** Expressive white eyes + eyebrows + small mouth, drawn around head center. */
const Face: React.FC<{
  mood: Mood;
  blink: number;
  lookX: number;
  lookY: number;
  glasses?: boolean;
}> = ({ mood, blink, lookX, lookY, glasses }) => {
  const eyeX = 22;
  const eyeY = -4;
  const big = mood === "surprised" || mood === "stressed";
  const rx = big ? 15 : 13;
  const ry = big ? 20 : 17;
  const baseLid =
    mood === "tired" ? 0.52 : mood === "sad" ? 0.28 : mood === "skeptical" || mood === "determined" ? 0.2 : 0;
  const lid = Math.min(1, baseLid + blink * (1 - baseLid));
  const px = lookX * 5;
  const py = lookY * 6 + (mood === "sad" ? 4 : 0);
  const pupilR = big ? 5 : 6.5;

  // eyebrows: [inner y, outer y] offsets relative to eye top
  const brow: Record<Mood, [number, number]> = {
    neutral: [-10, -10],
    happy: [-15, -13],
    tired: [-4, 0],
    sad: [-16, -5],
    surprised: [-22, -20],
    skeptical: [-9, -9],
    determined: [-3, -12],
    stressed: [-18, -8],
  };
  const [bi, bo] = brow[mood];

  const eye = (side: -1 | 1) => {
    const cx = side * eyeX;
    const by = eyeY - ry;
    // skeptical: one brow raised
    const raise = mood === "skeptical" && side === 1 ? -9 : 0;
    const browPath = `M ${cx - side * -12 * 0 + side * -2} ${by + bi + raise} L ${cx + side * 16} ${by + bo + raise}`;
    // Draw brow from inner (towards nose) to outer
    const inner = cx - side * 13;
    const outer = cx + side * 14;
    const browD = `M ${inner} ${by + bi + raise} Q ${cx} ${by + Math.min(bi, bo) - 4 + raise} ${outer} ${by + bo + raise}`;
    void browPath;
    return (
      <g key={side}>
        {mood === "happy" && blink < 0.5 ? (
          <path
            d={`M ${cx - rx} ${eyeY + 4} Q ${cx} ${eyeY - ry - 4} ${cx + rx} ${eyeY + 4}`}
            stroke="white"
            strokeWidth={6}
            fill="none"
            strokeLinecap="round"
          />
        ) : (
          <>
            <ellipse cx={cx} cy={eyeY} rx={rx} ry={ry} fill="white" />
            <circle cx={cx + px} cy={eyeY + py} r={pupilR} fill="#111" />
            {lid > 0 && (
              <rect x={cx - rx - 3} y={eyeY - ry - 3} width={rx * 2 + 6} height={(ry * 2 + 4) * lid + 1} fill="#000" />
            )}
            {lid > 0.05 && lid < 0.98 && (
              <line
                x1={cx - rx + 1}
                x2={cx + rx - 1}
                y1={eyeY - ry - 2 + (ry * 2 + 4) * lid}
                y2={eyeY - ry - 2 + (ry * 2 + 4) * lid}
                stroke="#000"
                strokeWidth={3}
              />
            )}
          </>
        )}
        <path d={browD} stroke="white" strokeWidth={6} fill="none" strokeLinecap="round" />
        {glasses && (
          <circle cx={cx} cy={eyeY} r={23} fill="none" stroke="white" strokeWidth={4} opacity={0.95} />
        )}
      </g>
    );
  };

  const mouth = (() => {
    const my = 30;
    switch (mood) {
      case "happy":
        return <path d={`M -15 ${my - 3} Q 0 ${my + 12} 15 ${my - 3}`} stroke="white" strokeWidth={5} fill="none" strokeLinecap="round" />;
      case "determined":
        return <path d={`M -11 ${my} Q 0 ${my + 5} 11 ${my - 1}`} stroke="white" strokeWidth={5} fill="none" strokeLinecap="round" />;
      case "sad":
        return <path d={`M -12 ${my + 5} Q 0 ${my - 5} 12 ${my + 5}`} stroke="white" strokeWidth={5} fill="none" strokeLinecap="round" />;
      case "surprised":
        return <ellipse cx={0} cy={my + 2} rx={7} ry={9} fill="white" />;
      case "stressed":
        return <path d={`M -14 ${my + 2} q 4.6 -5 9.3 0 q 4.6 5 9.3 0 q 4.6 -5 9.3 0`} transform="translate(-0 0)" stroke="white" strokeWidth={4} fill="none" strokeLinecap="round" />;
      case "tired":
        return <line x1={-9} x2={9} y1={my + 2} y2={my + 2} stroke="white" strokeWidth={4.5} strokeLinecap="round" />;
      default:
        return <path d={`M -10 ${my} Q 0 ${my + 4} 10 ${my}`} stroke="white" strokeWidth={4.5} fill="none" strokeLinecap="round" />;
    }
  })();

  return (
    <g>
      {eye(-1)}
      {eye(1)}
      {glasses && <path d="M -2 -6 Q 0 -10 2 -6" stroke="white" strokeWidth={4} fill="none" />}
      {mouth}
    </g>
  );
};

/** Solid black silhouette character with expressive white eyes. */
export const Character: React.FC<CharacterProps> = (p) => {
  const frame = useCurrentFrame();
  const {
    look,
    x,
    y,
    scale = 1,
    dir = 1,
    mood = "neutral",
    lookX = 0.4,
    lookY = 0,
    sitting = false,
    lean = 0,
    headTilt = 0,
    walk,
    slump = 0,
    bob = 0,
    seed = 1,
    eyesClosed = 0,
  } = p;

  const b = breath(frame, seed);
  const blink = Math.max(blinkAt(frame, seed), eyesClosed);
  const walking = walk !== undefined;
  const swing = walking ? Math.sin(walk!) : 0;
  const stepBob = walking ? Math.abs(Math.cos(walk!)) * -8 : 0;

  const defaultBack: Arm = { s: walking ? -swing * 22 : 6, e: walking ? 10 : 8 };
  const defaultFront: Arm = { s: walking ? swing * 22 : -6, e: walking ? 14 : 10 };
  const armBack = p.armBack ?? defaultBack;
  const armFront = p.armFront ?? defaultFront;

  const breathe = 1 + b * 0.012;
  const shoulderDrop = slump * 14;
  const headDrop = slump * 22;
  const headForward = slump * 10;

  const bodyW = look === "boss" ? 76 : look === "max" ? 70 : look === "lena" ? 58 : 64;
  const hipW = look === "lena" ? 50 : look === "boss" ? 66 : 56;
  const sy = SHOULDER_Y + shoulderDrop;

  // torso path (shoulders rounded)
  const torso = `M ${-hipW} ${HIP_Y + 10}
    L ${-bodyW} ${sy + 34}
    Q ${-bodyW} ${sy} ${-bodyW + 34} ${sy - 4}
    L ${bodyW - 34} ${sy - 4}
    Q ${bodyW} ${sy} ${bodyW} ${sy + 34}
    L ${hipW} ${HIP_Y + 10} Z`;

  const legW = look === "boss" ? 36 : 32;
  let legs: React.ReactNode;
  if (sitting) {
    legs = (
      <g stroke="#000" strokeWidth={legW} strokeLinecap="round" strokeLinejoin="round" fill="none">
        <polyline points={`-18,${HIP_Y + 6} 82,${HIP_Y + 6} 86,-16`} />
        <polyline points={`16,${HIP_Y + 6} 104,${HIP_Y + 2} 112,-16`} />
        <ellipse cx={100} cy={-10} rx={24} ry={11} fill="#000" stroke="none" />
        <ellipse cx={126} cy={-10} rx={24} ry={11} fill="#000" stroke="none" />
      </g>
    );
  } else {
    const la = swing * 24;
    const leg = (hx: number, ang: number, key: string) => {
      const kx = hx + Math.sin(rad(ang)) * 90;
      const ky = HIP_Y + 6 + Math.cos(rad(ang)) * 90;
      const fx = kx + Math.sin(rad(ang * 0.6 - Math.max(0, -ang) * 0.6)) * 92;
      const fy = Math.min(-14, ky + 92);
      return (
        <g key={key}>
          <polyline points={`${hx},${HIP_Y + 6} ${kx},${ky} ${fx},${fy}`} stroke="#000" strokeWidth={legW} strokeLinecap="round" strokeLinejoin="round" fill="none" />
          <ellipse cx={fx + 14} cy={fy + 4} rx={26} ry={11} fill="#000" />
        </g>
      );
    };
    legs = (
      <>
        {leg(-20, -la, "l1")}
        {leg(20, la, "l2")}
      </>
    );
  }

  const shoulderBack = { x: -bodyW + 18, y: sy + 14 };
  const shoulderFront = { x: bodyW - 18, y: sy + 14 };
  const ab = armPoints(shoulderBack.x, shoulderBack.y, armBack);
  const af = armPoints(shoulderFront.x, shoulderFront.y, armFront);
  const armW = look === "max" ? 30 : look === "boss" ? 30 : 26;

  const arm = (s: { x: number; y: number }, pts: ReturnType<typeof armPoints>, key: string) => (
    <g key={key}>
      <polyline
        points={`${s.x},${s.y} ${pts.ex},${pts.ey} ${pts.hx},${pts.hy}`}
        stroke="#000"
        strokeWidth={armW}
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <circle cx={pts.hx} cy={pts.hy} r={armW * 0.62} fill="#000" />
    </g>
  );

  const hx = headForward;
  const hy = HEAD_Y + headDrop + b * 1.5;

  const accessoriesBehindHead =
    look === "max" ? (
      // hood
      <path
        d={`M ${-HEAD_R - 16} ${hy + 10} Q ${-HEAD_R - 20} ${hy - HEAD_R - 22} 0 ${hy - HEAD_R - 18} Q ${HEAD_R + 20} ${hy - HEAD_R - 22} ${HEAD_R + 16} ${hy + 10} L ${bodyW - 10} ${sy + 20} L ${-bodyW + 10} ${sy + 20} Z`}
        fill="#000"
      />
    ) : look === "lena" ? (
      <>
        <circle cx={hx - 6} cy={hy - HEAD_R - 14} r={27} fill="#000" />
        <path d={`M ${-HEAD_R - 6} ${hy} Q ${-HEAD_R - 12} ${hy + 60} ${-HEAD_R + 6} ${hy + 76} L ${HEAD_R - 6} ${hy + 76} Q ${HEAD_R + 12} ${hy + 60} ${HEAD_R + 6} ${hy} Z`} fill="#000" />
      </>
    ) : null;

  const accessoriesFrontHead =
    look === "friend" ? (
      <g>
        <path d={`M ${hx - HEAD_R - 4} ${hy - 14} Q ${hx - HEAD_R} ${hy - HEAD_R - 14} ${hx} ${hy - HEAD_R - 14} Q ${hx + HEAD_R} ${hy - HEAD_R - 14} ${hx + HEAD_R + 4} ${hy - 14} Z`} fill="#000" />
        <path d={`M ${hx - 10} ${hy - 22} Q ${hx + 60} ${hy - 36} ${hx + 112} ${hy - 18} Q ${hx + 60} ${hy - 12} ${hx - 10} ${hy - 12} Z`} fill="#000" />
        <circle cx={hx} cy={hy - HEAD_R - 14} r={6} fill="#000" />
        <path d={`M ${hx - HEAD_R + 2} ${hy - 20} Q ${hx} ${hy - 30} ${hx + HEAD_R - 2} ${hy - 20}`} stroke="#2a2a2a" strokeWidth={3} fill="none" />
      </g>
    ) : look === "boss" ? (
      <path d={`M ${hx - HEAD_R + 4} ${hy - 26} Q ${hx - 20} ${hy - HEAD_R - 18} ${hx + HEAD_R - 2} ${hy - 30} Q ${hx + 10} ${hy - HEAD_R + 2} ${hx - HEAD_R + 4} ${hy - 26}`} fill="#000" />
    ) : null;

  return (
    <g transform={`translate(${x} ${y + bob}) scale(${scale * dir} ${scale})`}>
      {/* soft ground shadow */}
      <ellipse cx={sitting ? 50 : 0} cy={0} rx={sitting ? 110 : 80} ry={12} fill="#000" opacity={0.18} />
      <g transform={`translate(0 ${stepBob})`}>
        {legs}
        <g transform={`rotate(${lean} 0 ${HIP_Y})`}>
          {arm(shoulderBack, ab, "back")}
          <g transform={`translate(0 ${HIP_Y}) scale(1 ${breathe}) translate(0 ${-HIP_Y})`}>
            <path d={torso} fill="#000" />
            {look === "max" && (
              <>
                <path d={`M ${-34} ${HIP_Y - 30} L ${34} ${HIP_Y - 30} L ${26} ${HIP_Y - 66} L ${-26} ${HIP_Y - 66} Z`} fill="none" stroke="#1d1d1d" strokeWidth={3} />
                <line x1={-12} y1={sy + 4} x2={-14} y2={sy + 56} stroke="white" strokeWidth={3.5} strokeLinecap="round" opacity={0.9} />
                <line x1={12} y1={sy + 4} x2={14} y2={sy + 56} stroke="white" strokeWidth={3.5} strokeLinecap="round" opacity={0.9} />
              </>
            )}
            {look === "boss" && (
              <>
                <path d={`M -26 ${sy - 4} L 0 ${sy + 46} L 26 ${sy - 4} Z`} fill="white" />
                <path d={`M -7 ${sy + 4} L 7 ${sy + 4} L 10 ${sy + 70} L 0 ${sy + 86} L -10 ${sy + 70} Z`} fill="#000" />
              </>
            )}
            {look === "lena" && (
              <path d={`M -16 ${sy - 2} Q 0 ${sy + 18} 16 ${sy - 2}`} stroke="#222" strokeWidth={3} fill="none" />
            )}
          </g>
          <g transform={`rotate(${headTilt} ${hx} ${hy + HEAD_R})`}>
            {accessoriesBehindHead}
            <rect x={hx - 16} y={hy + HEAD_R - 14} width={32} height={30} fill="#000" />
            <circle cx={hx} cy={hy} r={HEAD_R} fill="#000" />
            {accessoriesFrontHead}
            <g transform={`translate(${hx + 6} ${hy + 4})`}>
              <Face mood={mood} blink={blink} lookX={lookX} lookY={lookY} glasses={look === "lena"} />
            </g>
          </g>
          {arm(shoulderFront, af, "front")}
          {p.holding && <g transform={`translate(${af.hx} ${af.hy})`}>{p.holding}</g>}
        </g>
      </g>
    </g>
  );
};
