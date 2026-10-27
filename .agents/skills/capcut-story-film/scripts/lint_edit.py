#!/usr/bin/env python3
"""Check plan/edit.json and print the shot list -> plan/edit.resolved.json

  python3 scripts/lint_edit.py <project>

Errors stop the build (gaps, unknown pictures or transitions, bad focus values). Warnings are craft notes (soft zooms,
long static holds, long dissolves). Fix errors; read every warning and fix it or accept it on purpose.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Project, save
from planfile import resolve_edit, lint

P = Project(sys.argv[1] if len(sys.argv) > 1 else '.')
R = resolve_edit(P)
err, warn = lint(P, R)
print(f"{'id':6s} {'picture':18s} {'start':>7s} {'dur':>5s}  {'zoom':>11s}  {'in':18s} note")
for s in R['shots']:
    z0, z1 = s['keys'][0][3], s['keys'][-1][3]
    print(f"{s['id']:6s} {s.get('plate', s['pic'])[:18]:18s} {s['t0']:7.2f} {s['t1'] - s['t0']:5.2f}  {z0:4.2f} -> {z1:4.2f}  {' '.join(map(str, s['in']))[:18]:18s} {s.get('note', '')[:60]}")
save(P.p('plan/edit.resolved.json'), {k: v for k, v in R.items() if k != 'plates'})
for w in warn: print('warning:', w)
for e in err: print('ERROR:', e)
if P.provisional: print('note: no voice yet, so word times are estimated from the storyboard; transcribe.py + align.py replace them')
print(f"{len(R['shots'])} shots, {len(err)} errors, {len(warn)} warnings")
sys.exit(1 if err else 0)
