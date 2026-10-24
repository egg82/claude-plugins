// director.mjs — human-paced choreography on a Playwright page.
//
// The page gets a drawn cursor (the real one never appears in a capture), and every
// action is timed: the cursor travels an eased curve, typing has a cadence, scrolls
// ease. Each action also records a camera cue ({t, rect, zoom}) so a post pass can
// punch in on whatever is being touched.

import fs from "node:fs";

const CURSOR_JS = (accent) => {
  const install = () => {
    if (document.getElementById("__cur")) return;
    const c = document.createElement("div");
    c.id = "__cur";
    c.innerHTML = `<svg width="26" height="26" viewBox="0 0 24 24"><path d="M4 2 L4 19 L8.5 15 L11.5 22 L14.5 20.6 L11.6 14 L18 14 Z"
      fill="#fff" stroke="#0b0e16" stroke-width="1.4" stroke-linejoin="round"/></svg>`;
    Object.assign(c.style, {
      position: "fixed", left: "0", top: "0", zIndex: 2147483647, pointerEvents: "none",
      translate: "-100px -100px", filter: "drop-shadow(0 2px 3px rgba(0,0,0,.45))",
      transition: "scale .12s ease", transformOrigin: "4px 2px",
    });
    document.documentElement.appendChild(c);
    const style = document.createElement("style");
    style.textContent = `
      * { cursor: none !important; }
      .__ripple { position: fixed; z-index: 2147483646; pointer-events: none; width: 14px; height: 14px;
        margin: -7px 0 0 -7px; border-radius: 50%; border: 2px solid ${accent};
        animation: __rip .55s cubic-bezier(.2,.7,.3,1) forwards; }
      @keyframes __rip { to { transform: scale(4.2); opacity: 0; } }
      html { scroll-behavior: auto !important; }
      ::-webkit-scrollbar { display: none; }`;
    document.documentElement.appendChild(style);
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install);
  else install();
};

const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2); // easeInOutCubic

export class Director {
  constructor(page, { fps = 60 } = {}) {
    this.page = page;
    this.fps = fps;
    this.x = 960; this.y = 600;
    this.t0 = null;
    this.cues = [];           // camera cues for the post pass
  }

  static async attach(page, opts = {}) {
    await page.addInitScript(CURSOR_JS, opts.accent ?? "#6fcf8b");
    return new Director(page, opts);
  }

  start() { this.t0 = Date.now(); }
  now() { return (Date.now() - this.t0) / 1000; }
  // `pt` is where the cursor will rest: the camera keeps it in frame, since that is where the
  // eye goes; `rect` is what it tries to fit whole.
  cue(kind, rect = null, zoom = 1, pt = null) { this.cues.push({ t: this.now(), kind, rect, zoom, pt }); }

  async wait(ms) { await this.page.waitForTimeout(ms); }

