import React from "react";
import { useCurrentFrame } from "remotion";
import { PALETTE, TimeOfDay } from "./palette";
import { Window } from "./Window";
import { Bin, Chair, Fridge, Laptop } from "./Props";

/* ---------- layout constants shared by scenes ---------- */
export const APT = {
  floor: 900,
  deskSeatX: 505, // character ground x when sitting at the desk
  laptop: { x: 760, y: 660 },
  chart: { x: 1085, y: 230 }, // top-center of the wall chart
  chartScale: 0.92,
  bin: { x: 1150, y: 900 },
  fridge: { x: 1250, y: 900 },
  sofaSeatX: 1560, // character ground x when sitting on the sofa
  sofaGround: 905,
};

export const CAFE = {
  ground: 1010,
  maxX: 560,
  lenaX: 1360,
  tableTop: 760,
  scale: 1.1,
};

const Gradient: React.FC<{ id: string; from: string; to: string; vertical?: boolean }> = ({ id, from, to, vertical = true }) => (
  <linearGradient id={id} x1="0" y1="0" x2={vertical ? 0 : 1} y2={vertical ? 1 : 0}>
    <stop offset="0" stopColor={from} />
    <stop offset="1" stopColor={to} />
  </linearGradient>
);

const LampGlow: React.FC<{ x: number; y: number; r: number; o: number; id: string; color?: string }> = ({ x, y, r, o, id, color = "#ffd58a" }) => (
  <>
    <defs>
      <radialGradient id={id}>
        <stop offset="0" stopColor={color} stopOpacity={0.55 * o} />
        <stop offset="1" stopColor={color} stopOpacity={0} />
      </radialGradient>
    </defs>
    <circle cx={x} cy={y} r={r} fill={`url(#${id})`} />
  </>
);

/* ---------------------------------- CAFÉ ---------------------------------- */
export const CafeBackground: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <g>
      <defs>
        <Gradient id="cafe-wall" from="#e0a06c" to="#6e4558" />
        <Gradient id="cafe-sky" from="#ff9a55" to="#5b3f86" />
        <Gradient id="cafe-floor" from="#5e3d2e" to="#3a261d" />
      </defs>
      <rect width={1920} height={1080} fill="url(#cafe-wall)" />
      {/* big window to the street */}
      <rect x={540} y={130} width={840} height={450} rx={10} fill="url(#cafe-sky)" />
      <circle cx={1180} cy={520} r={70} fill="#ffcf73" opacity={0.85} />
      <path d="M 540 580 L 540 430 L 640 430 L 640 380 L 760 380 L 760 470 L 880 470 L 880 350 L 980 350 L 980 440 L 1120 440 L 1120 400 L 1240 400 L 1240 460 L 1380 460 L 1380 580 Z" fill="#2b1d33" opacity={0.75} />
      {[600, 700, 820, 930, 1060, 1180, 1300].map((x, i) => (
        <rect key={x} x={x} y={470 + (i % 3) * 20} width={10} height={12} fill="#ffd98a" opacity={0.6 + 0.3 * Math.sin(frame / 20 + i)} />
      ))}
      <rect x={952} y={130} width={16} height={450} fill="#3b2730" />
      <rect x={530} y={120} width={860} height={14} fill="#3b2730" />
      <rect x={530} y={576} width={860} height={18} fill="#3b2730" />
      {/* menu board + shelves */}
      <rect x={110} y={170} width={300} height={190} rx={8} fill="#2a2a2a" />
      {[210, 245, 280, 315].map((y) => (
        <line key={y} x1={140} x2={140 + ((y * 7) % 120) + 120} y1={y} y2={y} stroke="#f2e7d0" strokeWidth={6} strokeLinecap="round" opacity={0.7} />
      ))}
      <rect x={1520} y={260} width={300} height={12} fill="#3b2730" />
      <rect x={1520} y={380} width={300} height={12} fill="#3b2730" />
      {[1550, 1600, 1660, 1720, 1770].map((x, i) => (
        <rect key={x} x={x} y={i % 2 ? 210 : 220} width={34} height={i % 2 ? 50 : 40} rx={6} fill={["#c96b4b", "#e8d8b8", "#7a9a7a", "#d8a650", "#b55"][i]} />
      ))}
      {/* pendant lamps */}
      {[760, 1160].map((x, i) => (
        <g key={x}>
          <line x1={x} y1={0} x2={x} y2={150} stroke="#2a1c22" strokeWidth={4} />
          <path d={`M ${x - 55} 205 Q ${x} 130 ${x + 55} 205 Z`} fill="#2a1c22" />
          <LampGlow x={x} y={220} r={330} o={1} id={`cafe-lamp-${i}`} />
        </g>
      ))}
      {/* floor */}
      <rect x={0} y={1010} width={1920} height={70} fill="url(#cafe-floor)" />
      <rect x={0} y={700} width={1920} height={310} fill="#000" opacity={0.08} />
    </g>
  );
};

