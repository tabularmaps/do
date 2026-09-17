#!/usr/bin/env python3
"""
配置データから tabularmaps/8bit 互換の board.csv (16行×16列、セルは市町村名、空白は空文字) を出す。
使い方: python3 scripts/export_board_csv.py data/layout-v07.json data/board.csv
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'data' / 'layout-v07.json'
dst = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'data' / 'board.csv'
layout = json.loads(src.read_text('utf-8'))
with dst.open('w', newline='', encoding='utf-8') as f:
    csv.writer(f).writerows(layout['board'])
print('wrote', dst)
