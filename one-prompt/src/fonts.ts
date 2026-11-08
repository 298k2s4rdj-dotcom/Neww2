import "@fontsource/playfair-display/400.css";
import "@fontsource/playfair-display/400-italic.css";
import "@fontsource/inter/400.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/800.css";
import "@fontsource/permanent-marker/400.css";
import { continueRender, delayRender } from "remotion";

export const SERIF = "'Playfair Display', Georgia, serif";
export const SANS = "Inter, Helvetica, Arial, sans-serif";
export const MARKER = "'Permanent Marker', 'Comic Sans MS', cursive";

// Make sure every font is loaded before the first frame is captured.
if (typeof document !== "undefined") {
  const handle = delayRender("Loading fonts");
  Promise.all(
    [
      "400 40px 'Playfair Display'",
      "italic 400 40px 'Playfair Display'",
      "400 40px Inter",
      "600 40px Inter",
      "800 40px Inter",
      "400 40px 'Permanent Marker'",
    ].map((f) => document.fonts.load(f)),
  )
    .catch(() => undefined)
    .then(() => continueRender(handle));
}