export const CafeTable: React.FC<{ x?: number }> = ({ x = 960 }) => (
  <g>
    <rect x={x - 230} y={CAFE.tableTop} width={460} height={22} rx={8} fill="#2b1a14" />
    <rect x={x - 14} y={CAFE.tableTop + 20} width={28} height={CAFE.ground - CAFE.tableTop - 30} fill="#2b1a14" />
    <ellipse cx={x} cy={CAFE.ground - 6} rx={90} ry={10} fill="#2b1a14" />
    {/* coffee cups */}
    <g transform={`translate(${x - 160} ${CAFE.tableTop})`}>
      <rect x={-18} y={-34} width={36} height={34} rx={6} fill="#f4efe6" />
      <path d="M 18 -26 q 14 2 0 16" stroke="#f4efe6" strokeWidth={5} fill="none" />
    </g>
    <g transform={`translate(${x + 170} ${CAFE.tableTop})`}>
      <rect x={-18} y={-34} width={36} height={34} rx={6} fill="#f4efe6" />
      <path d="M -18 -26 q -14 2 0 16" stroke="#f4efe6" strokeWidth={5} fill="none" />
    </g>
  </g>
);

export const CafeChairs: React.FC = () => (
  <>
    <Chair x={CAFE.maxX} y={CAFE.ground} scale={CAFE.scale} dir={1} color="#24160f" />
    <Chair x={CAFE.lenaX} y={CAFE.ground} scale={CAFE.scale} dir={-1} color="#24160f" />
  </>
);

