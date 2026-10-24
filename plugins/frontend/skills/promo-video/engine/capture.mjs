// capture.mjs — run one scene and record it as timestamped CDP screencast frames.
//
//   node capture.mjs <scene>        (cwd = the build dir: scenes/, theme.json, out/)
//
// A scene module exports setup(page, d) and act(page, d), and optionally
// `options` = { w, h, dsf, frame }. Only act() is recorded. Writes
// out/<scene>/frames/*.jpg + list.txt (ffmpeg concat list with each frame's real
// duration), cues.json (camera/caption/sound cues) and cap_<n>.png caption pills.
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { Director } from "./director.mjs";

const scene = process.argv[2];
const mod = await import(path.resolve(`scenes/${scene}.mjs`));
const { setup, act } = mod.default ?? mod;
// The video's format (set by build.sh) decides the page viewport and a card's size;
// a scene's own `options` still win for anything it sets explicitly.
const env = process.env;
const fmt = { vw: +(env.PROMO_VW ?? 1280), vh: +(env.PROMO_VH ?? 720), ow: +(env.PROMO_OW ?? 1920), oh: +(env.PROMO_OH ?? 1080) };
const sceneOpt = mod.options ?? mod.default?.options ?? {};
const opt = sceneOpt.frame === false
  ? { frame: false, w: fmt.ow, h: fmt.oh, dsf: 1 }             // a card fills the output frame
  : { frame: true, w: fmt.vw, h: fmt.vh, dsf: 2, ...sceneOpt };
const theme = JSON.parse(fs.readFileSync("theme.json", "utf8"));
const W = opt.w, H = opt.h, DSF = opt.dsf;
const out = `out/${scene}`;
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(`${out}/frames`, { recursive: true });

const browser = await chromium.launch({ args: ["--hide-scrollbars", "--force-color-profile=srgb"] });
const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: DSF, colorScheme: theme.colorScheme ?? "dark" });
const page = await ctx.newPage();
const dir = await Director.attach(page, { accent: theme.accent });

// A live site can be slow (right after a deploy, or while its backend works). Setup is off
// camera, so its waits are generous; the recorded part keeps Playwright's usual 30s.
page.setDefaultTimeout(120000);
await setup(page, dir);
page.setDefaultTimeout(30000);

const cdp = await ctx.newCDPSession(page);
const frames = [];
let n = 0;
cdp.on("Page.screencastFrame", async ({ data, metadata, sessionId }) => {
  const f = `${out}/frames/${String(n++).padStart(6, "0")}.jpg`;
  fs.writeFileSync(f, Buffer.from(data, "base64"));
  frames.push({ f, ts: metadata.timestamp });
  cdp.send("Page.screencastFrameAck", { sessionId }).catch(() => {});
});
await cdp.send("Page.startScreencast", { format: "jpeg", quality: 92, maxWidth: W * DSF, maxHeight: H * DSF, everyNthFrame: 1 });
await page.waitForTimeout(300);
// Instrument: sample every 100ms whether any "loading…" text is on screen, so a loading state
// the camera saw is reported as a number rather than hoped absent from a few sampled frames.
await page.evaluate(() => {
  window.__loadingSeen = [];
  setInterval(() => {
    const on = [...document.querySelectorAll("body *")].some((e) => e.childElementCount === 0
      && e.offsetParent !== null && /^\s*loading\W*$/i.test(e.textContent));
    if (on) window.__loadingSeen.push(Date.now());
  }, 100);
});
dir.start();
const tStart = Date.now() / 1000;
await act(page, dir);
await dir.drain();                                           // let the last line finish
await page.waitForTimeout(400);
await cdp.send("Page.stopScreencast");
const tEnd = Date.now() / 1000;
const loadingSeen = (await page.evaluate(() => window.__loadingSeen ?? []).catch(() => []))
  .map((ms) => ms / 1000 - tStart).filter((t) => t >= 0);