  async #place(x, y) {
    this.x = x; this.y = y;
    await this.page.mouse.move(x, y);
    await this.page.evaluate(([x, y]) => {
      const c = document.getElementById("__cur");
      if (c) c.style.translate = `${x}px ${y}px`; // `translate`, not `transform`: CSS `scale` would shrink a transform's offset too
    }, [x, y]);
  }

  // Eased travel along a gently bowed curve; duration scales with distance.
  async moveTo(x, y, { ms } = {}) {
    const dx = x - this.x, dy = y - this.y;
    const dist = Math.hypot(dx, dy);
    const dur = ms ?? Math.min(1100, 380 + dist * 0.55);
    const steps = Math.max(8, Math.round((dur / 1000) * this.fps));
    const sx = this.x, sy = this.y;
    // control point off to one side of the line, so the path arcs like a wrist does
    const bow = Math.min(90, dist * 0.18);
    const cx = sx + dx / 2 - (dy / (dist || 1)) * bow;
    const cy = sy + dy / 2 + (dx / (dist || 1)) * bow;
    const start = Date.now();
    for (let i = 1; i <= steps; i++) {
      const t = ease(i / steps);
      const px = (1 - t) ** 2 * sx + 2 * (1 - t) * t * cx + t * t * x;
      const py = (1 - t) ** 2 * sy + 2 * (1 - t) * t * cy + t * t * y;
      await this.#place(px, py);
      const due = start + (dur * i) / steps;
      const lag = due - Date.now();
      if (lag > 0) await this.page.waitForTimeout(lag);
    }
  }

  // The target's box, after an eased scroll if it is off screen: the mouse acts at viewport
  // coordinates, so an off-screen target would take the click somewhere else, silently.
  async box(target, { reveal = true } = {}) {
    const loc = typeof target === "string" ? this.page.locator(target).first() : target;
    await loc.waitFor({ state: "visible", timeout: 15000 });
    let b = await loc.boundingBox();
    if (!b) throw new Error(`no box for ${target}`);
    const vh = await this.page.evaluate(() => innerHeight);
    if (reveal && (b.y < 0 || b.y + Math.min(b.height, vh * 0.6) > vh)) {
      const y = (await this.page.evaluate(() => scrollY)) + b.y - vh * 0.3;
      await this.scrollTo(y, { ms: 900 });
      b = await loc.boundingBox();
    }
    return { loc, b };
  }

  // `spot` dims everything but the target in post, for as long as the camera rests on it.
  // `below` rests the cursor just under the target so it never covers what's being read.
  async hover(target, { zoom = 1, dwell = 500, spot = false, below = false } = {}) {
    const { b } = await this.box(target);
    const pt = { x: b.x + b.width / 2, y: below ? b.y + b.height + 6 : b.y + b.height / 2 };
    this.cue("focus", b, zoom, pt);
    if (spot) this.cues.at(-1).spot = true;
    await this.moveTo(pt.x, pt.y);
    await this.settle();
    await this.wait(dwell);
  }

  async click(target, { zoom = 1, dwell = 350, offset } = {}) {
    const { b } = await this.box(target);
    const x = b.x + (offset?.x ?? b.width / 2), y = b.y + (offset?.y ?? b.height / 2);
    this.cue("focus", b, zoom, { x, y });
    await this.moveTo(x, y);
    await this.wait(120);
    await this.page.evaluate(([x, y]) => {
      const c = document.getElementById("__cur");
      c.style.scale = "0.82";
      const r = document.createElement("div");
      r.className = "__ripple"; r.style.left = x + "px"; r.style.top = y + "px";
      document.documentElement.appendChild(r);
      setTimeout(() => r.remove(), 700);
      setTimeout(() => (c.style.scale = "1"), 140);
    }, [x, y]);
    this.cues.push({ t: this.now(), kind: "click" });
    await this.page.mouse.down();
    await this.wait(70);
    await this.page.mouse.up();
    await this.settle();
    await this.wait(dwell);
  }

  // Choose from a <select>. A native dropdown never paints in a headless capture, so the
  // cursor clicks the control (motion and ripple) and the value is set directly.
  async select(target, value, { zoom = 1, dwell = 600 } = {}) {
    await this.drain();          // the fast-forward below can't run under speech; wait before moving, not mid-click
    const { loc, b } = await this.box(target);
    const x = b.x + b.width / 2, y = b.y + b.height / 2;
    this.cue("focus", b, zoom, { x, y });
    await this.moveTo(x, y);
    await this.wait(120);
    await this.page.evaluate(([x, y]) => {
      const r = document.createElement("div");
      r.className = "__ripple"; r.style.left = x + "px"; r.style.top = y + "px";
      document.documentElement.appendChild(r);
      setTimeout(() => r.remove(), 700);
    }, [x, y]);
    this.cues.push({ t: this.now(), kind: "click" });
    // A select usually reloads what it filters, often flashing "loading…" for a moment: too
    // brief for settle() to see, long enough for a viewer to. Fast-forward through it.
    await this.fastForward(async () => {
      await loc.selectOption(value);
      await this.page.waitForTimeout(400);
      await this.#loadingGone(15000);
    });
    await this.wait(dwell);
  }

  // Drag horizontally across a control (a slider) between two fractions of its width.
  async drag(target, from, to, { zoom = 1, ms = 1600 } = {}) {
    const { b } = await this.box(target);
    const y = b.y + b.height / 2;
    this.cue("focus", b, zoom, { x: b.x + b.width * to, y });
    await this.moveTo(b.x + b.width * from, y);
    await this.wait(150);
    await this.page.evaluate(() => (document.getElementById("__cur").style.scale = "0.82"));
    await this.page.mouse.down();
    await this.moveTo(b.x + b.width * to, y, { ms });
    await this.page.mouse.up();
    await this.page.evaluate(() => (document.getElementById("__cur").style.scale = "1"));
  }

  // Type with a human cadence: quick runs, a short hitch after spaces.
  async type(text, { cps = 11 } = {}) {
    for (const ch of text) {
      await this.page.keyboard.type(ch);
      let d = 1000 / cps * (0.6 + Math.random() * 0.8);
      if (ch === " ") d += 90;
      await this.wait(d);
    }
  }

  // Eased window scroll to bring an element (or an absolute y) near the top third.
  async scrollTo(target, { ms = 1100, frac = 0.22 } = {}) {
    let y;
    if (typeof target === "number") y = target;
    else {
      const { b } = await this.box(target, { reveal: false });
      const cur = await this.page.evaluate(() => scrollY);
      const vh = await this.page.evaluate(() => innerHeight);
      y = cur + b.y - vh * frac;
    }
    const from = await this.page.evaluate(() => scrollY);
    this.cue("scroll");
    // the sound pass gives a real move a whoosh as long as the move itself
    Object.assign(this.cues.at(-1), { dur: ms / 1000, dist: Math.abs(Math.max(0, y) - from) });
    await this.page.evaluate(async ([to, ms]) => {
      const from = scrollY, t0 = performance.now();
      const e = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
      await new Promise((res) => {
        const step = (now) => {
          const k = Math.min(1, (now - t0) / ms);
          scrollTo(0, from + (to - from) * e(k));
          k < 1 ? requestAnimationFrame(step) : res();
        };
        requestAnimationFrame(step);
      });
    }, [Math.max(0, y), ms]);
  }

  // Camera back to the full frame.
  wide() { this.cue("wide", null, 1); }

  // Narration. vo.py synthesized every d.say("...") literal before filming, so the length is
  // known: a line waits for the previous one to finish, then speaks while the scene carries
  // on. It also becomes the caption, since most people watch muted and some miss captions.
  async say(text, { caption = true } = {}) {
    this.vo ??= JSON.parse(fs.readFileSync("vo/index.json", "utf8"));
    const line = this.vo[text];
    if (!line) throw new Error(`no voiceover for ${JSON.stringify(text)}: d.say() needs a string literal`);
    await this.drain();
    this.cues.push({ t: this.now(), kind: "say", text, file: line.file, dur: line.dur });
    // `caption` may be its own shorter wording: a word-for-word transcript under the voice is
    // redundant, a tighter phrase keeps it interesting. Delivery tags ("[curious] …") are
    // for the voice, never shown.
    const shown = typeof caption === "string" ? caption : text.replace(/\[[^\]]*\]\s*/g, "").trim();
    if (caption) this.caption(shown, line.dur + 0.3);
    this.speakingUntil = Date.now() + line.dur * 1000;
  }

  // Wait until the current line has been spoken.
  async drain() {
    const left = (this.speakingUntil ?? 0) - Date.now();
    if (left > 0) await this.wait(left + 150);
  }

  // A caption pill composited over the clip in post (never drawn in the page).
  caption(text, dur = 2.2) { this.cues.push({ t: this.now(), kind: "caption", text, dur }); }

  // Let anything the cursor just triggered finish loading before the scene moves on: a hover
  // card that reads "loading…" when the cursor leaves is missed polish. The wait plays fast.
  // Predicates are real functions, never strings: a site whose CSP forbids 'unsafe-eval' makes
  // a string predicate throw, and that throw once hid inside a .catch() so this wait silently
  // never happened. A wait that times out warns; it is never swallowed.
  async #loadingGone(timeout) {
    try {
      await this.page.waitForFunction(() => ![...document.querySelectorAll("body *")].some((e) =>
        e.childElementCount === 0 && e.offsetParent !== null && /^\s*loading\W*$/i.test(e.textContent)), null, { timeout });
    } catch (e) {
      if (!/Timeout/.test(e.message)) throw e;
      console.warn(`settle: still loading after ${timeout}ms`);
    }
  }

  async settle(timeout = 6000) {
    await this.wait(350);                                // hover cards open after a short delay
    const loading = await this.page.evaluate(() => [...document.querySelectorAll("body *")].some((e) =>
      e.childElementCount === 0 && e.offsetParent !== null && /^\s*loading\W*$/i.test(e.textContent)));
    if (!loading) return;
    await this.fastForward(() => this.#loadingGone(timeout));
    await this.wait(400);                                // a beat to see what loaded
  }

  // Off camera, in setup(): where the cursor starts. Its first move otherwise sets off from the
  // centre, and crossing anything with a hover card on the way flashes a "loading…" card.
  async startAt(x, y) {
    await this.page.mouse.move(x, y);
    this.x = x; this.y = y;
    await this.page.evaluate(([x, y]) => {
      const c = document.getElementById("__cur");
      if (c) c.style.translate = `${x}px ${y}px`;
    }, [x, y]);
  }

  // Off camera, in setup(): hover `target` until whatever it opens has finished loading, then
  // leave. Sites cache hover cards, so on camera the card opens already filled — waiting on
  // camera, however well trimmed, still shows a "loading…" state.
  async prewarm(target, timeout = 30000) {
    const loc = typeof target === "string" ? this.page.locator(target).first() : target;
    await loc.hover();
    await this.page.waitForTimeout(400);
    await this.#loadingGone(timeout);
    await this.page.mouse.move(2, 2);
    await this.page.waitForTimeout(300);
  }

  // Play whatever `fn` waits for (a slow server, a re-render) at `speed`x in the final cut.
  // capture.mjs retimes the frames and every later cue, so nothing downstream sees the gap.
  // 20x is effectively a cut: a load wait is a still page and a still camera, nothing to watch.
  async fastForward(fn, speed = 20) {
    await this.drain();                                  // speech is real-time: never compress under it
    const t = this.now();
    await fn();
    this.cues.push({ t, end: this.now(), kind: "ff", speed });
  }

  // A low sound accent at this moment: the one beat the story turns on. Use once or twice.
  accent(delay = 0.45) { this.cues.push({ t: this.now() + delay, kind: "accent" }); }

  // Rest the cursor somewhere neutral so hover cards don't pop open.
  // A resting cursor can land on something with a hover card, so it settles like a hover.
  async park(x, y) { await this.moveTo(x, y, { ms: 450 }); await this.settle(); }
}
