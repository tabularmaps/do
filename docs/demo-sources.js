/*
 * demo-sources.js — ダッシュボードのデモ用の指標 (source) 定義。
 * 実運用では、ここを自分のデータ取得 (fetchValues / valuesUrl) に差し替える。
 *
 * 「役場の緯度・経度」は municipalities.json から作る本物の値で、地図の南北・東西の
 * 妥当性を色で検算できる (北ほど濃い / 東ほど濃い に見えれば配置は破綻していない)。
 */
(function () {
  'use strict';
  let munisPromise = null;
  function munis() {
    if (!munisPromise) munisPromise = fetch('./data/municipalities.json').then((r) => r.json()).then((d) => d.municipalities);
    return munisPromise;
  }
  function seriesFrom(label, unit, pick) {
    return munis().then((ms) => {
      const values = {};
      for (const m of ms) values[m.code] = pick(m);
      return { label, unit, values, asOf: '（役場所在地の概略値）' };
    });
  }
  // 決定的な擬似乱数 (時刻で変わる)。5秒ごとに更新して「動く」ダッシュボードの形を確かめる。
  function pseudo(seed) {
    let x = seed >>> 0;
    return () => { x = (x * 1664525 + 1013904223) >>> 0; return x / 4294967296; };
  }
  window.TABULARMAPS_DEMO_SOURCES = [
    { key: 'lat', name: 'デモ: 役場の緯度', fetchValues: () => seriesFrom('役場の緯度', '°N', (m) => m.lat) },
    { key: 'lon', name: 'デモ: 役場の経度', fetchValues: () => seriesFrom('役場の経度', '°E', (m) => m.lon) },
    {
      key: 'random', name: 'デモ: 乱数 (5秒更新)', refreshMs: 5000,
      fetchValues: () => munis().then((ms) => {
        const rnd = pseudo(Math.floor(Date.now() / 5000));
        const values = {};
        for (const m of ms) values[m.code] = Math.round(rnd() * 1000) / 10;
        return { label: '乱数', unit: '%', min: 0, max: 100, values, asOf: new Date().toLocaleTimeString('ja-JP') };
      })
    }
  ];
})();
