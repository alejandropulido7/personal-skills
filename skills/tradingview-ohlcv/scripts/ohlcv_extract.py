import sys, json, time, csv, websocket, urllib.request

def get_ws_url():
    pages = json.load(urllib.request.urlopen("http://localhost:9222/json"))
    for p in pages:
        if p.get("type")=="page" and "tradingview.com/chart" in p.get("url",""):
            return p["webSocketDebuggerUrl"]
    raise RuntimeError("no chart page found")

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
      var f=b.first(),l=b.last();return {size:b.size(),first:f?f.value[0]:null,last:l?l.value[0]:null,sym:_exposed_chartWidgetCollection.activeChartWidget.value()._resolutionWV.value()};}catch(e){return {__err__:e.message};}})()""")

def read_bars():
    return js("""(function(){try{
      var b=_exposed_chartWidgetCollection.activeChartWidget.value()._modelWV.value().m_model._panes[0].dataSources()[0].bars();
      var o=[];for(var i=0;i<b.size();i++){var r=b.valueAt(i);if(r)o.push(r);}return o;}catch(e){return {__err__:e.message};}})()""")

res0 = js("(async()=>await _exposed_chartWidgetCollection.activeChartWidget.value().getResolution())()")
print("original resolution:", res0)

def switch(res, prev_first):
    js(f"(async()=>{{var w=_exposed_chartWidgetCollection.activeChartWidget.value();await w.setResolution('{res}');}})()")
    for _ in range(30):
        time.sleep(0.7)
        s = state()
        if isinstance(s, dict) and "__err__" in s: continue
        if prev_first is None or s.get("first") != prev_first:
            time.sleep(1.5); return True
    return False

prev = state().get("first")
for res in [240, 60, 15, 5]:
    switch(res, prev)
    bars = read_bars()
    if bars and not isinstance(bars, dict):
        with open(f"/tmp/ohlcv_{res}.csv","w",newline="") as f:
            w=csv.writer(f); w.writerow(["time","open","high","low","close","volume"]); w.writerows(bars)
        print(res, "min", len(bars), "bars -> /tmp/ohlcv_%s.csv" % res, "first", bars[0][0], "last", bars[-1][0])
    prev = state().get("first")
js(f"(async()=>{{var w=_exposed_chartWidgetCollection.activeChartWidget.value();await w.setResolution('{res0}');}})()")
print("restored resolution:", js("(async()=>await _exposed_chartWidgetCollection.activeChartWidget.value().getResolution())()"))
