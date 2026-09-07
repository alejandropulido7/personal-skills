import sys, json, time, websocket, urllib.request

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

def js(e, await_promise=False):
    r = call("Runtime.evaluate", {"expression": e, "returnByValue": True, "awaitPromise": await_promise})
    res = r.get("result", {}).get("result", {})
    if "exceptionDetails" in res: return {"__err__": res["exceptionDetails"]["text"]}
    if "value" in res: return res["value"]
    return {"__desc__": res.get("description", "")}

# Load line tools via webpack
print("loading tools...")
print(js("window.webpackChunktradingview.push([['__probe__'], {}, (r)=>{window.__req=r;}]); 'ok'"))
for tool in ['LineToolHorzLine','LineToolRect','LineToolPath','LineToolTrendLine','LineToolText']:
    r = js(f"(async()=>{{const m=window.__req(695211); await m.initLineTool('{tool}'); return 'loaded {tool}';}})()", True)
    print(r)

print("get last index:")
print(js("""(function(){var m=_exposed_chartWidgetCollection.activeChartWidget.value()._modelWV.value().m_model;
var p=m._panes[0];var b=p.dataSources()[0].bars();var l=b.last();return {idx:l.index,res:_exposed_chartWidgetCollection.activeChartWidget.value()._resolutionWV.value()};})()"""))

# Create drawings
draw_script = r"""
(async()=>{
  const w = _exposed_chartWidgetCollection.activeChartWidget.value();
  const m = w._modelWV.value().m_model;
  const pane = m._panes[0];
  const OUT = [];
  const created = [];

  function safe(fn, label){
    try { const r = fn(); OUT.push([label, 'OK']); return r; }
    catch(e){ OUT.push([label, 'ERR: '+e.message]); return null; }
  }
  function addName(line, txt){
    try {
      const ch = line.properties().childs();
      if (ch && ch.text) { ch.text.setValue(txt); OUT.push(['text '+txt, 'OK']); }
      else OUT.push(['text '+txt, 'no child']);
    } catch(e){ OUT.push(['text '+txt, 'ERR '+e.message]); }
  }

  const m695 = window.__req(695211);

  // --- SL horz line @ 29630 ---
  safe(()=>{
    const l = m.createLineTool({linetool:'LineToolHorzLine', point:{index:299, price:29630}, pane, properties:null});
    const ch = l.properties().childs();
    ch.linecolor && ch.linecolor.setValue('#ef5350');
    ch.linestyle && ch.linestyle.setValue(2);
    addName(l, 'SL 29630');
    created.push(l);
  }, 'SL line');

  // --- TP horz line @ 29795 ---
  safe(()=>{
    const l = m.createLineTool({linetool:'LineToolHorzLine', point:{index:299, price:29795}, pane, properties:null});
    const ch = l.properties().childs();
    ch.linecolor && ch.linecolor.setValue('#26a69a');
    ch.linestyle && ch.linestyle.setValue(2);
    addName(l, 'TP 29795');
    created.push(l);
  }, 'TP line');

  // --- Entry horz line @ 29685 ---
  safe(()=>{
    const l = m.createLineTool({linetool:'LineToolHorzLine', point:{index:299, price:29685}, pane, properties:null});
    const ch = l.properties().childs();
    ch.linecolor && ch.linecolor.setValue('#ffb74d');
    addName(l, 'ENTRADA 29685');
    created.push(l);
  }, 'ENTRY line');

  // --- Order Block rectangle 29645.3-29674.5 (from idx 286 to 299) ---
  safe(()=>{
    const l = m.createLineTool({linetool:'LineToolRect', point:{index:286, price:29674.5}, pane, properties:null});
    l.addPoint({index:299, price:29645.3});
    const ch = l.properties().childs();
    ch.linecolor && ch.linecolor.setValue('#26a69a');
    ch.backgroundColor && ch.backgroundColor.setValue('rgba(38,166,154,0.15)');
    addName(l, 'OB / DEMAND 29645-29675');
    created.push(l);
  }, 'OB rect');

  // --- Trend path: 29421.2 (idx 265) -> 29645.3 (idx 286) -> 29702.5 (idx 296) ---
  safe(()=>{
    const l = m.createLineTool({linetool:'LineToolPath', point:{index:265, price:29421.2}, pane, properties:null});
    l.addPoint({index:286, price:29645.3});
    l.addPoint({index:296, price:29702.5});
    const ch = l.properties().childs();
    ch.linecolor && ch.linecolor.setValue('#2962ff');
    addName(l, 'TENDENCIA 4H');
    created.push(l);
  }, 'trend path');

  // --- Text: esperar sweep ---
  safe(()=>{
    const l = m.createLineTool({linetool:'LineToolText', point:{index:299, price:29790}, pane, properties:null});
    const ch = l.properties().childs();
    ch.text && ch.text.setValue('Esperar sweep 29674/29645 + engulfing 5m alcista -> LONG');
    ch.color && ch.color.setValue('#ffb74d');
    created.push(l);
  }, 'text wait');

  // --- Text: fakeout/breakout prob ---
  safe(()=>{
    const l = m.createLineTool({linetool:'LineToolText', point:{index:299, price:29690}, pane, properties:null});
    const ch = l.properties().childs();
    ch.text && ch.text.setValue('Breakout 70% / Fakeout 30%');
    ch.color && ch.color.setValue('#42a5f5');
    created.push(l);
  }, 'text prob');

  m.fullUpdate && m.fullUpdate();
  await new Promise(r=>setTimeout(r, 400));
  // enumerate
  const names = [];
  for (const pn of m._panes){
    for (const s of pn.dataSources()){
      try { names.push(s.name? s.name(): '?'); } catch(e){}
    }
  }
  return {draw: OUT, datasources: names.slice(0, 30)};
})()
"""
res = js(draw_script, True)
print(json.dumps(res, indent=1, ensure_ascii=False)[:3000])
