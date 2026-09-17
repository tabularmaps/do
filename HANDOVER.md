# HANDOVER.md — 引き継ぎ (2026-09-18 時点)

`CLAUDE.md` (規約・現在形) と `DECISIONS.md` (D1〜D21、経緯) を一次情報とし、このファイルは「今どこまで進んでいて、
次に何をするか」だけを書く。

## 現在の状態

- 公開: https://tabularmaps.github.io/do/ (Open MCT ダッシュボード)、https://tabularmaps.github.io/do/preview.html (単体プレビュー)。
  GitHub Pages は main ブランチの `/docs`。CI (`.github/workflows/validate.yml`) は配置検証と `docs/data` の同期を確認し、直近まで成功。
- 配置: v08 (`data/layout-v08.json`)。179 市町村 + 根室振興局管内の 6 村 (北方領土) を保持し、地図としては 6 村を既定で描く。
  市町村数の集計は 179。前版 v07・v06 は `prototypes/` に保存。1×2 昇格は不要と確認済み (D12・D15)。
- データの裏取り: 市町村コード・名称は総務省一覧と一致 (`scripts/check_codes.py`、6 村込み)。札幌 10 区の配分は
  推計人口 (令和 8 年 9 月 1 日) の最大剰余法按分と一致 (D20)。
- 指標: 気象庁の気象警報・注意報 (`docs/jma-warnings.js`、r8 形式、5 分更新) が最初の実データ。デモ指標 (緯度・経度・乱数) も残す。
- 兄弟プロジェクト: tabularmaps/cldr (PR #1) とレイアウト JSON のキー名を共有。README で相互リンク済み。
- cafebabe (dwg7/cafebabe) へは Open MCT・コード照合・配置手法の教訓を 1 回寄稿済み (2026-09-17)。

## 表記上の約束 (公開物に関わるので必ず守る)

`CLAUDE.md`「北方領土の 6 村の扱い」を参照。要点: 政府資料の言い回しに限る (「市町村としての行政の実態がない」、
「歯舞群島は根室市の一部」)。「施政」を使わない。海のセルに名前を付けない。「179 市町村 + 6 村」のような並列表現を
しない (6 村は「根室振興局管内の 6 村」と北海道の内側に位置づける)。

## 次にやることの候補 (優先度順、未着手)

1. cafebabe への追加寄稿: 北方領土 6 村の扱い (政府の慣行の一覧 D16・D18、答弁書の言い回し、コード一覧・面積調・
   国土数値情報での収録、`includeNorthernTerritories` という命名の落とし穴 D17・D19) と、気象庁 JSON の旧形式が
   更新停止している件 (D21)。179 市町村を扱う他プロジェクト (sas0 など) に直接効く。
2. 役場座標の精密化: 国土地理院の地名検索 API (`https://msearch.gsi.go.jp/address-search/AddressSearch?q=<名前>`) で
   185 件を機械取得し、`data/municipalities.json` の概略座標を置き換える。配置を再生成して差分を確認し、D13 の
   「座標は概略値」を解消する。
3. GitHub Pages のキャッシュ対策: CSS/JS が 10 分キャッシュされ、更新直後に古い表示が残る。読み込み URL に版のクエリを付ける。
4. D13 の細部: 4 文字名の可読性、上川北部 (士別・名寄) の南北関係。
5. 指標の追加候補: 北海道の推計人口・国勢調査 (e-Stat)、河川・土砂災害情報。

## 作業の型 (再開時)

- 新版の作り方は `CLAUDE.md`「新しい版を作る手順」。生成 → 検証 → 描画 → `docs/data` へ複製 → CI。
- ブラウザ確認は `.claude/launch.json` の `docs` サーバー (python http.server 8765)。Open MCT のツリー展開は
  `.c-disclosure-triangle` (span) をクリックする。
- コミットの author は `18297+hfu@users.noreply.github.com`。コミットメッセージは日本語。
