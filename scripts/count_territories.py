#!/usr/bin/env python3
"""領土図 (design/territories-*.txt) のセル数を検算する。"""
import sys
from collections import Counter
NEED = dict(S=13, R=8, K=26, O=21, Z=24, I=7, P=16, G=23, B=17, H=7, T=22, U=11, N=8, W=14, E=7)
NEED['.'] = 32
# v08 以降: X = 北方領土の6村 (既定表示では余白として描くため、X + '.' = 32 を検算する)
NEED_X = 6
rows = [l.rstrip('\n') for l in open(sys.argv[1], encoding='utf-8') if l and not l.startswith('#')]
assert len(rows) == 16 and all(len(r) == 16 for r in rows), [len(r) for r in rows]
c = Counter(''.join(rows))
bad = False
if c.get('X', 0):
    NEED['.'] -= NEED_X
    NEED['X'] = NEED_X
for k in NEED:
    d = c.get(k, 0) - NEED[k]
    print(f'{k}: {c.get(k,0):3d} / {NEED[k]:3d}  {"" if d == 0 else f"({d:+d})"}')
    bad |= d != 0
print('total', sum(c.values()))
sys.exit(1 if bad else 0)
