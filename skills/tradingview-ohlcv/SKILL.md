---
name: tradingview-ohlcv
description: How to extract OHLCV candles from the active TradingView Desktop chart (any timeframe: 4H/1H/15M/5M) via the CDP debug port when the tradingview-mcp has no history endpoint for the symbol (e.g. NAS100/Pepperstone CFD). Use when the user asks for OHLCV data, historical bars or candles of the chart symbol at multiple resolutions.
---

# TradingView OHLCV extraction (via CDP)

Applies to symbols the `tradingview-mcp` can't serve (CFDs like PEPPERSTONE:NAS100 are not in
the scanner; `yahoo_price("NAS100")` 404s). The chart data pipeline itself can serve any
resolution, so read it straight from the chart model over CDP.

**Prereq:** TradingView Desktop running in debug mode (CDP on 9222). If not, use the
`tradingview-debug-launch` skill first.

## Flow (verified 2026-08-10, TV Desktop 3.3.0)

1. Connect to the chart page's `webSocketDebuggerUrl` with `suppress_origin=True`.
2. Read the **current resolution** (restore it at the end!) — `await w.getResolution()`.
3. For each target resolution: `await w.setResolution('240')` → **wait until the dataset
   actually changes** → validate bar spacing → read bars.
4. Read bars from `pane.dataSources()[0].bars()`:
   - `b.size()`, `b.valueAt(i)` with **local indices `0..size-1`** (not logical indices),
   - each row = `[time, open, high, low, close, volume]`, `b.first()`/`b.last()`.
5. Save CSVs + restore the original resolution.
6. ~300 bars are kept in memory per resolution (4H ≈ 50 days, 5m ≈ 25 h). Good-enough default.

## Gotchas (all hit in real sessions)

- **First read trick:** if the chart is ALREADY on a target resolution, switching to it makes
  no change → the "wait for change" timeout fires and you lose that timeframe. Solution:
  capture the dataset of the *current* resolution first (before switching), or read it again
  at the end before restoring.
- **Don't wait with `Date.now()`/fixed sleeps only:** `setResolution` resolves before the data
  swap; poll the `first` bar timestamp + `size` until they change, then settle ~1.5 s.
- **Validate spacing after reading:** consecutive bar times should be `res*60` seconds apart
  (allow sessions/FX gaps); if wrong → wait 3 s and re-read.
- **Restore always** the user's original timeframe when done (`w.setResolution(orig)`), and
  verify with `getResolution()`.
- Every `Runtime.evaluate` call must be `Runtime.enable`d first; wrap reads in try/catch so one
  failure doesn't kill the run.

## Ready-to-run script

```python
import sys, json, time, csv, websocket, urllib.request

def get_ws_url():
    pages = json.load(urllib.request.urlopen("http://localhost:9222/json"))
    for p in pages:
        if p.get("type")=="page" and "tradingview.com/chart" in p.get("url",""):
            return p["webSocketDebuggerUrl"]

ws = websocket.create_connection(get_ws_url(), timeout=120, suppress_origin=True)
mid = 0
def call(m, p=None):
    global mid; mid += 1
    ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == mid: return r
call("Runtime.enable")

def js(e):
    r = call("Runtime.evaluate", {"expression": e, "returnByValue": True, "awaitPromise": True})
    res = r.get("result", {}).get("result", {})
    if "exceptionDetails" in res: return {"__err__": res["exceptionDetails"]["text"]}
    if "value" in res: return res["value"]
    return {"__desc__": res.get("description", "")}

def state():
    return js("""(function(){try{
      var b=_exposed_chartWidgetCollection.activeChartWidget.value()._modelWV.value().m_model._panes[0].dataSources()[0].bars();
      var f=b.first(),l=b.last();return {size:b.size(),first:f?f.value[0]:null};}catch(e){return {__err__:e.message};}})()""")

def read_bars():
    return js("""(function(){try{
      var b=_exposed_chartWidgetCollection.activeChartWidget.value()._modelWV.value().m_model._panes[0].dataSources()[0].bars();
      var o=[];for(var i=0;i<b.size();i++){var r=b.valueAt(i);if(r)o.push(r);}return o;}catch(e){return {__err__:e.message};}})()""")

def switch(res, prev_first):
    js(f"(async()=>{{var w=_exposed_chartWidgetCollection.activeChartWidget.value();await w.setResolution('{res}');}})()")
    for _ in range(30):
        time.sleep(0.7)
        s = state()
        if isinstance(s, dict) and "__err__" in s: continue
        if prev_first is None or s.get("first") != prev_first: 
            time.sleep(1.5); return True
    return False

res0 = js("(async()=>await _exposed_chartWidgetCollection.activeChartWidget.value().getResolution())()")
prev = state().get("first")
for res in [240, 60, 15, 5]:
    if not switch(res, prev):       # already on this TF -> data is the current one, read it below anyway
        pass
    bars = read_bars()
    if bars and not isinstance(bars, dict):
        with open(f"/tmp/ohlcv_{res}.csv","w",newline="") as f:
            w=csv.writer(f); w.writerow(["time","open","high","low","close","volume"]); w.writerows(bars)
        print(res, "min", len(bars), "bars -> /tmp/ohlcv_%s.csv" % res)
    prev = state().get("first")
js(f"(async()=>{{var w=_exposed_chartWidgetCollection.activeChartWidget.value();await w.setResolution('{res0}');}})()")
```

