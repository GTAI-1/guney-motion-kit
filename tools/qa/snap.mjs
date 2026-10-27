// Headless stills from a composition: seeks the timeline (and its videos) to each time and screenshots.
// Usage: node qa/snap.mjs s1-step.html s1 out-dir 0.5 1.0 1.5 ...   (or a range: --range 0 5 0.25)
import fs from 'node:fs';
import { puppeteer, chromePath } from '../chrome.mjs';
const EXE = chromePath();
const [FILE, COMP, OUT, ...rest] = process.argv.slice(2);
let times = rest.map(Number);
if (rest[0] === '--range') { const [a, b, s] = rest.slice(1).map(Number); times = []; for (let t = a; t <= b + 1e-9; t += s) times.push(+t.toFixed(4)); }
fs.mkdirSync(OUT, { recursive: true });
const browser = await puppeteer.launch({ executablePath: EXE, headless: true, args: ['--allow-file-access-from-files', '--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'] });
const page = await browser.newPage(); await page.setViewport({ width: 1920, height: 1080 });
const errs = []; page.on('pageerror', (e) => errs.push(e.message)); page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.text()); });
// compositions use project-root-relative paths: load a copy with <base> at the project root
const [FPATH, HASH = ''] = FILE.split('#');
const html = fs.readFileSync(FPATH, 'utf8').replace('<head>', `<head><base href="file://${process.cwd()}/">`);
const TMP = process.cwd() + '/qa/_snap-' + process.pid + '.html'; fs.writeFileSync(TMP, html);
await page.goto('file://' + TMP + (HASH ? '#' + HASH : ''), { waitUntil: 'load' });
await page.evaluate(() => document.fonts.ready);
if (!(await page.evaluate(() => !!window.__timelines))) { console.log('PAGE FAILED TO REGISTER A TIMELINE:\n' + [...new Set(errs)].join('\n')); await browser.close(); process.exit(1); }
for (const t of times) {
  await page.evaluate(async ({ t, COMP }) => {
    const vids = [...document.querySelectorAll('video[data-start]')];
    await Promise.all(vids.map((v) => new Promise((res) => {
      const s = +v.dataset.start, d = +(v.dataset.duration || 1e9), local = +(v.dataset.mediaStart || 0) + Math.max(0, Math.min(t - s, d - 0.001));
      if (Math.abs(v.currentTime - local) < 1e-4 && v.readyState >= 2) return res();
      const done = () => { v.removeEventListener('seeked', done); res(); }; v.addEventListener('seeked', done); v.currentTime = local; setTimeout(res, 3000);
    })));
    window.__timelines[COMP].seek(t, false);
    window.dispatchEvent(new CustomEvent('hf-seek', { detail: { time: t } }));   // as the renderer does after each seek (also redraws t = 0)
  }, { t, COMP });
  if (process.env.WAIT) await new Promise((r) => setTimeout(r, +process.env.WAIT));
  if (process.env.ALPHA) await page.evaluate(() => { for (const el of [document.documentElement, document.body]) el.style.background = 'transparent'; });   // plates: ALPHA=1 + a #dbg flag that hides the backdrop
  await page.screenshot({ path: `${OUT}/t${t.toFixed(3)}.png`, omitBackground: !!process.env.ALPHA });
  if (process.env.PROBE) console.log('probe', t, JSON.stringify(await page.evaluate(() => window.__probe || null)));
}
console.log('shots', times.length, errs.length ? 'ERRORS:\n' + [...new Set(errs)].join('\n') : 'no errors');
await browser.close(); fs.rmSync(TMP, { force: true });
