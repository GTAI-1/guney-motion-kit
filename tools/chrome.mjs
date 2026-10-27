// The Chrome the checking tools drive: $CHROME_PATH if set, else the one HyperFrames renders with
// (`npx hyperframes browser path`; `npm run setup` downloads it once).
import { execSync } from 'node:child_process';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
export const puppeteer = require('puppeteer-core');
export function chromePath() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const out = execSync('npx --no-install hyperframes browser path', { cwd: new URL('..', import.meta.url).pathname, encoding: 'utf8' }).trim().split('\n').pop().trim();
  if (!out) throw new Error('No Chrome found: run `npm run setup` in the kit folder (or set CHROME_PATH).');
  return out;
}
