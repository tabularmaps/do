# tabularmaps / Hokkaido 8-bit map

## Mission

tabularmaps is a dashboard-oriented project that favors compact overview and stable comparison over geographic fidelity.

The Hokkaido map compresses all 179 municipalities into a fixed 16 x 16 grid. Geography may be distorted when distortion improves overview, comparison, labeling, or dashboard use.

The project is not a conventional map, an electoral cartogram, a population-proportional cartogram, or a ranking of municipal worth.

## Current baseline

Use the following as the next working baseline:

- Grid: 16 x 16, exactly 256 cells.
- Sapporo: 4 x 4, exactly 16 cells.
- Regional anchors: 2 x 2.
- All other municipalities: 1 x 1.
- 1 x 2 and 2 x 1 are legal but unused in the baseline.
- Structural space: unnamed and intentionally retained.
- All 179 municipalities must occur exactly once.

Current cell budget:

```text
179 base municipality cells
+15 additional cells for Sapporo 4 x 4
+30 additional cells for ten 2 x 2 regional anchors
=224 occupied cells

256 - 224 = 32 structural or reserved cells
```

Do not spend the 32-cell reserve merely because it exists.

## Working regional anchors

The current ten 2 x 2 anchors are:

- Sapporo is separate at 4 x 4.
- Hakodate
- Otaru
- Asahikawa
- Wakkanai
- Kitami
- Tomakomai
- Muroran
- Obihiro
- Kushiro
- Nemuro

This list is a working hypothesis, not a permanent fact. Changing it requires an explicit comparison against the whole Hokkaido layout.

## Why the baseline excludes 1 x 2

Earlier prototypes used many 1 x 2 or 2 x 1 connectors. That produced three problems:

1. The intermediate class attracted too many plausible candidates.
2. Administrative status, population, transport function, and regional identity became mixed in one visual variable.
3. Orientation created unintended semantics and reduced packing freedom.

Therefore start with 4 x 4, 2 x 2, and 1 x 1 only.

A municipality may later be promoted from 1 x 1 to 1 x 2 or 2 x 1 only when the completed baseline exposes a concrete problem that the promotion solves.

Allowed reasons include:

- materially improving regional cluster continuity;
- preventing a municipality from appearing incorrectly subordinate to a neighboring anchor;
- expressing a genuine bridge between two otherwise separated clusters;
- solving a persistent labeling or packing problem;
- supporting a frequent dashboard comparison that cannot be handled by styling alone.

Insufficient reasons on their own include:

- being a city;
- hosting a subprefectural bureau;
- having a large land area;
- being well known;
- ranking relatively high on one population list.

Every promotion consumes one reserved cell and must state which problem it solves.

## Structural space

Structural space is part of the design grammar, not leftover failure.

Use it to:

- separate clusters that would otherwise be visually confused;
- preserve a legible regional seam;
- relieve pressure around large blocks;
- retain future promotion capacity;
- support titles, legends, or external connections when appropriate.

Do not name a structural cell after a bay, sea, or other feature unless the name is necessary and consistently defensible across the whole map. The former Ishikari Bay cell was rejected because naming a single water cell creates avoidable controversy and inconsistent expectations.

The compact feeling of tabularmaps remains important. Do not use blank cells merely to trace the outline of Hokkaido.

## Placement priorities

Apply priorities in this order:

1. Include all 179 municipalities exactly once.
2. Preserve the footprint class of each municipality.
3. Maintain a compact dashboard-like composition.
4. Keep broad north-south and east-west relationships recognizable.
5. Keep functional regional clusters readable.
6. Preserve selected high-value adjacencies.
7. Use structural space only where it performs identifiable work.
8. Optimize aesthetics after the above constraints are satisfied.

Exact municipal adjacency is not required.

## High-value layout observations

Treat the following as current design knowledge:

- Otaru should read as northwest or upper-left of Sapporo.
- The municipalities of the Ishikari Plain should form a plausible chain between Sapporo and Asahikawa, especially around Ebetsu, Iwamizawa, Takikawa, Fukagawa, and Asahikawa.
- Ebetsu and Eniwa have substantial dashboard presence, but the baseline keeps them at 1 x 1 until the complete layout demonstrates a need for promotion.
- Bureau seats do not automatically receive larger footprints. Urakawa, Esashi, Kutchan, and other seats can remain 1 x 1.
- Kitami, Abashiri, and Monbetsu must be judged as a system, not independently.
- Kushiro, Nemuro, and Nakashibetsu must be judged as a system, not independently.
- Tomakomai and Muroran are both retained as 2 x 2 in the current baseline. This decision must be assessed against the weight of southern Hokkaido as a whole.
- Funka Bay may emerge humorously and usefully from structural space, but no named water cell is required.