/* -------------------------------- APARTMENT -------------------------------- */
export const ApartmentBackground: React.FC<{
  time: TimeOfDay;
  fridgeOpen?: number;
  laptopGlow?: number;
  showLaptop?: boolean;
  laptopOnSofa?: boolean;
  lampOn?: boolean;
}> = ({ time, fridgeOpen = 0, laptopGlow = 0.8, showLaptop = true, lampOn }) => {
  const pal = PALETTE[time];
  const lamp = lampOn ?? pal.lamp > 0;
  const id = `apt-${time}`;
  return (
    <g>
      <defs>
        <Gradient id={`${id}-wall`} from={pal.wall[0]} to={pal.wall[1]} />
        <Gradient id={`${id}-floor`} from={pal.floor[0]} to={pal.floor[1]} />
      </defs>
      <rect width={1920} height={1080} fill={`url(#${id}-wall)`} />
      <rect x={0} y={APT.floor} width={1920} height={180} fill={`url(#${id}-floor)`} />
      <rect x={0} y={APT.floor - 14} width={1920} height={14} fill="#000" opacity={0.18} />
      <Window x={120} y={190} w={300} h={380} time={time} id={id} />
      {/* shelf with plant */}
      <rect x={560} y={330} width={220} height={12} fill="#6b4f3a" />
      <rect x={590} y={290} width={40} height={40} fill="#c0533a" />
      <path d="M 610 290 q -30 -50 -10 -70 M 610 290 q 20 -60 40 -60 M 610 290 q 0 -50 6 -80" stroke="#3f7d4a" strokeWidth={10} fill="none" strokeLinecap="round" />
      <rect x={660} y={300} width={22} height={30} fill="#3d6fb6" />
      <rect x={686} y={292} width={18} height={38} fill="#e0b84f" />
      {/* desk */}
      <rect x={560} y={660} width={360} height={20} rx={4} fill="#6b4f3a" />
      <rect x={580} y={680} width={16} height={220} fill="#5a4130" />
      <rect x={884} y={680} width={16} height={220} fill="#5a4130" />
      <rect x={780} y={680} width={120} height={110} fill="#5a4130" />
      <line x1={790} x2={890} y1={735} y2={735} stroke="#3f2d22" strokeWidth={3} />
      {/* desk lamp */}
      <g>
        <rect x={860} y={648} width={44} height={12} rx={4} fill="#2b2b2b" />
        <line x1={882} y1={650} x2={850} y2={560} stroke="#2b2b2b" strokeWidth={8} />
        <path d="M 820 560 L 880 548 L 870 590 Z" fill="#2b2b2b" />
        {lamp && <LampGlow x={850} y={600} r={300} o={1} id={`${id}-desklamp`} />}
      </g>
      <Chair x={APT.deskSeatX} y={APT.floor} dir={1} color="#2f2f37" />
      {showLaptop && <Laptop x={APT.laptop.x} y={APT.laptop.y} dir={-1} glow={laptopGlow} />}
      {/* fridge */}
      <Fridge x={APT.fridge.x} y={APT.fridge.y} open={fridgeOpen} />
      <rect x={1280} y={480} width={40} height={30} fill="#f1c40f" transform="rotate(-6 1300 495)" opacity={fridgeOpen > 0.3 ? 0 : 1} />
      {/* sofa */}
      <g>
        <rect x={1480} y={600} width={420} height={140} rx={40} fill="#4b6584" />
        <rect x={1470} y={710} width={440} height={110} rx={30} fill="#566f90" />
        <rect x={1450} y={660} width={60} height={170} rx={26} fill="#4b6584" />
        <rect x={1880} y={660} width={60} height={170} rx={26} fill="#4b6584" />
        <rect x={1490} y={820} width={18} height={80} fill="#2f3d52" />
        <rect x={1870} y={820} width={18} height={80} fill="#2f3d52" />
        <rect x={1760} y={640} width={90} height={80} rx={20} fill="#e0a458" transform="rotate(-10 1805 680)" />
      </g>
      {/* floor lamp near sofa */}
      <g>
        <line x1={1430} y1={900} x2={1430} y2={430} stroke="#2b2b2b" strokeWidth={8} />
        <path d="M 1385 430 L 1475 430 L 1455 370 L 1405 370 Z" fill={lamp ? "#ffe2a0" : "#d9d2c3"} />
        {lamp && <LampGlow x={1430} y={430} r={360} o={1} id={`${id}-floorlamp`} />}
      </g>
      <Bin x={APT.bin.x} y={APT.bin.y} scale={0.9} />
      {/* night tint */}
      {(time === "night" || time === "rain") && <rect width={1920} height={1080} fill="#0a1030" opacity={0.18} />}
    </g>
  );
};

