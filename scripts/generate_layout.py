#!/usr/bin/env python3
"""
北海道 tabular map (16×16) の配置生成器。

設計思想: 「どの振興局がどのセル群を占めるか」(領土図) は人が描き、
「領土の中で市町村をどう並べるか」だけを最適化器が解く。
振興局の継ぎ目や構造余白の位置は設計判断であり、目的関数の副産物にしない。

  入力 1. design/territories-<version>.txt — 16行×16文字の領土図 (人手)
  入力 2. data/municipalities.json         — 179市町村 + 北方領土6村 (振興局・区分・概略座標・status)
  段階 A. 2×2拠点を ANCHOR_HINTS の位置に置く (自振興局の領土内であることを検証)
  段階 B. 各振興局の1×1市町村を、領土内の残りセルへ地理座標で初期割当
  段階 C. 焼きなまし: 同じ振興局の1×1セル同士の入れ替えで
          (a) 地理的隣接 (Delaunay) の保存  (b) 領土内での方位妥当性 を改善

出力: data/layout-<version>.json。画像は scripts/render_layout.py が作る。
使い方: python3 scripts/generate_layout.py [--version v08] [--seed 1] [--iters 200000]
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial import Delaunay

ROOT = Path(__file__).resolve().parent.parent
N = 16

# ----------------------------------------------------------------------------
# 設計パラメータ
# ----------------------------------------------------------------------------

LETTER = {'S': '宗谷', 'R': '留萌', 'K': '上川', 'O': 'オホーツク', 'Z': '空知', 'I': '石狩',
          'P': '石狩', 'G': '後志', 'B': '胆振', 'H': '日高', 'T': '十勝', 'U': '釧路',
          'N': '根室', 'W': '渡島', 'E': '檜山',
          'X': '北方領土'}   # 北方領土の6村 (根室振興局管内、既定表示では余白として描く)

# 大ブロックの左上セル。すべて設計判断 (理由は DECISIONS.md)。
ANCHOR_HINTS = {
    '札幌': (2, 7),
    '小樽': (0, 5),    # 札幌の左上 (北西)。積丹半島の付け根
    '稚内': (4, 0),    # 最北。西に礼文・利尻、東に猿払・浜頓別
    '旭川': (8, 3),    # 上川の中心。北西に鷹栖、西に深川 (空知)
    '北見': (12, 3),   # オホーツクの中心。北に紋別系、東に網走系、南に置戸・訓子府
    '帯広': (10, 10),  # 十勝平野の中心
    '釧路': (12, 11),  # 十勝の東、根室の南西。東に釧路町・厚岸・浜中
    '根室': (14, 9),   # 南東端。北に別海・中標津・標津・羅臼
    '室蘭': (3, 12),   # 噴火湾東岸。北西に伊達・洞爺湖、東に登別・白老をはさんで苫小牧
    '苫小牧': (6, 11), # 千歳の南、札幌の南東
    '函館': (7, 14),   # 渡島帯の東端 = 半島の南東。西に北斗・七飯、松前は帯の西端
}

# 1×1のピン留め (設計判断で位置を固定する市町村)。最適化の対象外。
PINS = {
    '江別': (6, 7),    # 札幌の真東。石狩平野の札幌→岩見沢→旭川の鎖の起点
    '岩見沢': (7, 7),  # 江別の真東。空知の中心都市
    '中川': (8, 0),    # 上川最北 (音威子府より北)
    '平取': (8, 12),   # むかわの南、日高の入口
    '日高': (9, 13),   # 新冠の西
    '白糠': (12, 10),  # 釧路の北西 (釧路町と取り違えない)
    '釧路町': (14, 12),# 釧路の真東
    '壮瞥': (5, 11),   # 室蘭の北・喜茂別の南 (登別・白老の列の北端)
    '倶知安': (1, 7),  # 赤井川・小樽に接する後志の中心。京極はその南
    '京極': (1, 8),
    '音更': (11, 9),   # 帯広の真北 (双子都市)
    '浦幌': (12, 13),  # 十勝の南東端。白糠(釧路)に接する
    # 渡島は半島を2列の帯に展開する: 上段=噴火湾沿い (長万部→八雲→森→鹿部→七飯→函館)、
    # 下段=津軽海峡沿い (松前→福島→知内→木古内→北斗→函館)。上段と松前を固定し、下段は隣接から決まる。
    '長万部': (2, 14), '八雲': (3, 14), '森': (4, 14), '鹿部': (5, 14), '七飯': (6, 14),
    '松前': (2, 15), '知内': (4, 15),
    # オホーツク東岸 (v08): 網走→小清水→斜里→清里 を x=14 の列に北から並べ、羅臼 (根室) へつなぐ。
    # 領土が幅広の塊になったため、正規化座標だけでは網走が最北端に置かれてしまう。
    '網走': (14, 2), '小清水': (14, 3), '斜里': (14, 4), '清里': (14, 5),
    '置戸': (12, 5),   # 北見の南西 (訓子府と並ぶ)。領土の形の都合で北側に置かれるのを防ぐ
}

# 北方領土の6村 (v08 以降)。東端の列に北から 択捉 (蘂取・紗那・留別)、国後 (留夜別・泊)、色丹 の順。
# (15,3) (15,6) は海峡にあたる余白。既定の179表示ではこの列全体が海として読めるように、6村は x=15 だけに置く。
# 6村の name は正式名称 (「泊村」等) のまま扱う: 後志の泊村 (01403) と同名のため、表示上も区別する。
NT_PINS = {
    '蘂取村': (15, 0), '紗那村': (15, 1), '留別村': (15, 2),
    '留夜別村': (15, 4), '泊村': (15, 5),
    '色丹村': (15, 7),
}

# 地理座標 → グリッド座標 (方位妥当性の目標にのみ使う)。
# 経度2.586セル/度・緯度3.75セル/度で、北緯43.5°付近ではほぼ等方 (1セル ≈ 30km)。
def geo_to_grid(lon, lat):
    return (lon - 139.8) * 2.586 + 0.5, (45.42 - lat) * 3.75 + 0.5

W_GEO = 0.6       # 領土内正規化位置からの距離² (方位妥当性)
W_NEIGHBOR = 1.0  # 地理的隣接ペアのグリッド上のギャップ (隣接保存)
NEIGHBOR_KM = 40.0        # これ以下は無条件に隣接
NEIGHBOR_KM_SPARSE = 85.0 # これ以下なら、どちらかの端点の3近傍に入る場合だけ隣接 (道東・道北向け)


# ----------------------------------------------------------------------------
def load_munis():
    data = json.loads((ROOT / 'data' / 'municipalities.json').read_text('utf-8'))
    return data['municipalities']


def territory_key(m):
    """領土図上での所属: 179市町村は振興局、北方領土の6村は 'X' の領土。"""
    return '北方領土' if m.get('status') == 'northern_territories' else m['bureau']


def load_territories(version):
    path = ROOT / 'design' / f'territories-{version}.txt'
    rows = [l.rstrip('\n') for l in path.read_text('utf-8').splitlines() if l and not l.startswith('#')]
    assert len(rows) == N and all(len(r) == N for r in rows), path
    terr = {}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            terr[(x, y)] = None if ch == '.' else LETTER[ch]
    return terr


def build_neighbor_graph(munis):
    """役場座標のDelaunay三角分割から地理的隣接グラフを作る。"""
    pts = np.array([[(m['lon'] - 139.8) * 80.5, (m['lat'] - 45.42) * 111.0] for m in munis])
    tri = Delaunay(pts)
    cand = {}
    for s in tri.simplices:
        for a in range(3):
            for b in range(a + 1, 3):
                i, j = sorted((s[a], s[b]))
                cand[(i, j)] = float(np.hypot(*(pts[i] - pts[j])))
    nearest = {}
    for (i, j), d in cand.items():
        nearest.setdefault(i, []).append((d, j)); nearest.setdefault(j, []).append((d, i))
    top3 = {i: {j for _, j in sorted(v)[:3]} for i, v in nearest.items()}
    return sorted(e for e, d in cand.items()
                  if d <= NEIGHBOR_KM or (d <= NEIGHBOR_KM_SPARSE and (e[1] in top3[e[0]] or e[0] in top3[e[1]])))


def rect_gap(ax, ay, aw, ah, bx, by, bw, bh):
    dx = max(0, bx - (ax + aw), ax - (bx + bw))
    dy = max(0, by - (ay + ah), ay - (by + bh))
    return dx + dy


# ----------------------------------------------------------------------------
def place_blocks(munis, terr):
    blocks = {}
    occupied = set()
    for m in munis:
        w, h = m['footprint']
        if (w, h) == (1, 1):
            continue
        x, y = ANCHOR_HINTS[m['name']]
        cells = {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}
        bad = [c for c in cells if terr.get(c) != m['bureau']]
        assert not bad, f"{m['name']} の {bad} が {m['bureau']} の領土ではない"
        assert not (cells & occupied), m['name']
        occupied |= cells
        blocks[m['name']] = (x, y, w, h)
    return blocks, occupied


def initial_assignment(munis, terr, occupied):
    """振興局ごとに、地理bboxを領土bboxへ正規化した位置で1×1を割り当てる。"""
    cells, targets = {}, {}
    by_name = {m['name']: m for m in munis}
    pins = dict(PINS)
    if any(t == '北方領土' for t in terr.values()):
        pins.update(NT_PINS)
    for name, c in pins.items():
        assert terr.get(c) == territory_key(by_name[name]) and c not in occupied, (name, c)
        cells[name] = c; occupied = occupied | {c}
        targets[name] = c
    for b in sorted({territory_key(m) for m in munis}):
        ms = [m for m in munis if territory_key(m) == b and m['footprint'] == [1, 1] and m['name'] not in pins]
        free = sorted(c for c, t in terr.items() if t == b and c not in occupied)
        assert len(free) == len(ms), (b, len(free), len(ms))
        if not ms:
            continue  # 全員がピン留め (北方領土の6村など)
        lons = [m['lon'] for m in ms]; lats = [m['lat'] for m in ms]
        xs = [c[0] for c in free]; ys = [c[1] for c in free]

        def norm(v, lo, hi, a, b_):
            return a if hi == lo else a + (v - lo) / (hi - lo) * (b_ - a)
        cost = []
        for m in ms:
            nx = norm(m['lon'], min(lons), max(lons), min(xs), max(xs))
            ny = norm(-m['lat'], -max(lats), -min(lats), min(ys), max(ys))
            gx, gy = geo_to_grid(m['lon'], m['lat'])
            # 領土内の正規化位置 (歪みを織り込んだ目標) と全道の地理位置の混合
            targets[m['name']] = (0.7 * nx + 0.3 * (gx - 0.5), 0.7 * ny + 0.3 * (gy - 0.5))
            tx, ty = targets[m['name']]
            cost.append([(x - tx) ** 2 + (y - ty) ** 2 for (x, y) in free])
        ri, ci = linear_sum_assignment(np.array(cost))
        for i, j in zip(ri, ci):
            cells[ms[i]['name']] = free[j]
    return cells, targets


class Annealer:
    """同じ振興局の1×1セル同士の入れ替えによる局所改善。"""

    def __init__(self, munis, blocks, cells, edges, targets, rng):
        self.rng = rng
        self.munis = munis
        self.bureau = [territory_key(m) for m in munis]
        self.target = [targets.get(m['name']) for m in munis]
        self.rect = {}
        idx = {m['name']: i for i, m in enumerate(munis)}
        for name, (x, y, w, h) in blocks.items():
            self.rect[idx[name]] = (x, y, w, h)
        for name, (x, y) in cells.items():
            self.rect[idx[name]] = (x, y, 1, 1)
        self.adj = {i: [] for i in range(len(munis))}
        for i, j in edges:
            self.adj[i].append(j); self.adj[j].append(i)
        self.grid = {}
        for i, (x, y, w, h) in self.rect.items():
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    self.grid[(xx, yy)] = i
        self.movable = {}
        pinned = set(PINS) | set(NT_PINS)
        for c, i in self.grid.items():
            if self.rect[i][2:] == (1, 1) and munis[i]['name'] not in pinned:
                self.movable.setdefault(self.bureau[i], []).append(c)
        self.bureaus = [b for b, cs in self.movable.items() if len(cs) >= 2]

    def item_energy(self, item, cell):
        x, y = cell
        tx, ty = self.target[item]
        e = W_GEO * ((x - tx) ** 2 + (y - ty) ** 2)
        for j in self.adj[item]:
            e += W_NEIGHBOR * rect_gap(x, y, 1, 1, *self.rect[j])
        return e

    def local(self, p, q):
        return self.item_energy(self.grid[p], p) + self.item_energy(self.grid[q], q)

    def total(self):
        e = 0.0
        for c, i in self.grid.items():
            if self.rect[i][2:] == (1, 1):
                e += self.item_energy(i, c)
        return e

    def swap(self, p, q):
        a, b = self.grid[p], self.grid[q]
        self.grid[p], self.grid[q] = b, a
        self.rect[a] = (q[0], q[1], 1, 1)
        self.rect[b] = (p[0], p[1], 1, 1)

    def run(self, iters, t0=2.0, t1=0.02):
        rng = self.rng
        cur = self.total(); best = cur; best_state = dict(self.grid)
        for k in range(iters):
            t = t0 * (t1 / t0) ** (k / iters)
            cs = self.movable[rng.choice(self.bureaus)]
            p, q = rng.sample(cs, 2)
            before = self.local(p, q)
            self.swap(p, q)
            d = self.local(p, q) - before
            if d <= 0 or rng.random() < math.exp(-d / t):
                cur += d
                if cur < best - 1e-9:
                    best = cur; best_state = dict(self.grid)
            else:
                self.swap(p, q)
        self.grid = best_state
        for c, i in self.grid.items():
            if self.rect[i][2:] == (1, 1):
                self.rect[i] = (c[0], c[1], 1, 1)
        return best

    def export(self):
        return {self.munis[i]['name']: c for c, i in self.grid.items() if self.rect[i][2:] == (1, 1)}


# ----------------------------------------------------------------------------
def report(munis, blocks, cells, edges):
    """隣接保存率・振興局まとまりの簡易指標。"""
    idx = {m['name']: i for i, m in enumerate(munis)}
    rect = {}
    for n, (x, y, w, h) in blocks.items():
        rect[idx[n]] = (x, y, w, h)
    for n, (x, y) in cells.items():
        rect[idx[n]] = (x, y, 1, 1)
    gaps = [rect_gap(*rect[i], *rect[j]) for i, j in edges]
    grid = {}
    for i, (x, y, w, h) in rect.items():
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                grid[(xx, yy)] = munis[i]['bureau']
    same = diff = 0
    for (x, y), b in grid.items():
        for n in ((x + 1, y), (x, y + 1)):
            if n in grid:
                if grid[n] == b: same += 1
                else: diff += 1
    return {'edges': len(edges), 'adjacent_kept': sum(g == 0 for g in gaps),
            'within_1': sum(g <= 1 for g in gaps), 'mean_gap': round(sum(gaps) / len(gaps), 3),
            'region_boundary_edges': diff, 'region_internal_edges': same}


def to_layout(version, munis, blocks, cells, structural, metrics, seed):
    by_name = {m['name']: m for m in munis}
    placements = []
    for name, (x, y, w, h) in blocks.items():
        m = by_name[name]
        placements.append({'code': m['code'], 'name': name, 'bureau': m['bureau'], 'status': m.get('status', 'active'),
                           'x': x, 'y': y, 'w': w, 'h': h})
    for name, (x, y) in cells.items():
        m = by_name[name]
        placements.append({'code': m['code'], 'name': name, 'bureau': m['bureau'], 'status': m.get('status', 'active'),
                           'x': x, 'y': y, 'w': 1, 'h': 1})
    placements.sort(key=lambda p: p['code'])
    def make_board(include_nt):
        board = [[''] * N for _ in range(N)]
        for p in placements:
            if p['status'] != 'active' and not include_nt:
                continue
            for yy in range(p['y'], p['y'] + p['h']):
                for xx in range(p['x'], p['x'] + p['w']):
                    board[yy][xx] = p['name']
        return board
    board = make_board(False)
    nt = [p for p in placements if p['status'] == 'northern_territories']
    counts = {'active': sum(p['status'] == 'active' for p in placements), 'northern_territories': len(nt)}
    return {
        'version': version,
        'grid': [N, N],
        'classes': {'札幌': [4, 4], 'regional_anchor': [2, 2], 'municipality': [1, 1]},
        'regional_anchors': [n for n, (x, y, w, h) in blocks.items() if (w, h) == (2, 2)],
        'generator': {'script': 'scripts/generate_layout.py', 'territories': f'design/territories-{version}.txt',
                      'seed': seed, 'metrics': metrics},
        'counts': counts,
        'placements': placements,
        'structural_spaces': [list(c) for c in structural],
        'board': board,
        **({'northern_territories': {
                'note': '根室振興局管内の6村。現在は日本の施政下になく村としての行政は行われていない。'
                        '既定表示 (179市町村) では構造余白として描き、明示的に含める時だけ市町村として描く。',
                'cells': [[p['x'], p['y']] for p in nt],
            }, 'board_all': make_board(True)} if nt else {}),
    }


def print_board(board):
    for row in board:
        print(' '.join(f'{(c or "·"):　<4}' for c in row))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--version', default='v08')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--iters', type=int, default=200000)
    ap.add_argument('--no-anneal', action='store_true')
    ap.add_argument('--out', default=None)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    munis = load_munis()
    terr = load_territories(args.version)
    if not any(t == '北方領土' for t in terr.values()):
        # 領土図に X が無い版 (v07 以前) は 179 市町村だけを扱う
        munis = [m for m in munis if m.get('status', 'active') == 'active']
    edges = build_neighbor_graph(munis)
    blocks, occupied = place_blocks(munis, terr)
    cells, targets = initial_assignment(munis, terr, occupied)
    structural = sorted(c for c, t in terr.items() if t is None)
    nt_cells = sorted(c for c, t in terr.items() if t == '北方領土')
    assert len(structural) + len(nt_cells) == 32, (len(structural), len(nt_cells))
    print('initial metrics:', report(munis, blocks, cells, edges), file=sys.stderr)
    if not args.no_anneal:
        ann = Annealer(munis, blocks, cells, edges, targets, rng)
        e0 = ann.total(); e1 = ann.run(args.iters)
        cells = ann.export()
        print(f'anneal energy {e0:.1f} -> {e1:.1f}', file=sys.stderr)
    metrics = report(munis, blocks, cells, edges)
    print('final metrics:', metrics, file=sys.stderr)
    layout = to_layout(args.version, munis, blocks, cells, structural, metrics, args.seed)
    out = Path(args.out) if args.out else ROOT / 'data' / f'layout-{args.version}.json'
    out.write_text(json.dumps(layout, ensure_ascii=False, indent=1), 'utf-8')
    print_board(layout['board'])
    print('wrote', out, file=sys.stderr)


if __name__ == '__main__':
    main()
