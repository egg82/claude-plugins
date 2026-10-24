// cards.mjs — title cards: kinetic type on the theme's colours, captured like any scene.
//
// A project's card scene is just:
//   import { card, words, logo } from "../cards.mjs";
//   export default card({ ms: 4000, markup: `<div class="stage"><div>${logo()}<h1>${words("Hello", 0.3)}</h1></div></div>` });
//
// Vocabulary: .stage (full-screen centred layer; stack several and fade one out with
// style="animation:out .6s ease-in 2.9s forwards"), h1/h2, .g (accent colour),
// .strike (animated strike-through; set --sd to its delay), words(text, startSec) for a
// word-by-word rise, logo() for the theme's logo with a pop-in.
import fs from "node:fs";

const theme = JSON.parse(fs.readFileSync("theme.json", "utf8"));
const FONT = theme.font ?? "Inter";
// top, bottom, side fractions a platform's overlays cover; text stays inside them
const SAFE = (process.env.PROMO_SAFE ?? "0 0 0").split(" ").map(Number);

const CSS = `
  html,body{margin:0;height:100%;background:${theme.bg};overflow:hidden;font-family:'${FONT}',sans-serif;color:${theme.ink}}
  body{background:radial-gradient(900px 600px at 12% 0%,${theme.accent}33,transparent 70%),
       radial-gradient(1000px 700px at 92% 100%,${theme.accent2 ?? theme.accent}33,transparent 70%),${theme.bg}}
  .stage{position:absolute;inset:${SAFE[0] * 100}% ${SAFE[2] * 100}% ${SAFE[1] * 100}%;display:grid;place-items:center;text-align:center}
  .w{display:inline-block;opacity:0;transform:translateY(38px);filter:blur(10px);
     animation:rise .9s cubic-bezier(.16,1,.3,1) forwards}
  @keyframes rise{to{opacity:1;transform:none;filter:none}}
  @keyframes out{to{opacity:0;transform:translateY(-30px);filter:blur(8px)}}
  @keyframes pop{0%{opacity:0;transform:scale(.6) rotate(-12deg)}60%{opacity:1;transform:scale(1.06) rotate(2deg)}100%{opacity:1;transform:none}}
  @keyframes strike{to{transform:scaleX(1)}}
  h1{font-weight:750;font-size:104px;letter-spacing:-.035em;line-height:1.05;margin:0}
  h2{font-weight:600;font-size:52px;letter-spacing:-.02em;margin:0;color:${theme.dim ?? theme.ink}}
  h1,h2{max-width:86vw;margin-inline:auto}                  /* wrap rather than touch the frame edge */
  .g{color:${theme.accent}}
  .strike{position:relative}
  .strike::after{content:"";position:absolute;left:-2%;right:-2%;top:54%;height:9px;border-radius:9px;background:${theme.bad ?? "#e5484d"};
     transform:scaleX(0);transform-origin:left;animation:strike .5s cubic-bezier(.65,0,.35,1) forwards;animation-delay:var(--sd)}
`;

export const words = (s, t0, step = 0.09) =>
  s.split(" ").map((w, i) => `<span class="w" style="animation-delay:${(t0 + i * step).toFixed(2)}s">${w}</span>`).join(" ");

export const logo = (delay = 0.2, size = 120) => theme.logo
  ? `<div style="opacity:0;animation:pop .8s cubic-bezier(.34,1.56,.64,1) ${delay}s forwards;width:${size}px;height:${size}px;margin:auto">
       ${fs.readFileSync(theme.logo, "utf8").replace("<svg", `<svg width="${size}" height="${size}"`)}</div>`
  : "";

// `voice` is a narration line spoken over the card (no caption: the card's text is on screen).
// `pops` are seconds at which something visibly pops in (the logo), for a matching sound.
export function card({ ms, markup, voice, pops = [] }) {
  return {
    options: { frame: false },                                // sized to the video's output frame
    async setup(page) {
      await page.setContent(`<html><head><link href="https://fonts.googleapis.com/css2?family=${encodeURIComponent(FONT)}:wght@500;600;750&display=block" rel="stylesheet">
        <style>${CSS}</style></head><body></body></html>`, { waitUntil: "networkidle" });
      await page.evaluate((f) => Promise.all(["500", "600", "750"].map((w) => document.fonts.load(`${w} 40px '${f}'`))), FONT);
      // A card set in a fallback font looks like a mistake; fail instead of filming it.
      if (!(await page.evaluate((f) => document.fonts.check(`750 40px '${f}'`), FONT))) throw new Error(`${FONT} did not load`);
    },
    async act(page, d) {
      await page.evaluate((h) => (document.body.innerHTML = h), markup);
      for (const p of pops) d.cues.push({ t: d.now() + p, kind: "pop" });
      if (voice) { await d.wait(250); await d.say(voice, { caption: false }); }
      await d.wait(ms);
    },
  };
}
