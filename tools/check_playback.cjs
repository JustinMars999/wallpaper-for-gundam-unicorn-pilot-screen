// SPDX-License-Identifier: GPL-3.0-only
const { existsSync } = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

async function main(filename) {
  if (!filename || !existsSync(filename)) {
    throw new Error("Pass the path to a local release MP4.");
  }
  const browser = await chromium.launch({
    ...(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : { channel: "chrome" }),
    headless: true,
    args: ["--autoplay-policy=no-user-gesture-required"],
  });
  try {
    const page = await browser.newPage({ viewport: { width: 960, height: 540 } });
    await page.goto(pathToFileURL(path.join(__dirname, "loop-player.html")).href);
    const result = await page.evaluate(async (url) => {
      const video = document.querySelector("video");
      function nextEvent(name) {
        return new Promise((resolve, reject) => {
          const controller = new AbortController();
          const options = { once: true, signal: controller.signal };
          const timeout = setTimeout(() => finish(new Error("Timed out waiting for " + name)), 15000);
          function finish(error) {
            clearTimeout(timeout);
            controller.abort();
            if (error) reject(error);
            else resolve();
          }
          video.addEventListener(name, () => finish(), options);
          video.addEventListener("error", () => finish(new Error(video.error?.message || "Video error")), options);
        });
      }
      const loaded = nextEvent("loadedmetadata");
      video.src = url;
      await loaded;
      if (video.duration !== 180) throw new Error("Unexpected duration " + video.duration);
      const sought = nextEvent("seeked");
      video.currentTime = video.duration - 0.65;
      await sought;
      await video.play();

      let displayedFrames = 0;
      const crossed = await new Promise((resolve, reject) => {
        let previous = null;
        const timeout = setTimeout(() => reject(new Error("No playback wrap after " + previous)), 18000);
        function observe(_now, frame) {
          displayedFrames += 1;
          if (previous > 179 && frame.mediaTime < 0.7) {
            clearTimeout(timeout);
            resolve([previous, frame.mediaTime]);
            return;
          }
          previous = frame.mediaTime;
          video.requestVideoFrameCallback(observe);
        }
        video.requestVideoFrameCallback(observe);
      });
      await new Promise((resolve) => setTimeout(resolve, 200));
      video.pause();
      if (video.currentTime <= crossed[1]) throw new Error("Playback stopped at the loop boundary.");
      return { crossed, displayedFrames, width: video.videoWidth, height: video.videoHeight, continuedAt: video.currentTime };
    }, pathToFileURL(path.resolve(filename)).href);
    console.log(JSON.stringify(result));
  } finally {
    await browser.close();
  }
}
main(process.argv[2]).catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
