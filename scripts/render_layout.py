#!/usr/bin/env python3
"""
配置データ (data/layout-*.json) を PNG に描く (レビュー用)。

使い方: python3 scripts/render_layout.py data/layout-v07.json [出力.png] [--title "..."]
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent

COLORS = {'宗谷': '#8cc5e3', '留萌': '#7db7d8', '上川': '#87c99b', 'オホーツク': '#6cc6c1', '空知': '#e6c86a',
          '石狩': '#e99562', '後志': '#c9a5d6', '胆振': '#e28b78', '日高': '#e7a3a8', '十勝': '#b6d36f',
          '釧路': '#73b5b2', '根室': '#67a7a5', '渡島': '#d79b72', '檜山': '#b98b75'}
FONT_CANDIDATES = [
    '/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc',
    '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',
    '/usr/share/fonts/truetype/noto/NotoSansCJK-VF.ttf.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
]


def font(size):
    for fp in FONT_CANDIDATES:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size, index=0)
            except OSError:
                continue
    return ImageFont.load_default()


def render(layout, out, title=None, subtitle=None):
    n = layout['grid'][0]
    S, M, TOP = 90, 60, 170
    im = Image.new('RGB', (M * 2 + n * S, TOP + n * S + 150), 'white')
    d = ImageDraw.Draw(im)
    title = title or f"tabularmaps 北海道 {layout['version']}"
    subtitle = subtitle or '16×16 全道・三階級 (札幌4×4、広域拠点10か所2×2、その他168市町村1×1)'
    d.text((M, 25), title, font=font(42), fill='#172033')
    d.text((M, 88), subtitle, font=font(22), fill='#64748b')
    for i in range(n + 1):
        d.line((M + i * S, TOP, M + i * S, TOP + n * S), fill='#e5eaf0')
        d.line((M, TOP + i * S, M + n * S, TOP + i * S), fill='#e5eaf0')
    for x, y in layout['structural_spaces']:
        x0, y0 = M + x * S + 3, TOP + y * S + 3
        d.rounded_rectangle((x0, y0, x0 + S - 6, y0 + S - 6), 5, fill='#f7fafc', outline='#dfe6ec', width=2)
    for p in layout['placements']:
        x0, y0 = M + p['x'] * S + 3, TOP + p['y'] * S + 3
        x1, y1 = M + (p['x'] + p['w']) * S - 3, TOP + (p['y'] + p['h']) * S - 3
        big = p['w'] * p['h'] > 1
        fill = COLORS[p['bureau']]
        if big:
            outline, width, fsize = '#334155', 4, 26 if p['w'] == 4 else 23
        else:
            outline, width, fsize = 'white', 2, 15
        d.rounded_rectangle((x0, y0, x1, y1), 8 if big else 5, fill=fill, outline=outline, width=width)
        lab = p['name']
        f = font(fsize if len(lab) <= 4 else 13)
        bb = d.textbbox((0, 0), lab, font=f)
        d.text(((x0 + x1 - (bb[2] - bb[0])) / 2 - bb[0], (y0 + y1 - (bb[3] - bb[1])) / 2 - bb[1]), lab, font=f, fill='#172033')
    met = layout.get('generator', {}).get('metrics', {})
    foot = f"セル収支: 16 + 40 + 168 + 32 = 256。構造余白は無名。"
    if met:
        foot += f"  地理的隣接 {met['edges']} 組のうち隣接保存 {met['adjacent_kept']}・1セル以内 {met['within_1']}。"
    d.text((M, TOP + n * S + 25), foot, font=font(19), fill='#52606d')
    # 凡例
    lx, ly = M, TOP + n * S + 70
    for i, (b, c) in enumerate(COLORS.items()):
        x = lx + (i % 7) * 160; y = ly + (i // 7) * 30
        d.rectangle((x, y, x + 20, y + 20), fill=c)
        d.text((x + 28, y - 2), b, font=font(17), fill='#52606d')
    im.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('layout', nargs='?', default=str(ROOT / 'data' / 'layout-v07.json'))
    ap.add_argument('out', nargs='?', default=None)
    ap.add_argument('--title', default=None)
    ap.add_argument('--subtitle', default=None)
    a = ap.parse_args()
    layout = json.loads(Path(a.layout).read_text('utf-8'))
    out = a.out or str(ROOT / 'prototypes' / f"tabularmaps_hokkaido_{layout['version']}.png")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    print('wrote', render(layout, out, a.title, a.subtitle))


if __name__ == '__main__':
    main()
