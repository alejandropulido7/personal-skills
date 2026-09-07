import json, websocket, urllib.request
def get_ws_url():
    pages = json.load(urllib.request.urlopen("http://localhost:9222/json"))
    for p in pages:
        if p.get("type")=="page" and "tradingview.com/chart" in p.get("url",""):
            return p["webSocketDebuggerUrl"]
ws = websocket.create_connection(get_ws_url(), timeout=120, suppress_origin=True)
mid=0
def call(m,p=None):
    global mid; mid+=1
    ws.send(json.dumps({"id":mid,"method":m,"params":p or {}}))
    while True:
        r=json.loads(ws.recv())
        if r.get("id")==mid: return r
call("Runtime.enable")
def js(e,ap=False):
    r=call("Runtime.evaluate",{"expression":e,"returnByValue":True,"awaitPromise":ap})
    res=r.get("result",{}).get("result",{})
    if "exceptionDetails" in res: return {"__err__":res["exceptionDetails"]["text"]}
    if "value" in res: return res["value"]
    return {"__desc__":res.get("description","")}

script = r"""
(async()=>{
  const w = _exposed_chartWidgetCollection.activeChartWidget.value();
  const m = w._modelWV.value().m_model;
  const pane = m._panes[0];
  const OUT = {};
  const m695 = window.__req(695211);
  // make sure rect tool loaded into create registry
  for (const nm of ['LineToolRect','LineToolRectangle']) {
    try { await m695.initLineTool(nm); OUT['init '+nm]='ok'; } catch(e){ OUT['init '+nm]=e.message; }
  }
  for (const nm of ['LineToolRect','LineToolRectangle']) {
    try {
      const l = m.createLineTool({linetool:nm, point:{index:286, price:29674.5}, pane, properties:null});
      l.addPoint({index:299, price:29645.3});
      const ch = l.properties().childs();
      if(ch.linecolor) ch.linecolor.setValue('#26a69a');
      if(ch.backgroundColor) ch.backgroundColor.setValue('rgba(38,166,154,0.15)');
      OUT['created '+nm] = 'yes';
    } catch(e){ OUT['created '+nm] = 'ERR '+e.message; }
  }
  m.fullUpdate && m.fullUpdate();
  await new Promise(r=>setTimeout(r,400));
  const names=[];
  for (const pn of m._panes){ for (const s of pn.dataSources()){ try{names.push(s.name?s.name():'?');}catch(e){} } }
  OUT.datasources = names.slice(0,30);
  return OUT;
})()
"""
print(json.dumps(js(script, True), indent=1, ensure_ascii=False)[:2500])
