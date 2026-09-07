---
name: tradingview-drawings
description: Reference for creating, reading and manipulating drawing tools / line tools on a TradingView chart (long/short positions, rays, trend lines, arrows, paths). Use when the user asks to draw levels, entries, zones or annotations on their TradingView chart — either in the TradingView Desktop app (via CDP port 9222 + internal model) or in a custom app using the Charting Library public API (createShape / createMultipointShape with shapes like "long_position", "short_position", "trend_line", "horz_ray").
---

# TradingView drawings: how to create & manipulate drawing tools

The user's setup is **TradingView Desktop** (Pepperstone/NAS100 chart, etc.). It exposes a
local debug port (CDP) on **http://localhost:9222**. Two ways to control drawings:

1. **Public Charting Library API** (`widget.activeChart().createMultipointShape(...)`) — the
   documented, supported surface. Only works if the charting-library widget instance is reachable.
2. **Internal model via CDP** (works on the Desktop app) — read/enumerate/load/create drawings
   through `window._exposed_chartWidgetCollection`. Verified working on TV Desktop 3.3.0
   (Chrome 140 / Electron) with the `ses` bundle.

Prefer reading the real chart first (never guess levels from memory) and confirming with the
user before drawing (drawing modifies their chart).

---

## 1. Connect to the TradingView Desktop chart over CDP

- Port: `9222`. Find the chart page: `GET http://localhost:9222/json` and pick the page whose
  `url` contains `tradingview.com/chart`.
- WebSocket CDP: connect to that page's `webSocketDebuggerUrl` with **Origin header suppressed**
  (Chrome rejects connections with a wrong origin unless
  `--remote-allow-origins=*` was set). In Python `websocket-client`:
  `websocket.create_connection(ws_url, suppress_origin=True)`. Then send
  `Runtime.evaluate` with `returnByValue:true` (and `awaitPromise:true` for async JS).

Access path (verified):

```js
// chart widget (the active chart tab)
const w  = window._exposed_chartWidgetCollection.activeChartWidget.value();
// symbol / interval
await w.getSymbol();                       // e.g. "PEPPERSTONE:NAS100"
w._resolutionWV.value();                    // e.g. "60" (1H)
// internal chart model
const m  = w._modelWV.value().m_model;
```

## 2. Enumerate existing drawings (read what the user marked)

```js
const m = window._exposed_chartWidgetCollection.activeChartWidget.value()._modelWV.value().m_model;
for (const pane of m._panes) {
  for (const s of pane.dataSources()) {
    const name = s.name ? s.name() : '';         // "Horizontal ray", "Arrow", "Path", "Position", ...
    const pts  = (s.points && s.points()) || []; // [{time, price}, ...]
    // s.id(), s.metaInfo(), s.properties() also available
  }
}
```

- Drawing tools appear as pane data-sources with `name()` like `Path`, `Arrow`, `Horizontal ray`,
  `Trend Line`, `Position`, etc. Internal overlays/alerts (`Sessions`, `AlertLabel`, ...) are not
  user drawings.
- `points()` returns `{ time, price }` anchors. Convert `time` (unix) to dates for the analysis.

## 3. Create a drawing

### 3a. Official Charting Library API (when the widget instance is available)

**Rule: pick the constructor method by how many coordinate points the shape needs:**

| method | for shapes with | example shapes |
|---|---|---|
| `createShape(point, options)` | exactly 1 point | `horizontal_line`, `vertical_line`, `arrow_up`, `arrow_down`, `text`, `price_tag` |
| `createMultipointShape(points, options)` | 2+ points | `trend_line`, `rectangle`, `triangle`, `fib_retracement`, `parallel_channel`, `prediction`, `long_position`, `short_position` |
| `createExecutionShape(options)` | immutable Buy/Sell execution markers (trade history) | returns `IExecutionLineAdapter` — cannot be moved by the user |
| `createAnchoredShape(position, options)` | viewport-anchored (screen %), ignores time/price scales | `anchored_text`, `anchored_note` |

**Coordinate structures (typed):**
- `PricedPoint` = `{ time: <unix>, price: <float> }` — standard, anchors to the price grid.
- `TimePoint` = `{ time: <unix> }` — time-axis-only tools (`vertical_line`).
- `StickedPoint` — logically snapped to a bar's OHLC values.
- `PositionPercents` = `{ x: 0-100, y: 0-100 }` — only for `createAnchoredShape`.

