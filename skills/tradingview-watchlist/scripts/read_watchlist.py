import json, websocket, urllib.request

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

# Get the full innerText after "Lista de seguimiento" to capture symbol rows
r = js("""(function(){
  const body = document.body.innerText;
  const idx = body.indexOf('Lista de seguimiento');
  // find the section with columns Símbolo/Última/Cambio%
  const colIdx = body.indexOf('Símbolo');
  if(colIdx<0) return 'no columns';
  return body.slice(colIdx, colIdx+2000);
})()""")
print(r)
