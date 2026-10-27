#!/usr/bin/env node
// npm run setup [-- --name "Alex" --house-style on|off]
// Checks the tools, installs packages and the render browser, asks two questions (your first name, for the Claude window
// greeting; whether to turn on the Guney house style), writes kit.config.json, and syncs the assistant files.
import { execSync, spawnSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { createInterface } from 'node:readline/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const ok = (m) => console.log('  ok   ' + m), bad = (m) => console.log('  FIX  ' + m);
const has = (cmd, flag = '-version') => spawnSync(cmd, [flag], { stdio: 'ignore' }).status === 0;
const os = process.platform, hint = { darwin: 'brew install ffmpeg', win32: 'winget install Gyan.FFmpeg', linux: 'sudo apt install ffmpeg' }[os] || 'install FFmpeg';
let problems = 0;
console.log('\nChecking tools');
const major = +process.versions.node.split('.')[0];
major >= 22 ? ok(`Node ${process.versions.node}`) : (bad(`Node ${process.versions.node}: install Node 22 or newer from nodejs.org`), problems++);
has('ffmpeg') ? ok('ffmpeg') : (bad(`ffmpeg missing: ${hint}`), problems++);
has('ffprobe') ? ok('ffprobe') : (bad(`ffprobe missing: it comes with FFmpeg (${hint})`), problems++);
has('python3', '--version') || has('python', '--version') ? ok('Python (for the checking tools)') : bad('Python 3 missing: only the checking tools need it (python.org); numpy and Pillow for the Resolve finish');
if (problems) { console.log('\nInstall the missing tools above, then run npm run setup again.\n'); process.exit(1); }
if (!existsSync(join(root, 'node_modules/hyperframes'))) { console.log('\nInstalling packages'); execSync('npm install', { cwd: root, stdio: 'inherit' }); }
console.log('\nGetting the render browser (Chrome for HyperFrames)');
execSync('npx --no-install hyperframes browser ensure', { cwd: root, stdio: 'inherit' });
// two questions (flags skip them; no terminal: defaults)
const arg = (k) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : undefined; };
const prev = existsSync(join(root, 'kit.config.json')) ? JSON.parse(readFileSync(join(root, 'kit.config.json'), 'utf8')) : {};
let name = arg('name') ?? prev.user, house = arg('house-style') ?? (prev.houseStyle === undefined ? undefined : prev.houseStyle ? 'on' : 'off');
if ((name === undefined || house === undefined) && process.stdin.isTTY) {
  const rl = createInterface({ input: process.stdin, output: process.stdout });
  if (name === undefined) name = (await rl.question('\nYour first name (the Claude window greets you with it): ')).trim() || 'there';
  if (house === undefined) house = /^y/i.test((await rl.question('Turn on the Guney house style (animated background, graphics that build on screen, built-in checks)? [Y/n] ')).trim() || 'y') ? 'on' : 'off';
  rl.close();
}
const cfg = { user: name || 'there', houseStyle: (house ?? 'on') === 'on' };
writeFileSync(join(root, 'kit.config.json'), JSON.stringify(cfg, null, 2) + '\n');
ok(`kit.config.json: name "${cfg.user}", house style ${cfg.houseStyle ? 'on' : 'off'}`);
execSync('node scripts/sync.mjs', { cwd: root, stdio: 'inherit' });
console.log(`\nReady. Next:\n  npm run new-video -- hello\n  cd video-projects/hello\n  npx hyperframes render -o renders/hello.mp4\n`);
