#!/usr/bin/env node
// npm run sync   AGENTS.md is the one source of the assistant rules: CLAUDE.md (Claude Code) and GEMINI.md (Gemini CLI,
// Antigravity) are copies of it. Skills live in .claude/skills/ and are mirrored to .agents/skills/ (Codex).
import { readFileSync, writeFileSync, rmSync, cpSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const src = readFileSync(join(root, 'AGENTS.md'), 'utf8');
for (const f of ['CLAUDE.md', 'GEMINI.md']) writeFileSync(join(root, f), `<!-- Generated from AGENTS.md by npm run sync. Edit AGENTS.md, not this file. -->\n` + src);
if (existsSync(join(root, '.agents/skills'))) rmSync(join(root, '.agents/skills'), { recursive: true });
cpSync(join(root, '.claude/skills'), join(root, '.agents/skills'), { recursive: true });
console.log('  ok   CLAUDE.md, GEMINI.md and .agents/skills synced from AGENTS.md and .claude/skills');
