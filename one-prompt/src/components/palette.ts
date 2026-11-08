export type TimeOfDay = "day" | "evening" | "night" | "morning" | "rain";

export const PALETTE: Record<TimeOfDay, { wall: [string, string]; sky: [string, string]; floor: [string, string]; lamp: number }> = {
  day: { wall: ["#efe3cf", "#d9c7aa"], sky: ["#7fbcf5", "#d6efff"], floor: ["#a88763", "#8a6c4d"], lamp: 0 },
  morning: { wall: ["#f5e6cf", "#e2c9a8"], sky: ["#ffcf9a", "#bcdcff"], floor: ["#b08e69", "#8f7052"], lamp: 0 },
  evening: { wall: ["#d9a57b", "#93635a"], sky: ["#ff9757", "#6a4b8c"], floor: ["#7a5a45", "#5a4033"], lamp: 0.6 },
  night: { wall: ["#3e4466", "#272b45"], sky: ["#0b1330", "#1e2a56"], floor: ["#3b3346", "#2a2433"], lamp: 1 },
  rain: { wall: ["#3c4456", "#242a38"], sky: ["#4c5768", "#262d39"], floor: ["#363645", "#262631"], lamp: 1 },
};
