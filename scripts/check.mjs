#!/usr/bin/env node
// npm run check   A quick health check: the tools, the render browser, and a 1-second render of the starter.
import { execSync, spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, cpSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const run = (c, o = {}) => execSync(c, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], ...o }).trim();
console.log('  ok   node ' + process.versions.node);
for (const t of ['ffmpeg', 'ffprobe']) console.log(spawnSync(t, ['-version'], { stdio: 'ignore' }).status === 0 ? `  ok   ${t}` : `  FIX  ${t} missing`);
console.log('  ok   render browser: ' + run('npx --no-install hyperframes browser path', { cwd: root }).split('\n').pop());
const tmp = mkdtempSync(join(tmpdir(), 'gmk-')), dest = join(tmp, 'check');
cpSync(join(root, 'templates/starter'), dest, { recursive: true });
cpSync(join(root, 'lib'), join(dest, 'assets'), { recursive: true });
cpSync(join(root, 'fonts'), join(dest, 'assets/fonts'), { recursive: true });
execSync(`node -e "require('fs').writeFileSync('${join(dest, 'assets/kit-config.js')}', 'window.KIT = {user:\\'there\\'};')"`);
const hf = join(root, 'node_modules/.bin/hyperframes');   // the kit's own HyperFrames (the temp folder has no node_modules)
run(`"${hf}" render -o "${join(dest, 'check.mp4')}" --fps 30 --quality draft`, { cwd: dest });
const ok = existsSync(join(dest, 'check.mp4'));
console.log(ok ? '  ok   rendered the starter' : '  FIX  the starter did not render');
rmSync(tmp, { recursive: true, force: true });
process.exit(ok ? 0 : 1);