## Usage pattern (minimal, per request)

```bash
python3 tv_ohlcv.py   # → /tmp/ohlcv_240.csv /tmp/ohlcv_60.csv /tmp/ohlcv_15.csv /tmp/ohlcv_5.csv
```

Then summarize the last candles per timeframe in the chat (with dates) and offer the CSVs.

## Indicadores y análisis estructural (pandas-ta / fallback)

Regla general (estrategias): **no calcular indicadores a mano** — usar la librería `pandas-ta`
sobre los CSVs de `/tmp/ohlcv_<tf>.csv`.

```python
import pandas as pd, pandas_ta as ta
df = pd.read_csv('/tmp/ohlcv_60.csv', parse_dates=['time'], index_col='time')
df.ta.sma(length=20, append=True)     # etc: rsi, macd, ema, atr, engulfing vía df.ta.cdl_pattern
```

### Fallback (entornos sin pandas-ta)

`pandas-ta` NO está disponible en todos los entornos: las versiones recientes exigen
Python ≥3.12 y en Python 3.11 el índice de PyPI no las resuelve. Si `import pandas_ta`
falla:

1. Intentar `python3 -m pip install --user pandas-ta` (1 sola vez más).
2. Si sigue fallando, **no bloquearse** (máx 2 reintentos). Continuar con el **análisis
   estructural SMC** usando solo `pandas`/`numpy` (esto NO es calcular indicadores técnicos,
   es lógica de estructura de mercado):
   - Swings: máximos/mínimos locales con ventana izquierda/derecha (p.ej. 3/3).
   - Estructura: Higher Highs/Lower Lows vs Lower Highs/Lower Lows sobre los últimos swings.
   - Vela envolvente (engulfing): comparar cuerpo de la vela actual vs la previa
     (`c1>o1 and c0<o0 and o1<=c0 and c1>=o0` para alcista; invertido para bajista).
   - Pool de liquidez: agregar daily por día (NY) `high/low` → PDH/PDL; por sesiones
     (Asia 20-08 NY, Londres 08-13 NY, NY 13-20 NY) → H/L de sesión.
3. **Documentar en la respuesta** que se usó el fallback (ej. `pandas-ta` no disponible:
   análisis estructural con pandas/numpy).

## Relación con la sesión NY y conversión de huso

- Los timestamps de los CSVs están en **UTC** (unix seconds). La sesión de Nueva York se
  evalúa en **EDT (UTC-4)** en verano: `dt_ny = dt - 4h`.
- Ventana NY: 09:30–16:00 EST/EDT. Para el checklist de sesión reportar `ABIERTA/CERRADA`.
- Los CSVs se guardan en `/tmp/` (efímero); para análisis posteriores en la misma sesión
  reutilizarlos, no re-extraer.

## Related

- `tradingview-debug-launch` skill — enabling/verifying the CDP port.
- `tradingview-drawings` skill — using the same model access to draw/read drawings.
- `scan-nas100` skill — rutina completa de validación SMC que consume estos CSVs.