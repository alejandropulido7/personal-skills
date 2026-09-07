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

to_remove = ["PDL 29421", "ASIA LOW 29559", "ASIA HIGH 29765", "NY HIGH 29818", "DAY HIGH 29890"]

# two-pass: first collect all ray data sources + labels, then remove the matching ones
script = r"""
(async()=>{
  const w = _exposed_chartWidgetCollection.activeChartWidget.value();
  const m = w._modelWV.value().m_model;
  const pane = m._panes[0];
  const OUT = [];
  const rmList = __RM__;

  // PASS 1: collect
  const found = [];
  for (const pn of m._panes){
    for (const s of pn.dataSources()){
      try {
        if (s.name && s.name() === 'Horizontal ray'){
          let txt=''; try{ txt = s.properties().childs().text.value(); }catch(e){}
          found.push({s, txt});
        }
      } catch(e){}
    }
  }
  OUT.push('total rays encontrados: '+found.length);
  OUT.push('nombres: '+found.map(f=>f.txt).join(' | '));

  // PASS 2: remove matching
  for (const f of found){
    if (rmList.includes(f.txt)){
      try { pane.removeDataSource(f.s, true); OUT.push('ELIMINADO: '+f.txt); } catch(e){ OUT.push('ERR eliminar '+f.txt+' '+e.message); }
    } else {
      OUT.push('CONSERVADO: '+f.txt);
    }
  }
  m.fullUpdate && m.fullUpdate();
  await new Promise(r=>setTimeout(r, 400));

  // verify
  const remaining=[];
  for (const pn of m._panes){ for (const s of pn.dataSources()){ try { if (s.name && s.name()==='Horizontal ray'){ let t=''; try{t=s.properties().childs().text.value();}catch(e){} remaining.push(t); } }catch(e){} } }
  OUT.push('RAYS RESTANTES: '+remaining.length+' -> '+remaining.join(' | '));
  return OUT;
})()
"""
script = script.replace("__RM__", json.dumps(to_remove))
print(json.dumps(js(script, True), indent=1, ensure_ascii=False)[:1800])