## Separate metadata from footprint

Do not encode every important property as area.

The following should normally be metadata or optional styling:

- subprefectural bureau seat;
- population rank;
- municipal class;
- port, airport, medical, or logistics function;
- border, island, or remote-area role;
- statistical value used by a dashboard.

Possible visual channels include border, icon, label, pattern, tooltip, or interactive state. Dashboard data should normally remain free to control fill color.

## Sapporo expansion

Sapporo occupies a stable 4 x 4 outer footprint.

The footprint may be expanded into the ten administrative wards for a detailed view. The ward layout is an independent subproblem and should be refined separately.

Current direction:

- favor population, economic activity, and administrative importance over land area;
- preserve approximate internal direction where practical;
- keep the outer 4 x 4 footprint invariant;
- collapse to a single Sapporo municipality in the all-Hokkaido view;
- expand to wards only when the dashboard requires ward-level data.

Do not treat Sapporo wards as municipalities. They are children of Sapporo in the data model.

Suggested structure:

```yaml
id: '01100'
name: 札幌市
footprint: [4, 4]
expandable: true
children:
  - 中央区
  - 北区
  - 東区
  - 白石区
  - 豊平区
  - 南区
  - 西区
  - 厚別区
  - 手稲区
  - 清田区
```

Claude should refine the internal 4 x 4 ward allocation later. Do not block the Hokkaido-wide work on that refinement.

## Optimization model

Treat layout generation as constrained optimization with human review.

Suggested hard constraints:

- fixed 16 x 16 grid;
- no overlap;
- no out-of-bounds footprint;
- each municipality appears once;
- Sapporo remains contiguous 4 x 4;
- each regional anchor remains contiguous 2 x 2.

Suggested soft objectives:

```text
maximize compact overview
maximize regional cluster readability
maximize selected adjacency preservation
maximize broad directional plausibility
maximize label readability
minimize misleading adjacency
minimize unnecessary structural space
minimize excessive geographic distortion
minimize unexplained footprint promotion
```

Do not optimize only Euclidean distance from municipal centroids. A visually persuasive tabular map requires regional topology, hierarchy, and dashboard behavior.

## Review method

For each new version:

1. Freeze the municipality footprint classes.
2. Generate or hand-place the large blocks first.
3. Place regional clusters.
4. Allocate 1 x 1 municipalities.
5. Inspect the whole map before considering any 1 x 2 promotion.
6. List every promotion or demotion and its reason.
7. Check that structural spaces perform identifiable work.
8. Validate cell count and municipality uniqueness programmatically.
9. Save the layout as data, not only as an image.
10. Keep the previous version for comparison.

## Handoff artifacts

The current handoff consists of:

- `tabularmaps_hokkaido_prototype_06_three_tiers.png`
- `hokkaido-v06-layout.json`
- `generate_hokkaido_v06.py`
- `tabularmaps_sapporo_4x4_wards_prototype_02_weighted.png`

Prototype 06 is a baseline for critique, not a final map. The layout script uses approximate regional target positions and an assignment optimizer. Claude should improve the objective function, especially cluster continuity and selected adjacencies, rather than polishing the image alone.

## Data sources

Authoritative source for the 179 municipalities and the 14 subprefectural bureau groupings:

- Hokkaido Government, “Municipalities by General Subprefectural Bureau and Subprefectural Bureau”
- https://www.pref.hokkaido.lg.jp/link/shichoson/
- https://www.pref.hokkaido.lg.jp/gyosei/shicho/index.html

Authoritative source for Sapporo administrative wards and ward statistics:

- City of Sapporo, ward administration overview
- City of Sapporo, population statistics
- https://www.city.sapporo.jp/shimin/shinko/kusei-suishin/gaiyo/index.html
- https://www.city.sapporo.jp/toukei/jinko/jinko.html

## Design checkpoint

The next task is not to add intermediate footprints.

The next task is to improve the 4 x 4 / 2 x 2 / 1 x 1 baseline until the whole map reveals where, if anywhere, a two-cell exception is genuinely necessary.
