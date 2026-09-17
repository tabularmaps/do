#!/usr/bin/env python3
"""
配置データ (data/layout-*.json) の機械検証。

  - 16×16 = 256 セルが、市町村 224 + 構造余白 32 でちょうど埋まる
    (v08 以降: 構造余白 26 + 北方領土6村 6。既定の179表示では6村のセルも余白として扱う)
  - 179市町村 (+ status が northern_territories の6村) が全て1回ずつ現れ、コードが municipalities.json と一致する
  - 各市町村のフットプリントが階級 (札幌4×4 / 拠点2×2 / その他1×1) と一致する
  - 重なり・はみ出しがない
  - board (人間用の派生表現) が placements と一致する

使い方: python3 scripts/validate_layout.py data/layout-v07.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def validate(layout, munis):
    errors = []
    n = layout['grid'][0]
    by_code = {m['code']: m for m in munis}
    seen = {}
    grid = {}
    for p in layout['placements']:
        m = by_code.get(p['code'])
        if m is None:
            errors.append(f"未知のコード {p['code']} ({p['name']})"); continue
        if p['code'] in seen:
            errors.append(f"{p['name']} が重複"); continue
        seen[p['code']] = p
        if [p['w'], p['h']] != m['footprint']:
            errors.append(f"{p['name']} のフットプリント {p['w']}×{p['h']} が階級 {m['footprint']} と不一致")
        if p['name'] != m['name'] or p['bureau'] != m['bureau']:
            errors.append(f"{p['code']} の名前/振興局がマスターと不一致")
        if p.get('status', 'active') != m.get('status', 'active'):
            errors.append(f"{p['name']} の status がマスターと不一致")
        for yy in range(p['y'], p['y'] + p['h']):
            for xx in range(p['x'], p['x'] + p['w']):
                if not (0 <= xx < n and 0 <= yy < n):
                    errors.append(f"{p['name']} が範囲外 ({xx},{yy})"); continue
                if (xx, yy) in grid:
                    errors.append(f"({xx},{yy}) で {p['name']} と {grid[(xx, yy)]} が重なる")
                grid[(xx, yy)] = p['name']
    has_nt = any(p.get('status') == 'northern_territories' for p in layout['placements'])
    missing = [m['name'] for m in munis if m['code'] not in seen
               and (has_nt or m.get('status', 'active') == 'active')]
    if missing:
        errors.append(f"欠落: {missing}")
    active = sum(p.get('status', 'active') == 'active' for p in layout['placements'])
    if active != 179:
        errors.append(f"179市町村ではなく {active} 件")
    nt = [p for p in layout['placements'] if p.get('status') == 'northern_territories']
    if has_nt:
        if len(nt) != 6:
            errors.append(f"北方領土の村が {len(nt)} 件 (期待 6)")
        if any(p['x'] != 15 or p['w'] * p['h'] != 1 for p in nt):
            errors.append("北方領土の村は東端の列 (x=15) の 1×1 に限る (既定表示で凹みを作らないため)")
    structural = {tuple(c) for c in layout['structural_spaces']}
    if len(structural) + len(nt) != 32:
        errors.append(f"構造余白 {len(structural)} + 北方領土 {len(nt)} ≠ 32")
    for c in structural:
        if c in grid:
            errors.append(f"構造余白 {c} に {grid[c]} が置かれている")
    if len(grid) + len(structural) != n * n:
        errors.append(f"セル収支 {len(grid)} + {len(structural)} ≠ {n * n}")
    nt_cells = {(p['x'], p['y']) for p in nt}
    for key, include in (('board', False), ('board_all', True)):
        board = layout.get(key)
        if not board:
            continue
        for y in range(n):
            for x in range(n):
                want = grid.get((x, y), '')
                if not include and (x, y) in nt_cells:
                    want = ''
                if board[y][x] != want:
                    errors.append(f"{key}[{y}][{x}]={board[y][x]!r} ≠ placements {want!r}")
    return errors


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'data' / 'layout-v08.json'
    layout = json.loads(path.read_text('utf-8'))
    munis = json.loads((ROOT / 'data' / 'municipalities.json').read_text('utf-8'))['municipalities']
    errors = validate(layout, munis)
    if errors:
        print('\n'.join('NG ' + e for e in errors)); sys.exit(1)
    act = [p for p in layout['placements'] if p.get('status', 'active') == 'active']
    nt = [p for p in layout['placements'] if p.get('status') == 'northern_territories']
    occ = sum(p['w'] * p['h'] for p in act)
    st = len(layout['structural_spaces'])
    msg = f"OK {path.name}: 179市町村 占有 {occ} + 構造余白 {st}"
    if nt:
        msg += f" + 北方領土6村 {len(nt)} (既定表示では余白) = {occ + st + len(nt)}"
    else:
        msg += f" = {occ + st}"
    print(msg)


if __name__ == '__main__':
    main()
