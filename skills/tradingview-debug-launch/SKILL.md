---
name: tradingview-debug-launch
description: How to open and close TradingView Desktop in debug mode (CDP port 9222) so drawing tools can be read/created programmatically, plus how to verify the connection fast. Use when the user asks to start/restart TradingView for chart scripting/drawing, or when the CDP port is not responding and you need to relaunch it quickly.
---

# TradingView Desktop: abrir normal vs modo debug

**Regla por defecto — abrir TradingView de forma NORMAL** (`open -a TradingView`, sin flags).
Así los dibujos se guardan y sincronizan con el móvil, y el uso es el habitual.

Esto es importante por un hallazgo verificado (2026-08-13): la pérdida de dibujos al cambiar
de símbolo NO se debe al modo debug, sino al **símbolo/broker**. En `CAPITALCOM:NAS100` los
dibujos se guardan; en `PEPPERSTONE:NAS100` no. Por eso **usar siempre `CAPITALCOM:NAS100`**
y abrir TradingView normalmente.

**Modo debug (CDP 9222) SOLO se usa puntualmente** cuando se necesita scripting/lectura
programática (extraer OHLCV o dibujar vía CDP). Al terminar el scripting, cerrar y reabrir en
modo normal para el uso diario.

## Apertura normal (uso diario)

```bash
open -a TradingView        # sin flags -> sin CDP, dibujos persistentes
```

## Modo debug (solo scripting)

TradingView Desktop solo expone el CDP en **http://localhost:9222** cuando se lanza **con el
flag** `--remote-debugging-port=9222`. `open -a TradingView` normal NO lo habilita.

Electron apps are single-instance: si TradingView ya está corriendo, el nuevo comando se
ignora y NO se pasan los args. Por eso: salir primero, luego lanzar con el flag.

```bash
osascript -e 'quit app "TradingView"' 2>/dev/null
sleep 3
pkill -f "TradingView.app/Contents/MacOS/TradingView" 2>/dev/null
sleep 2
open -a TradingView --args --remote-debugging-port=9222
```

Path/port notes:
- Port: **9222** (matches the `tradingview-draw` MCP default).
- Confirm the flag actually took: `ps aux | grep "TradingView --remote" | grep -v grep` should
  show `--remote-debugging-port=9222`.

## 2. Esperar CDP listo (poll rápido, solo en modo debug)

El puerto aparece antes de que el gráfico termine de cargar — tarda ~30–120 s en frío.
Pollear hasta que exista la página del chart:

```bash
for i in $(seq 1 60); do
  if curl -s -m 2 "http://localhost:9222/json?t=$i" 2>/dev/null | grep -q "tradingview.com/chart"; then
    echo "CDP_UP_${i}"; break
  fi
  sleep 2
done
```

- If TradingView was already open before you quit it, it restores the last layout/symbol
  (e.g. `PEPPERSTONE:NAS100 · 60`), so you can resume right where the user was.
- Run this poll as the FIRST step of the open flow instead of a slow generic poll; the
  loop above is the intended one-liner.

## 3. Smoke test rápido (conexión + gráfico correcto)

Esto SÓLO aplica en modo debug (con CDP). Si TradingView está abierto normal, no hay CDP y no
se puede hacer scripting — es el comportamiento esperado.

```bash
# list chart page WebSocket URL
curl -s http://localhost:9222/json | grep -o '"webSocketDebuggerUrl": "[^"]*chart[^"]*"'
```

Python (`websocket-client`) — note **`suppress_origin=True`** (Chrome rejects a wrong origin):

```python
import json, websocket, urllib.request
pages = json.load(urllib.request.urlopen("http://localhost:9222/json"))
ws_url = next(p["webSocketDebuggerUrl"] for p in pages
              if p.get("type")=="page" and "tradingview.com/chart" in p.get("url",""))
ws = websocket.create_connection(ws_url, suppress_origin=True)

def js(expr):
    ws.send(json.dumps({"id":1,"method":"Runtime.evaluate",
        "params":{"expression":expr,"returnByValue":True,"awaitPromise":True}}))
    while True:
        r=json.loads(ws.recv())
        if r.get("id")==1:
            v=r["result"]["result"]; return v.get("value", v.get("description",""))

# symbol + interval + drawing count in one call
print(js("""(async()=>{const w=_exposed_chartWidgetCollection.activeChartWidget.value();
  const m=w._modelWV.value().m_model;const s=m._panes[0].dataSources();
  let cnt=0;for(const x of s){const n=x.name?x.name():'';if(/ray|risk|reward|path|Trend|Position/i.test(n))cnt++;}
  return {sym:await w.getSymbol(), res:w._resolutionWV.value(), drawings:cnt};})()"""))
```

If `drawings` > 0, the chart already has marked levels — read them before drawing anything.

## 4. Cerrar TradingView (modo debug)

```bash
osascript -e 'quit app "TradingView"' 2>/dev/null   # graceful
pkill -f "TradingView.app/Contents/MacOS/TradingView" 2>/dev/null  # hard kill fallback
```

El flag de debug NO persiste — el siguiente arranque normal (`open -a TradingView`) no tendrá
CDP. **Tras terminar el scripting, reabrir en modo normal** para el uso diario y la
sincronización de dibujos al móvil.

## 5. Modos de fallo comunes → arreglo rápido

| Síntoma | Causa | Fix |
|---|---|---|
| `/json/version` vacío / sin JSON | TradingView abierto NORMAL (sin CDP) | es esperado; solo hay CDP en modo debug (sección 1) |
| `/json/version` vacío pero se lanzó con flag | flag no tomado | salir + relanzar con `--remote-debugging-port=9222` (sección 1) |
| puerto 9222 en uso por otra app | conflicto | usar otro puerto (p.ej. `--remote-debugging-port=9223`) |
| `Runtime.evaluate` conexión 403 | header origin | `suppress_origin=True` |
| arranque largo antes del chart | frío / login | pollear hasta ~2 min; el usuario debe estar logueado |
| símbolo cambió a media sesión | usuario cambió de pestaña | re-chequear `await getSymbol()` al inicio de cada script |

## Reference
- Drawing skill (how to read/create/delete drawings once connected):
  `~/.gemini/config/skills/tradingview-drawings/SKILL.md`