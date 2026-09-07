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

# Switch to 1H (60) and wait for data change
prev = js("""(function(){try{var b=_exposed_chartWidgetCollection.activeChartWidget.value()._modelWV.value().m_model._panes[0].dataSources()[0].bars();var f=b.first();return f?f.value[0]:null;}catch(e){return null;}})()""")
js("""(async()=>{var w=_exposed_chartWidgetCollection.activeChartWidget.value();await w.setResolution('60');})()""")
for _ in range(30):
    time.sleep(0.7)
    cur = js("""(function(){try{var b=_exposed_chartWidgetCollection.activeChartWidget.value()._modelWV.value().m_model._panes[0].dataSources()[0].bars();var f=b.first();return f?f.value[0]:null;}catch(e){return null;}})()""")
    if cur != prev:
        time.sleep(1.5); break

res = js("""(function(){
  const w=_exposed_chartWidgetCollection.activeChartWidget.value();
  const m=w._modelWV.value().m_model;
  const bars=m._panes[0].dataSources()[0].bars();
  const last=bars.last();
  return {res:w._resolutionWV.value(), lastIdx:last?last.index:null, lastT:last?last.value[0]:null};
})()""")
print("resolucion:", res)

# anchors: name, 1H index, price, color
anchors = [
    ("PDL 29421",       269, 29421.2, '#26a69a'),
    ("ASIA LOW 29559",  279, 29558.8, '#26a69a'),
    ("LONDON LOW 29645",286, 29645.3, '#26a69a'),
    ("NY LOW 29675",    295, 29674.5, '#26a69a'),
    ("ASIA HIGH 29765", 299, 29764.9, '#ef5350'),
    ("PDH 29773",       262, 29773.4, '#ef5350'),
    ("NY HIGH 29818",   292, 29818.4, '#ef5350'),
    ("DAY HIGH 29890",  287, 29889.5, '#ef5350'),
]

script = r"""
(async()=>{
  const w = _exposed_chartWidgetCollection.activeChartWidget.value();
  const m = w._modelWV.value().m_model;
  const pane = m._panes[0];
  const OUT = [];
  // remove existing rays
  const toRemove = [];
  for (const pn of m._panes){ for (const s of pn.dataSources()){ try { if (s.name && s.name() === 'Horizontal ray') toRemove.push(s); } catch(e){} } }
  for (const s of toRemove){ try { pane.removeDataSource(s, true); } catch(e){} }
  m.fullUpdate && m.fullUpdate();
  await new Promise(r=>setTimeout(r, 300));
  const m695 = window.__req(695211);
  await m695.initLineTool('LineToolHorzRay');
  const anchors = __ANCHORS__;
  for (const [name, idx, price, color] of anchors){
    try {
      const l = m.createLineTool({linetool:'LineToolHorzRay', point:{index:idx, price:price}, pane, properties:null});
      const ch = l.properties().childs();
      ch.linecolor && ch.linecolor.setValue(color);
      if (ch.text) ch.text.setValue(name);
      OUT.push('ray '+name+' @ idx '+idx);
    } catch(e){ OUT.push('ray '+name+' ERR '+e.message); }
  }
  m.fullUpdate && m.fullUpdate();
  await new Promise(r=>setTimeout(r, 400));
  return OUT;
})()
"""
script = script.replace("__ANCHORS__", json.dumps(anchors))
print(json.dumps(js(script, True), indent=1, ensure_ascii=False)[:2000])
