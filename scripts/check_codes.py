#!/usr/bin/env python3
"""
市町村マスター (data/municipalities.json) と札幌区 (data/sapporo-wards.json) のコード・正式名称を、
総務省「都道府県コード並びに市区町村コード」の Excel と突き合わせる。openpyxl 不要 (zip + 正規表現)。

使い方: python3 scripts/check_codes.py [--xlsx path]   (省略時は総務省サイトから取得)
一覧の掲載ページ: https://www.soumu.go.jp/denshijiti/code.html
"""
import argparse
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE_PAGE = 'https://www.soumu.go.jp/denshijiti/code.html'
# 北方領土の6村は法令上のコードを持つが、行政が行われておらず「179市町村」に含めない。
NORTHERN_TERRITORIES = {'01695', '01696', '01697', '01698', '01699', '01700'}


def fetch_latest_xlsx():
    html = urllib.request.urlopen(urllib.request.Request(CODE_PAGE, headers={'User-Agent': 'Mozilla/5.0'})).read().decode('shift_jis', 'replace')
    links = sorted(set(re.findall(r'href="(/main_content/\d+\.xlsx)"', html)))
    if not links:
        sys.exit('Excel のリンクが見つからない: ' + CODE_PAGE)
    # 複数ある場合、北海道の市町村行を最も多く含むものを採用する
    best = None
    for l in links:
        data = urllib.request.urlopen(urllib.request.Request('https://www.soumu.go.jp' + l, headers={'User-Agent': 'Mozilla/5.0'})).read()
        p = Path('/tmp') / Path(l).name
        p.write_bytes(data)
        n = len([k for k in read_codes(p) if k.startswith('01')])
        if best is None or n > best[0]:
            best = (n, p)
    return best[1]


def read_codes(path):
    z = zipfile.ZipFile(path)
    ss = []
    x = z.read('xl/sharedStrings.xml').decode('utf-8')
    for si in re.findall(r'<si>(.*?)</si>', x, re.S):
        ss.append(''.join(re.findall(r'<t[^>]*>(.*?)</t>', si, re.S)))
    found = {}
    for sheet in [n for n in z.namelist() if n.startswith('xl/worksheets/sheet')]:
        x = z.read(sheet).decode('utf-8')
        for row in re.findall(r'<row[^>]*>(.*?)</row>', x, re.S):
            cells = {}
            for ref, typ, inner in re.findall(r'<c r="([A-Z]+)\d+"(?:[^>]*t="(\w+)")?[^>]*>(.*?)</c>', row, re.S):
                v = re.search(r'<v>(.*?)</v>', inner)
                if v:
                    v = v.group(1)
                    cells[ref] = ss[int(v)] if typ == 's' else v
            a = str(cells.get('A', ''))
            if len(a) == 6 and a.isdigit() and cells.get('C'):
                found[a[:5]] = cells['C']   # 6桁目は検査数字
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--xlsx', default=None)
    a = ap.parse_args()
    path = Path(a.xlsx) if a.xlsx else fetch_latest_xlsx()
    official = read_codes(path)
    munis = json.loads((ROOT / 'data' / 'municipalities.json').read_text('utf-8'))['municipalities']
    wards = json.loads((ROOT / 'data' / 'sapporo-wards.json').read_text('utf-8'))['wards']
    errors = []
    mine = {m['code']: m for m in munis}
    for code, name in official.items():
        if not code.startswith('01') or code == '01000':
            continue
        if code[:3] == '011' and code != '01100':
            continue  # 札幌市の区は下で別に照合
        if code in NORTHERN_TERRITORIES:
            continue
        if code not in mine:
            errors.append(f'マスターに無い: {code} {name}')
        elif mine[code]['fullName'] != name:
            errors.append(f'名称不一致: {code} {mine[code]["fullName"]} ≠ {name}')
    for code in mine:
        if code not in official:
            errors.append(f'一覧に無い: {code} {mine[code]["fullName"]}')
    for w in wards:
        off = official.get(w['code'])
        if off != '札幌市' + w['name']:
            errors.append(f'区の不一致: {w["code"]} {w["name"]} ≠ {off}')
    if errors:
        print('\n'.join('NG ' + e for e in errors)); sys.exit(1)
    print(f'OK {path.name}: 179市町村と札幌10区のコード・名称が総務省一覧と一致 (北方領土6村は対象外)')


if __name__ == '__main__':
    main()
