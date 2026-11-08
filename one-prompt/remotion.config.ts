import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(90);
Config.setOverwriteOutput(true);
Config.setConcurrency(null); // let Remotion pick based on CPU cores

// Use a locally installed Chrome Headless Shell instead of downloading one,
// e.g. REMOTION_BROWSER_EXECUTABLE=/path/to/chrome-headless-shell npm run render
if (process.env.REMOTION_BROWSER_EXECUTABLE) {
  Config.setBrowserExecutable(process.env.REMOTION_BROWSER_EXECUTABLE);
}