// Caption pills, rendered by the browser so they get real type.
const caps = dir.cues.filter((c) => c.kind === "caption");
if (caps.length) {
  const cp = await browser.newPage({ viewport: { width: fmt.ow, height: 400 }, deviceScaleFactor: 1 });
  const font = theme.font ?? "Inter";
  for (let i = 0; i < caps.length; i++) {
    // narration lines run long: wrap inside ~80% of the frame rather than overflow it
    await cp.setContent(`<html><head><link href="https://fonts.googleapis.com/css2?family=${encodeURIComponent(font)}:wght@600&display=block" rel="stylesheet"></head>
      <body style="margin:0;background:transparent"><div id=p style="display:inline-flex;align-items:center;gap:14px;padding:16px 28px 16px 22px;
      max-width:${Math.round(fmt.ow * 0.8)}px;box-sizing:border-box;line-height:1.25;
      border-radius:34px;background:${theme.surface}ee;border:1px solid ${theme.accent}77;box-shadow:0 10px 40px rgba(0,0,0,.5);
      font:600 34px '${font}',sans-serif;color:${theme.ink};letter-spacing:-.01em"><span style="width:12px;height:12px;border-radius:50%;
      background:${theme.accent};box-shadow:0 0 14px ${theme.accent}"></span>${caps[i].text}</div></body></html>`, { waitUntil: "networkidle" });
    await cp.evaluate((f) => document.fonts.load(`600 34px '${f}'`), font);
    await cp.locator("#p").screenshot({ path: `${out}/cap_${i}.png`, omitBackground: true });
  }
}
await browser.close();

// Fast-forward windows compress time: T maps a recording time (s from start) to cut time.
const ffs = dir.cues.filter((c) => c.kind === "ff");
const T = (t) => t - ffs.reduce((s, w) => s + Math.max(0, Math.min(t, w.end) - w.t) * (1 - 1 / w.speed), 0);

// Screencast emits only on paint, so frames are irregular; give each its real (retimed) duration.
const kept = frames.filter((fr, i) => fr.ts >= tStart || (frames[i + 1] && frames[i + 1].ts > tStart));
if (!kept.length) throw new Error(`${scene}: no frames captured`);
let list = "";
for (let i = 0; i < kept.length; i++) {
  const a = Math.max(kept[i].ts, tStart) - tStart, b = (kept[i + 1] ? kept[i + 1].ts : tEnd) - tStart;
  const d = T(b) - T(a);
  if (d < 0.0005) continue;                                  // swallowed by a fast-forward
  list += `file '${path.basename(kept[i].f)}'\nduration ${d.toFixed(4)}\n`;
}
list += `file '${path.basename(kept.at(-1).f)}'\n`;
fs.writeFileSync(`${out}/frames/list.txt`, list);
// A caption's on-screen span compresses with the picture; speech plays in real time, so a
// "say" cue keeps its duration and only moves.
const cues = dir.cues.filter((c) => c.kind !== "ff").map((c) => ({
  ...c, t: T(c.t), ...(c.dur && c.kind !== "say" ? { dur: T(c.t + c.dur) - T(c.t) } : {}) }));
const duration = T(tEnd - tStart);
// on-camera "loading…" time, after fast-forwards: each 100ms sample counts for its retimed span
const loadingOnCamera = loadingSeen.reduce((s, t) => s + (T(t + 0.1) - T(t)), 0);
const loadingAt = [...new Set(loadingSeen.map((t) => +T(t).toFixed(1)))];     // cut-time seconds, for finding it
fs.writeFileSync(`${out}/cues.json`, JSON.stringify({ W, H, DSF, frame: opt.frame, duration, loadingOnCamera, loadingAt, cues }, null, 1));
console.log(`${scene}: ${kept.length} frames, ${(tEnd - tStart).toFixed(1)}s recorded -> ${duration.toFixed(1)}s cut, ${cues.length} cues`
  + (loadingOnCamera > 0.05 ? `  WARNING: "loading…" on camera for ${loadingOnCamera.toFixed(2)}s` : ""));
