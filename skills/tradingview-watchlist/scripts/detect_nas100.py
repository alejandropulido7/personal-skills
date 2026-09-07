"""
detect_nas100.py — Detecta el simbolo NAS100 COMPLETO (con broker) desde la watchlist
del TradingView Desktop (via CDP 9222). Abre el panel de la lista (widgetbar) si esta
cerrado y lee las filas [data-symbol-full] en la misma sesion (el panel se cierra solo
si se cambia de simbolo entre llamadas). Busca en TODAS las listas del panel la fila
con data-symbol-short == target y devuelve su data-symbol-full (p.ej. CAPITALCOM:NAS100).

Uso: python3 detect_nas100.py [--short NAS100]
Salida: JSON con filas encontradas + BEST_SYMBOL=<full> de la fila activa.
"""
import json, sys, time, websocket, urllib.request

def get_ws_url():
    pages = json.load(urllib.request.urlopen("http://localhost:9222/json", timeout=5))
    for p in pages:
        if p.get("type")=="page" and "tradingview.com/chart" in p.get("url",""):
            return p["webSocketDebuggerUrl"]
    raise RuntimeError("no chart page (TradingView abierto normal sin CDP?)")

ws = websocket.create_connection(get_ws_url(), timeout=30, suppress_origin=True)
ws.settimeout(25)
mid = 0
def call(m, p=None):
    global mid; mid += 1
    ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == mid: return r
call("Runtime.enable")

def js(e, ap=False):
    r = call("Runtime.evaluate", {"expression": e, "returnByValue": True, "awaitPromise": ap})
    res = r.get("result", {}).get("result", {})
    if "exceptionDetails" in res: return {"__js_err__": res["exceptionDetails"]["text"]}
    if "value" in res: return res["value"]
    return {"__desc__": res.get("description", "")}

target = "NAS100"
args = sys.argv[1:]
i = 0
while i < len(args):
    if args[i] == "--short" and i+1 < len(args): target = args[i+1]; i += 2
    else: i += 1

CLICK_JS = r"""(function(){
  const all=document.querySelectorAll('button');
  for(const el of all){
    const aria=(el.getAttribute('aria-label')||'').trim();
    if(/Lista de seguimiento/.test(aria)){ el.click(); return 'clicked'; }
  }
  return 'not-found';
})()"""

READ_JS = r"""
(function(){
  const target = __TARGET__;
  const found = [];
  const rows = document.querySelectorAll('[data-symbol-full]');
  for(const r of rows){
    const short = r.getAttribute('data-symbol-short') || '';
    if(short.toUpperCase() === target.toUpperCase()){
      const full = r.getAttribute('data-symbol-full') || '';
      const active = r.getAttribute('data-active') === 'true';
      let listName = '?';
      let p = r;
      for(let d=0; p && d<12; d++){
        const txt = p.querySelector && p.querySelector('[class*=titleRow], [class*=titleText]');
        if(txt && (txt.textContent||'').trim()){
          const t = (txt.textContent||'').trim();
          if(t && !/Simbolo|Ultima|Cbo|Cambio/.test(t)){ listName = t; break; }
        }
        p = p.parentElement;
      }
      found.push({short, full, active, list: listName});
    }
  }
  return found;
})()
"""
READ_JS = READ_JS.replace("__TARGET__", json.dumps(target))

# polling: click (si no hay filas) y esperar hasta 12s
res = None
for attempt in range(6):
    # click if panel closed
    has_rows = js("document.querySelectorAll('[data-symbol-full]').length")
    if not isinstance(has_rows, (int, float)) or has_rows == 0:
        js(CLICK_JS)
    time.sleep(2)
    res = js(READ_JS)
    if isinstance(res, list) and len(res) > 0:
        break

print(json.dumps(res, indent=1, ensure_ascii=False)[:1500])
if isinstance(res, list) and res:
    best = next((x for x in res if x.get("active")), res[0])
    print("BEST_SYMBOL=" + best["full"])
else:
    print("NO_SYMBOL_FOUND for", target)