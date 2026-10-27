// Seek a composition and evaluate an expression at each time (scenes expose window.__P etc. for this).
// Usage: node qa/evalat.mjs comp.html id "expr" t1 t2 ...
import fs from 'node:fs';
import { puppeteer, chromePath } from '../chrome.mjs';
const EXE = chromePath();
const [FILE, COMP, EXPR, ...ts] = process.argv.slice(2);
const browser = await puppeteer.launch({ executablePath: EXE, headless: true, args: ['--allow-file-access-from-files'] });
const page = await browser.newPage(); await page.setViewport({ width: 1920, height: 1080 });
const errs = []; page.on('pageerror', (e) => errs.push(e.message));
const html = fs.readFileSync(FILE, 'utf8').replace('<head>', `<head><base href="file://${process.cwd()}/">`);
const TMP = process.cwd() + '/qa/_eval-' + process.pid + '.html'; fs.writeFileSync(TMP, html);
await page.goto('file://' + TMP, { waitUntil: 'load' }); await page.evaluate(() => document.fonts.ready);
for (const t of ts.map(Number)) {
  const r = await page.evaluate(({ t, COMP, EXPR }) => { window.__timelines[COMP].seek(t, false); window.__timelines[COMP].seek(t, false); return JSON.stringify(eval(EXPR)); }, { t, COMP, EXPR });
  console.log(t, r);
}
if (errs.length) console.log('ERRORS', errs.join('\n'));
await browser.close(); fs.rmSync(TMP, { force: true });
