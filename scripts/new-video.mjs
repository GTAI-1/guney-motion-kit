#!/usr/bin/env node
// npm run new-video -- <slug>   Creates video-projects/<slug>: the starter (index.html), the kit library in assets/
// (scripts, styles, fonts, sound effects), and empty compositions/ plan/ qa/ renders/ folders.
import { cpSync, mkdirSync, existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const slug = process.argv[2];
if (!slug || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) { console.log('Usage: npm run new-video -- <lowercase-slug>   (e.g. my-first-video)'); process.exit(1); }
const dest = join(root, 'video-projects', slug);
if (existsSync(dest)) { console.log(`video-projects/${slug} already exists: pick another name.`); process.exit(1); }
const cfg = existsSync(join(root, 'kit.config.json')) ? JSON.parse(readFileSync(join(root, 'kit.config.json'), 'utf8')) : { user: 'there', houseStyle: true };
cpSync(join(root, 'templates/starter'), dest, { recursive: true });
cpSync(join(root, 'lib'), join(dest, 'assets'), { recursive: true });
cpSync(join(root, 'fonts'), join(dest, 'assets/fonts'), { recursive: true });
cpSync(join(root, 'sfx'), join(dest, 'assets/audio/sfx'), { recursive: true });
for (const d of ['compositions', 'plan', 'qa', 'renders']) mkdirSync(join(dest, d), { recursive: true });
writeFileSync(join(dest, 'assets/kit-config.js'), `window.KIT = ${JSON.stringify(cfg)};\n`);
writeFileSync(join(dest, 'hyperframes.json'), JSON.stringify({ $schema: 'https://hyperframes.heygen.com/schema/hyperframes.json', paths: { blocks: 'compositions', assets: 'assets' } }, null, 2) + '\n');
writeFileSync(join(dest, 'meta.json'), JSON.stringify({ id: slug, name: slug, width: 1920, height: 1080, fps: 60 }, null, 2) + '\n');
console.log(`Created video-projects/${slug}\n  cd video-projects/${slug}\n  npx hyperframes preview            (watch it in the browser)\n  npx hyperframes render -o renders/${slug}.mp4 --fps 60 --quality high`);
