import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { FPS } from "../config";
import { SANS } from "../fonts";
import { ease, lerpF, typed } from "../util";

const SCREEN = { x: 300, y: 80, w: 1320, h: 780 };

/** Big laptop filling the frame; children render inside the screen. */
export const LaptopCloseup: React.FC<{ children: React.ReactNode; ambient?: string; zoom?: number }> = ({
  children,
  ambient = "#2a2f3d",
  zoom = 0.03,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const s = 1 + zoom * ease(frame, 0, durationInFrames);
  return (
    <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 40%, ${ambient} 0%, #0d0f14 85%)` }}>
      <AbsoluteFill style={{ transform: `scale(${s})`, transformOrigin: "50% 45%" }}>
        <div
          style={{
            position: "absolute",
            left: SCREEN.x - 26,
            top: SCREEN.y - 26,
            width: SCREEN.w + 52,
            height: SCREEN.h + 52,
            background: "#16181d",
            borderRadius: 28,
            boxShadow: "0 30px 80px rgba(0,0,0,0.6)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: SCREEN.x,
            top: SCREEN.y,
            width: SCREEN.w,
            height: SCREEN.h,
            background: "#fff",
            borderRadius: 6,
            overflow: "hidden",
            fontFamily: SANS,
          }}
        >
          {children}
        </div>
        <div
          style={{
            position: "absolute",
            left: SCREEN.x - 160,
            top: SCREEN.y + SCREEN.h + 26,
            width: SCREEN.w + 320,
            height: 40,
            background: "linear-gradient(#2b2e36, #16181d)",
            borderRadius: "0 0 40px 40px",
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Cursor: React.FC<{ color?: string; h?: number }> = ({ color = "#111", h = 1 }) => {
  const frame = useCurrentFrame();
  const on = Math.floor(frame / 15) % 2 === 0;
  return <span style={{ display: "inline-block", width: 4, height: `${h}em`, background: color, marginLeft: 3, verticalAlign: "-0.15em", opacity: on ? 1 : 0 }} />;
};

const BrowserChrome: React.FC<{ tabs: string[]; visibleTabs?: number; url: string; dark?: boolean }> = ({ tabs, visibleTabs, url, dark }) => {
  const n = visibleTabs ?? tabs.length;
  return (
    <div style={{ background: dark ? "#202124" : "#dee1e6", paddingTop: 10 }}>
      <div style={{ display: "flex", gap: 2, padding: "0 10px", overflow: "hidden" }}>
        {tabs.slice(0, n).map((t, i) => (
          <div
            key={i}
            style={{
              flex: "1 1 0",
              minWidth: 0,
              maxWidth: 220,
              background: i === n - 1 ? (dark ? "#35363a" : "#fff") : dark ? "#2b2c30" : "#cfd3d9",
              color: dark ? "#ddd" : "#333",
              fontSize: 15,
              padding: "9px 10px",
              borderRadius: "10px 10px 0 0",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {t}
          </div>
        ))}
      </div>
      <div style={{ background: dark ? "#35363a" : "#fff", padding: "10px 16px", borderBottom: "1px solid #ccc" }}>
        <div style={{ background: dark ? "#202124" : "#f1f3f4", color: dark ? "#ccc" : "#555", borderRadius: 20, padding: "8px 18px", fontSize: 18 }}>{url}</div>
      </div>
    </div>
  );
};

/* ------------------------- scene 1: course + tabs ------------------------- */
const TABS = [
  "AI for beginners",
  "Learn Python fast",
  "What is a neural net",
  "Prompt engineering 101",
  "Top 50 AI tools",
  "Machine learning roadmap",
  "Best AI course 2026?",
  "Linear algebra crash",
  "Become an AI expert",
  "AI MASTERY BOOTCAMP",
];

export const CourseScreen: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tabs = Math.min(TABS.length, 1 + Math.floor(frame / 4));
  const price = spring({ frame: frame - 50, fps, config: { damping: 9 } });
  return (
    <AbsoluteFill>
      <BrowserChrome tabs={TABS} visibleTabs={tabs} url="ai-mastery-bootcamp.example/enroll" />
      <div style={{ padding: "50px 80px", display: "flex", gap: 60, background: "linear-gradient(135deg,#0f172a,#312e81)", height: "100%", color: "white", position: "relative" }}>
        <div style={{ position: "absolute", left: 80, right: 80, top: 430, display: "flex", gap: 20 }}>
          {["Week 1 · Foundations", "Week 2 · Math & Python", "Week 3 · Deep Learning", "Week 4 · Build & Deploy"].map((w, i) => (
            <div key={w} style={{ flex: 1, height: 150, borderRadius: 16, background: "rgba(255,255,255,0.08)", padding: 20, opacity: ease(frame, 20 + i * 6, 32 + i * 6) }}>
              <div style={{ fontSize: 20, fontWeight: 600 }}>{w}</div>
              <div style={{ fontSize: 16, opacity: 0.6, marginTop: 10 }}>{12 - i} modules · {20 + i * 3}h of video</div>
              <div style={{ height: 6, background: "rgba(255,255,255,0.15)", borderRadius: 3, marginTop: 40 }} />
            </div>
          ))}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 20, letterSpacing: 6, opacity: 0.7 }}>30-DAY PROGRAM</div>
          <div style={{ fontSize: 64, fontWeight: 800, lineHeight: 1.05, marginTop: 12 }}>AI MASTERY BOOTCAMP</div>
          <div style={{ fontSize: 26, marginTop: 24, opacity: 0.85 }}>47 modules · 3 hours a day · Become an AI expert</div>
          <div style={{ display: "flex", gap: 14, marginTop: 30 }}>
            {["Python", "Math", "Neural nets", "Agents", "Vision"].map((t) => (
              <div key={t} style={{ fontSize: 18, padding: "8px 16px", borderRadius: 20, background: "rgba(255,255,255,0.15)" }}>{t}</div>
            ))}
          </div>
        </div>
        <div
          style={{
            width: 380,
            height: 330,
            background: "white",
            color: "#111",
            borderRadius: 24,
            padding: 34,
            transform: `scale(${0.85 + price * 0.15}) rotate(${(1 - price) * -4}deg)`,
            boxShadow: "0 20px 50px rgba(0,0,0,0.4)",
          }}
        >
          <div style={{ fontSize: 22, color: "#666" }}>Course</div>
          <div style={{ fontSize: 96, fontWeight: 800, lineHeight: 1.1 }}>$199</div>
          <div style={{ fontSize: 18, color: "#999", textDecoration: "line-through" }}>$499</div>
          <div style={{ marginTop: 24, background: "#ef4444", color: "white", fontWeight: 800, fontSize: 28, textAlign: "center", padding: "16px 0", borderRadius: 14 }}>ENROLL NOW</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ------------------------ scene 2: Module 1 of 47 ------------------------ */
export const ModuleScreen: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <BrowserChrome tabs={TABS} url="ai-mastery-bootcamp.example/course/module-1" dark />
      <div style={{ display: "flex", height: "100%", background: "#111" }}>
        <div style={{ flex: 1, padding: 36 }}>
          <div style={{ background: "#000", height: 430, borderRadius: 12, position: "relative", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ width: 120, height: 120, borderRadius: "50%", background: "rgba(255,255,255,0.15)", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <div style={{ width: 0, height: 0, borderTop: "30px solid transparent", borderBottom: "30px solid transparent", borderLeft: "48px solid white", marginLeft: 12 }} />
            </div>
            <div style={{ position: "absolute", bottom: 18, left: 20, right: 20, height: 6, background: "#333", borderRadius: 3 }}>
              <div style={{ width: 4, height: 6, background: "#ef4444" }} />
            </div>
            <div style={{ position: "absolute", bottom: 32, right: 22, color: "#aaa", fontSize: 18 }}>0:00 / 2:38:00</div>
          </div>
          <div style={{ color: "white", fontSize: 44, fontWeight: 800, marginTop: 30, opacity: ease(frame, 4, 16) }}>Module 1 of 47 – 2h 38min</div>
          <div style={{ color: "#888", fontSize: 22, marginTop: 8 }}>Introduction to the History of Artificial Intelligence (Part 1)</div>
        </div>
        <div style={{ width: 340, background: "#1b1b1b", padding: 24, color: "#bbb", fontSize: 18 }}>
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} style={{ padding: "13px 0", borderBottom: "1px solid #2c2c2c", color: i === 0 ? "white" : "#888" }}>
              Module {i + 1} · {["2h 38m", "3h 05m", "2h 51m", "4h 10m", "2h 22m", "3h 40m", "2h 59m", "3h 12m", "5h 01m"][i]}
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ----------------------------- chat interface ----------------------------- */
export const ChatScreen: React.FC<{
  prompt: string;
  reply?: string;
  /** seconds after mount when the reply starts */
  replyAt?: number;
  typeFrom?: number;
  history?: { prompt: string; reply: string }[];
  cps?: number;
}> = ({ prompt, reply = "", replyAt = 3, typeFrom = 0.4, history = [], cps = 20 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const typeStart = typeFrom * FPS;
  const n = typed(frame - typeStart, cps);
  const typingDone = n >= prompt.length;
  const sentAt = typeStart + (prompt.length / cps) * FPS + 10;
  const sent = frame >= sentAt;
  const replyStart = replyAt * FPS;
  const r = typed(frame - replyStart, 90);
  const sentPop = spring({ frame: frame - sentAt, fps, config: { damping: 14 } });

  return (
    <AbsoluteFill style={{ background: "#f7f7f8", display: "flex", flexDirection: "column" }}>
      <div style={{ height: 64, background: "white", borderBottom: "1px solid #e5e5e5", display: "flex", alignItems: "center", padding: "0 30px", gap: 14 }}>
        <div style={{ width: 34, height: 34, borderRadius: 10, background: "linear-gradient(135deg,#10b981,#3b82f6)" }} />
        <div style={{ fontSize: 24, fontWeight: 600, color: "#222" }}>AI Assistant</div>
      </div>
      <div style={{ flex: 1, padding: "30px 120px", display: "flex", flexDirection: "column", gap: 22, justifyContent: "flex-end", overflow: "hidden" }}>
        {history.map((h, i) => (
          <React.Fragment key={i}>
            <UserMsg text={h.prompt} />
            <BotMsg text={h.reply} />
          </React.Fragment>
        ))}
        {sent && (
          <div style={{ transform: `translateY(${(1 - sentPop) * 30}px)`, opacity: sentPop }}>
            <UserMsg text={prompt} />
          </div>
        )}
        {sent && frame < replyStart && <BotMsg text="" dots />}
        {reply && frame >= replyStart && <BotMsg text={reply.slice(0, r)} />}
      </div>
      <div style={{ padding: "18px 120px 34px" }}>
        <div style={{ background: "white", border: "2px solid #d9d9e3", borderRadius: 22, padding: "20px 26px", fontSize: 30, color: "#222", display: "flex", alignItems: "center", boxShadow: "0 4px 16px rgba(0,0,0,0.06)" }}>
          <div style={{ flex: 1 }}>
            {!sent ? (
              n > 0 ? (
                <>
                  {prompt.slice(0, n)}
                  <Cursor />
                </>
              ) : (
                <span style={{ color: "#aaa" }}>
                  Message AI Assistant…
                  <Cursor />
                </span>
              )
            ) : (
              <span style={{ color: "#aaa" }}>Message AI Assistant…</span>
            )}
          </div>
          <div style={{ width: 46, height: 46, borderRadius: 23, background: typingDone && !sent ? "#111" : "#ccc", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 26 }}>↑</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const UserMsg: React.FC<{ text: string }> = ({ text }) => (
  <div style={{ alignSelf: "flex-end", background: "#2563eb", color: "white", fontSize: 30, padding: "16px 26px", borderRadius: "26px 26px 6px 26px", maxWidth: "70%" }}>{text}</div>
);

const BotMsg: React.FC<{ text: string; dots?: boolean }> = ({ text, dots }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ alignSelf: "flex-start", display: "flex", gap: 16, maxWidth: "80%" }}>
      <div style={{ width: 44, height: 44, flex: "0 0 44px", borderRadius: 12, background: "linear-gradient(135deg,#10b981,#3b82f6)" }} />
      <div style={{ background: "white", color: "#222", fontSize: 28, lineHeight: 1.4, padding: "16px 26px", borderRadius: "6px 26px 26px 26px", boxShadow: "0 2px 10px rgba(0,0,0,0.06)", whiteSpace: "pre-wrap" }}>
        {dots ? (
          <span style={{ letterSpacing: 6 }}>
            {[0, 1, 2].map((i) => (
              <span key={i} style={{ opacity: 0.3 + 0.7 * Math.max(0, Math.sin(frame / 4 - i)) }}>●</span>
            ))}
          </span>
        ) : (
          text
        )}
      </div>
    </div>
  );
};

/* ------------------- scene 5: goal typed, then deleted ------------------- */
export const NotesScreen: React.FC<{ text: string; typeFrom: number; deleteAt: number }> = ({ text, typeFrom, deleteAt }) => {
  const frame = useCurrentFrame();
  const n = typed(frame - typeFrom * FPS, 14);
  const del = typed(frame - deleteAt * FPS, 24);
  const visible = Math.max(0, Math.min(text.length, n) - del);
  const deleting = frame >= deleteAt * FPS && visible > 0;
  return (
    <AbsoluteFill style={{ background: "#fffdf5", padding: "60px 110px", fontFamily: SANS }}>
      <div style={{ fontSize: 22, color: "#a08a5a", letterSpacing: 4 }}>NOTES · GOALS</div>
      <div style={{ fontSize: 52, fontWeight: 800, color: "#222", marginTop: 16 }}>New goal</div>
      <div style={{ height: 3, background: "#eadfc3", margin: "26px 0 44px" }} />
      <div style={{ fontSize: 64, fontWeight: 800, color: "#111", letterSpacing: 1 }}>
        <span style={{ background: deleting ? "rgba(239,68,68,0.15)" : "transparent" }}>{text.slice(0, visible)}</span>
        <Cursor h={1.05} />
      </div>
      <div style={{ position: "absolute", bottom: 50, left: 110, fontSize: 24, color: "#b9a77d", opacity: lerpF(frame, [deleteAt * FPS + 40, deleteAt * FPS + 60], [0, 1]) }}>
        Today: 1 prompt.
      </div>
    </AbsoluteFill>
  );
};