/* --------------------------------- BEDROOM --------------------------------- */
export const BedroomBackground: React.FC<{ time?: TimeOfDay }> = ({ time = "morning" }) => {
  const pal = PALETTE[time];
  return (
    <g>
      <defs>
        <Gradient id="bed-wall" from={pal.wall[0]} to={pal.wall[1]} />
        <Gradient id="bed-floor" from={pal.floor[0]} to={pal.floor[1]} />
        <linearGradient id="bed-sunbeam" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#fff3cf" stopOpacity={0.55} />
          <stop offset="1" stopColor="#fff3cf" stopOpacity={0} />
        </linearGradient>
      </defs>
      <rect width={1920} height={1080} fill="url(#bed-wall)" />
      <rect x={0} y={900} width={1920} height={180} fill="url(#bed-floor)" />
      <Window x={180} y={200} w={320} h={380} time={time} id="bedroom" />
      <path d="M 500 200 L 1100 900 L 700 900 L 180 580 Z" fill="url(#bed-sunbeam)" />
      {/* framed pictures */}
      <rect x={900} y={260} width={160} height={120} fill="#fff" stroke="#6b4f3a" strokeWidth={10} />
      <path d="M 910 370 L 960 310 L 1000 350 L 1030 320 L 1050 370 Z" fill="#7fb3d5" />
      <rect x={1100} y={240} width={110} height={150} fill="#fff" stroke="#6b4f3a" strokeWidth={10} />
      <circle cx={1155} cy={300} r={28} fill="#f5b041" />
      {/* bed */}
      <rect x={1440} y={480} width={50} height={420} rx={14} fill="#6b4f3a" />
      <rect x={700} y={690} width={760} height={110} rx={20} fill="#f2efe8" />
      <rect x={700} y={680} width={560} height={130} rx={24} fill="#7a9cc6" />
      <rect x={1270} y={630} width={160} height={70} rx={30} fill="white" />
      <rect x={690} y={800} width={790} height={30} rx={8} fill="#6b4f3a" />
      <rect x={710} y={830} width={20} height={70} fill="#5a4130" />
      <rect x={1440} y={830} width={20} height={70} fill="#5a4130" />
      {/* nightstand */}
      <rect x={1530} y={700} width={200} height={200} rx={8} fill="#8a6a4f" />
      <line x1={1550} x2={1710} y1={790} y2={790} stroke="#6b4f3a" strokeWidth={4} />
      <circle cx={1630} cy={750} r={7} fill="#5a4130" />
      <circle cx={1630} cy={840} r={7} fill="#5a4130" />
    </g>
  );
};

/* ---------------------------------- OFFICE --------------------------------- */
export const OfficeBackground: React.FC = () => (
  <g>
    <defs>
      <Gradient id="off-wall" from="#d8e2ea" to="#aebfcc" />
      <Gradient id="off-floor" from="#7f8c99" to="#5f6b77" />
    </defs>
    <rect width={1920} height={1080} fill="url(#off-wall)" />
    {[0, 1, 2, 3].map((i) => (
      <g key={i}>
        <rect x={140 + i * 430} y={140} width={340} height={330} fill="#cfe6f7" />
        <rect x={140 + i * 430} y={140} width={340} height={330} fill="none" stroke="#f4f7fa" strokeWidth={12} />
        <line x1={310 + i * 430} x2={310 + i * 430} y1={140} y2={470} stroke="#f4f7fa" strokeWidth={8} />
        <rect x={160 + i * 430} y={330} width={60} height={140} fill="#9fb7c9" />
        <rect x={240 + i * 430} y={280} width={50} height={190} fill="#9fb7c9" />
        <rect x={380 + i * 430} y={360} width={80} height={110} fill="#9fb7c9" />
      </g>
    ))}
    <rect x={0} y={900} width={1920} height={180} fill="url(#off-floor)" />
    {/* desk with monitor */}
    <rect x={560} y={650} width={460} height={20} rx={4} fill="#ece6dc" />
    <rect x={580} y={670} width={14} height={230} fill="#c9c2b6" />
    <rect x={986} y={670} width={14} height={230} fill="#c9c2b6" />
    <rect x={800} y={470} width={200} height={130} rx={8} fill="#1d1f24" />
    <rect x={810} y={480} width={180} height={110} rx={4} fill="#eaf4ff" />
    <rect x={824} y={494} width={90} height={10} fill="#3d7bfd" />
    {[516, 532, 548].map((y) => (
      <rect key={y} x={824} y={y} width={150} height={6} fill="#b8c7d6" />
    ))}
    <rect x={824} y={562} width={20} height={20} fill="#16a34a" />
    <rect x={850} y={552} width={20} height={30} fill="#16a34a" />
    <rect x={876} y={540} width={20} height={42} fill="#16a34a" />
    <rect x={890} y={600} width={20} height={40} fill="#1d1f24" />
    <rect x={860} y={636} width={80} height={14} rx={4} fill="#1d1f24" />
    <Chair x={505} y={900} dir={1} color="#2f2f37" />
    {/* plant */}
    <rect x={1700} y={800} width={90} height={100} rx={10} fill="#c0533a" />
    <path d="M 1745 800 q -60 -80 -30 -160 M 1745 800 q 50 -90 70 -150 M 1745 800 q 0 -100 10 -190" stroke="#3f7d4a" strokeWidth={14} fill="none" strokeLinecap="round" />
  </g>
);
