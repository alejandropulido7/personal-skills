import json, time, websocket, urllib.request

def get_ws_url():
    pages = json.load(urllib.request.urlopen("http://localhost:9222/json"))
    for p in pages:
        if p.get("type")=="page" and "tradingview.com/chart" in p.get("url",""):
            return p["webSocketDebuggerUrl"]
    raise RuntimeError("no chart page")

ws = websocket.create_connection(get_ws_url(), timeout=120, suppress_origin=True)
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
    if "exceptionDetails" in res: return {"__err__": res["exceptionDetails"]["text"]}
    if "value" in res: return res["value"]
    return {"__desc__": res.get("description", "")}

# plain lines, one per rule (no table chars). Done=green check, pending=orange circle.
text = (
    "✅ Tendencia 4H: ALCISTA (HH/HL)\n"
    "✅ Tendencia 1H/15m: NEUTRO\n"
    "✅ Sesión NY: CERRADA (22:40 EDT)\n"
    "✅ Sweep consumido: BUY-side @29889 (PDH)\n"
    "🟠 Sweep sell-side pendiente 29645/29675\n"
    "🟠 MSS: ruptura con cuerpo del swing\n"
    "🟠 Vela envolvente 5m alcista\n"
    "🟠 ENTRADA al cierre de la envolvente\n"
    "✅ R:R 1:2 | SL 29630 | TP 29795\n"
    "📊 Breakout 70% / Fakeout 30%"
)

script = r"""
(async()=>{
  const w = _exposed_chartWidgetCollection.activeChartWidget.value();
  const m = w._modelWV.value().m_model;
  const pane = m._panes[0];
  const bars = pane.dataSources()[0].bars();
  const last = bars.last();
  const lastIdx = last ? last.index : 299;
  const lastClose = last ? last.value[4] : null;
  const OUT = [];

  // 1) remove existing Text tools
  const toRemove = [];
  for (const pn of m._panes){ for (const s of pn.dataSources()){ try { if (s.name && s.name() === 'Text') toRemove.push(s); } catch(e){} } }
  for (const s of toRemove){ try { pane.removeDataSource(s, true); } catch(e){} }
  m.fullUpdate && m.fullUpdate();
  await new Promise(r=>setTimeout(r, 300));

  // 2) create single text, plain lines, blue, size 16
  const m695 = window.__req(695211);
  await m695.initLineTool('LineToolText');
  const txt = __TEXT__;
  try {
    const l = m.createLineTool({linetool:'LineToolText', point:{index:lastIdx, price:lastClose+35}, pane, properties:null});
    const ch = l.properties().childs();
    if (ch.text) ch.text.setValue(txt);
    if (ch.color) ch.color.setValue('#2196f3');   // blue
    if (ch.fontsize) ch.fontsize.setValue(16);     // size 16
    OUT.push('created text size16 blue @ idx '+lastIdx);
  } catch(e){ OUT.push('create ERR '+e.message); }

  m.fullUpdate && m.fullUpdate();
  await new Promise(r=>setTimeout(r, 400));

  let textCount=0;
  for (const pn of m._panes){ for (const s of pn.dataSources()){ try { if (s.name && s.name()==='Text') textCount++; } catch(e){} } }
  OUT.push('text count: '+textCount);
  return OUT;
})()
"""
script = script.replace("__TEXT__", json.dumps(text))
print(json.dumps(js(script, True), indent=1, ensure_ascii=False)[:800])
print("--- TEXTO COLOCADO ---")
print(text)