```js
const chart = widget.activeChart();   // IChartWidgetApi
const entityId = await chart.createMultipointShape(
  [ { time: t1, price: p1 }, { time: t2, price: p2 } ],
  {
    shape: 'long_position',   // see shape strings below
    overrides: { 'linetoolriskrewardlong.linecolor': '#26a69a' },
    lock: false,
    disableSave: true,
    disableUndo: true,
    disableSelection: false,
    zOrder: 'top',
  },
);
```

Shapes (from `CreateShapeOptions.shape` / `CreateMultipointShapeOptions.shape` union):
`'long_position'`, `'short_position'`, `'trend_line'`, `'horz_line'`, `'horz_ray'`,
`'vert_line'`, `'arrow'`, `'ray'`, `'path'`, `'prediction'`, `'fib_retracement'`,
`'text'`, `'anchored_text'`, `'arrowup'`, `'arrowdown'`, `'flag'`, `'price_tag'`, ...

Other official methods:
- `createShape(point, options)` — single-point drawings (e.g. `{shape:'vertical_line'}`).
- `createAnchoredShape({x,y}, options)` — percent-anchored drawings.
- `getAllShapes()` → `EntityInfo[]`; `getShapeById(id)` → `ILineDataSourceApi`.
- `removeEntity(id, {disableUndo})` — delete a drawing (works for any `create*` result).

`options` details:
- `shape`: exact tool id string (e.g. `"rectangle"`).
- `overrides`: key-value visual props layered over the theme defaults (e.g.
  `{ color: '#FF0000', linewidth: 2 }`).
- `ownerStudyId`: id of an active study — docks the drawing to a secondary pane
  (RSI/MACD) instead of the main price pane.

**Pattern — Order Block / FVG rectangle (multipoint):**
```js
widget.activeChart().createMultipointShape(
  [ { time: openBarTs, price: 15500 }, { time: futureTs, price: 15430.50 } ],
  { shape: "rectangle",
    overrides: { color: "#FF0000", backgroundColor: "rgba(255,0,0,0.2)", transparency: 20 } },
);
```

**Important (from docs):** for `long_position` / `short_position` the tip/label text is
generated automatically. **Do not set** `options.text` for these, or you get
`Error: Value is undefined`.

Override keys are prefixed: `linetoolriskrewardlong.*` (Risk/Reward Long = "Posición larga")
and `linetoolriskrewardshort.*` (Risk/Reward Short = "Posición corta"). Documented
`linetoolriskrewardlong.*` properties (defaults): `linecolor`(#808080), `linewidth`(1),
`textcolor`(#ffffff), `fontsize`(12), `borderColor`(#667b8b), `drawBorder`(false),
`fillBackground`(true), `fillLabelBackground`(true), `labelBackgroundColor`(#585858),
`alwaysShowStats`(false), `showPriceLabels`(true), `compact`(false), `currency`(NONE),
`lotSize`(1), `accountSize`(1000), `risk`(25), `riskDisplayMode`(percents),
`profitBackground`(rgba(8,153,129,0.2)), `profitBackgroundTransparency`(80),
`stopBackground`(rgba(242,54,69,0.2)), `stopBackgroundTransparency`(80).
Docs: https://www.tradingview.com/charting-library-docs/latest/api/interfaces/Charting_Library.RiskrewardlongLineToolOverrides/

### 3b. Internal model via CDP (TradingView Desktop) — verified

Names are the internal class names: `LineToolHorzRay`, `LineToolArrow`, `LineToolPath`,
`LineToolPosition`, `LineToolTrendLine`, `LineToolVertLine`, `LineToolRiskRewardLong`,
`LineToolRiskRewardShort`, `LineToolLongPosition`, ... NOT all are always loaded.

**The risk/reward position tools map to the toolbar "Posición larga"/"Posición corta":**
- Long Position  = `LineToolRiskRewardLong`  (locale "posición larga", module 575021)
- Short Position = `LineToolRiskRewardShort` (locale "posición corta", module 424181)
- `LineToolPosition` is the generic "Position" trading tool (buy/sell UI), not the directional arrow.

Lazy loading: tools are loaded on demand. Grab webpack require and load the tool first:

```js
window.webpackChunktradingview.push([['__probe__'], {}, (r) => { window.__req = r; }]); // capture require
const m695 = window.__req(695211);          // module exporting initLineTool / createLineTool
await m695.initLineTool('LineToolRiskRewardLong');   // load the tool module
```

Then create on the chart model:

```js
const m  = window._exposed_chartWidgetCollection.activeChartWidget.value()._modelWV.value().m_model;
const pane = m._panes[0];
const line = m.createLineTool({
  linetool: 'LineToolRiskRewardLong',       // or 'LineToolHorzRay', 'LineToolPath', ...
  point: { index: <barIndex>, price: <price> },  // first anchor
  pane,
  properties: null,                          // null => defaults
});
// add more anchors for multipoint tools:
line.addPoint && line.addPoint({ index: <i2>, price: <p2> });
m.fullUpdate && m.fullUpdate();
```

**CRITICAL gotcha — points need a bar `index`, not only `time`:** the internal
`_normalizePoint` does `this._model.timeScale().normalizeBarIndex(e.index)` and throws
`Value is null` when `e.index` is missing (or when the `time` is not aligned to a real bar,
e.g. `Date.now()/1000` past the last bar). Always pass `{ index, price }` where `index` is a
real bar index. Get the last bar index like this:

```js
const last = pane.dataSources()[0].bars().last();  // { index: 299, value: [time, o, h, l, c, v] }
const IDX = last.index;                            // bar-aligned index for anchoring "now"
```

`createLineTool` may still THROW `Value is null` in some flows even though the entity IS
created and usable — catch it, find the entity via `pane.dataSources()`, and continue.

### Horizontal Ray (S/R) — REGLA DE ANCLAJE (obligatoria para SMC)

**Un `horizontal_ray` (Soporte/Resistencia) DEBE anclarse en la vela que GENERÓ el nivel**
(la vela del swing que lo creó), no en la última vela ni en `Date.now()/1000`.

- El ancla `{ index, price }` apunta a la **vela del swing** (timestamp del high/low que
  definió el nivel). El rayo se proyecta hacia la derecha desde ese origen.
- Encontrar el índice de esa vela en los OHLCV extraídos (skill `tradingview-ohlcv`):
  localizar el bar cuyo `high` (resistencia) o `low` (soporte) == el precio del nivel, y usar
  su índice local `0..size-1`.
- **Ejemplo correcto** (soporte generado en la vela 286 @ 29645.3, anclado ahí):

```js
const m = window._exposed_chartWidgetCollection.activeChartWidget.value()._modelWV.value().m_model;
const pane = m._panes[0];
await window.__req(695211).initLineTool('LineToolHorzRay');
const ray = m.createLineTool({
  linetool: 'LineToolHorzRay',
  point: { index: 286, price: 29645.3 },  // <-- vela del swing que generó el nivel
  pane,
  properties: null,
});
const ch = ray.properties().childs();
ch.linecolor && ch.linecolor.setValue('#26a69a');   // soporte (verde) / resistencia '#ef5350'
m.fullUpdate && m.fullUpdate();
```

- **Qué NO hacer:** anclar el ray en el último bar (o `index: last.index`) solo porque la
  herramienta lo permita, o en `Date.now()/1000` (además de quedar fuera de pantalla, pierde
  la referencia al swing que lo originó). Si se usan niveles explícitos vía la tool MCP
  `draw_horizontal_rays` (que ancla en el último bar), **re-anclar después vía CDP** al índice
  de la vela generadora, o pasar el timestamp del swing para que el rayo nazca ahí.
- La nomenclatura del nombre del nivel se coloca en el child `text` (si el tool lo soporta):
  `ch.text.setValue('High 4H')`, `ch.text.setValue('Low 15')`, `ch.text.setValue('PDH')`, etc.

### Drawing a Long/Short Position (Risk/Reward) — internal structure (verified)

The `LineToolRiskRewardLong/Short` tools store **4 logical "points"** but only 2 are
real anchors (`pointsCount()` === 2):

| logical index | meaning | how to set |
|---|---|---|
| 0 | entry | the anchor passed to `createLineTool` |
| 1 | drag handle | forced to entry price (ignore) |
| 2 | **stop** | `line.properties().childs().stopPrice.setValue(x)` |
| 3 | **target** | `line.properties().childs().targetPrice.setValue(y)` |

So SL/TP are **properties, not points** — do not try to `setPoint(2/3)`. Configure like this:

```js
const ch = line.properties().childs();
ch.entryPrice.setValue(29550);                 // optional (anchor already sets it)
ch.stopPrice.setValue(29440);                  // stop
ch.targetPrice.setValue(30162);                // target
ch.linecolor.setValue('#26a69a');              // long = green
// for short: stopPrice=29950, targetPrice=29497, linecolor='#ef5350'

// verify:
line.priceAxisPoints();  // -> [{price:24800/*stop*/}, {price:29550/*entry*/}, {price:30162/*target*/}]
```

`points()` for these tools returns only the 2 anchors `[entry, handle]` (both at the entry
price) — use `priceAxisPoints()` or the `stopPrice`/`targetPrice` childs to confirm SL/TP.

Additional point editing: `model.changeLinePoint(line, index, point)`,
`model.startChangingLinetool`/`endChangingLinetool`, `line.setPoint(index, point)`.
Delete: `pane.removeDataSource(line, true)` or `line.destroy()`.

Webpack chunk catalog (chunk `53590` = loader module; `695211` = createLineTool module;
`45221`/`38801` = line-tool catalogs). If `createLineTool` throws
`Line tool X is not loaded`, call `initLineTool(X)` first. If it throws
`Cannot create unknown line tool: X`, the name is wrong — check the catalog.

---

## 4. Workflow / tips

1. **Read first**: pull symbol, interval, and existing drawings (path/levels the user drew) so the
   strategy matches their marks. Convert unix timestamps to dates.
2. **Confirm before drawing**: tell the user exactly which levels/tools you'll place. Drawing
   changes their chart permanently.
3. For entries use the **position tools** (`long_position`/`short_position` = "posición
   larga/corta"). For S/R zones use rays/lines (`horz_ray`/`horz_line`).
4. **S/R anchoring rule (SMC):** anchor every `horz_ray` at the **candle that generated the
   level** (the swing candle's bar index), projecting right — never at the last bar nor
   `Date.now()`. See the dedicated section above for the pattern.
5. **Avoid clutter — only relevant levels:** do NOT draw every liquidity pool as a ray. Keep a
   maximum of ~3 S/R rays that actually participate in the active/pending trade (e.g. the
   sell-side pools that trigger the entry + the already-swept context level). Remove redundant
   or far-away levels; contextual info (sweep consumed, day high) goes in the checklist text,
   not as extra rays. Re-verify ray count after resolution changes (rays can get lost/mis-anchored).
6. **Anchor visibility:** a Horizontal Ray anchored at a `time` beyond the last bar (or at
   `Date.now()/1000`) renders **off-screen and invisible**. Anchor zones at a bar index at or
   left of the visible range so the ray crosses the chart. Get the visible range with
   `m.timeScale().logicalRange()` (`{_left, _right}` are logical indices); anchoring at
   `index: 0` (first bar) is the safest way to make a level span the whole chart.
7. After drawing, verify by re-enumerating `pane.dataSources()` and checking the new tools'
   `name()` and `points()` were created. When iterating and deleting in the same loop, elements
   get skipped — collect references first, then remove.
8. If the CDP port is unreachable, TradingView Desktop may be closed — relaunch it
   (`open -a TradingView`) and wait for `http://localhost:9222/json` to respond.

## Reference URLs

- Drawings API guide: https://www.tradingview.com/charting-library-docs/latest/ui_elements/drawings/drawings-api
- IChartWidgetApi (createMultipointShape / createShape / getAllShapes / getShapeById / removeEntity):
  https://www.tradingview.com/charting-library-docs/latest/api/interfaces/Charting_Library.IChartWidgetApi/
- CreateMultipointShapeOptions (shape strings + overrides):
  https://www.tradingview.com/charting-library-docs/latest/api/interfaces/Charting_Library.CreateMultipointShapeOptions/
- RiskRewardLong overrides ("Posición larga"):
  https://www.tradingview.com/charting-library-docs/latest/api/interfaces/Charting_Library.RiskrewardlongLineToolOverrides/
- RiskRewardShort overrides ("Posición corta"):
  https://www.tradingview.com/charting-library-docs/latest/api/interfaces/Charting_Library.RiskrewardshortLineToolOverrides/