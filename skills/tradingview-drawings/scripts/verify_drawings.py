import json, websocket, urllib.request
from datetime import datetime, timezone
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

r = js("""(function(){
  const w=_exposed_chartWidgetCollection.activeChartWidget.value();
  const m=w._modelWV.value().m_model;
  const out=[];
  for(const pn of m._panes){for(const s of pn.dataSources()){
    try{ const nm=s.name?s.name():'?';
      if(['Horizontal ray','Horizontal line','Rectangle','Path','Text','Trend Line'].includes(nm)){
        let txt=''; try{ txt=s.properties().childs().text.value(); }catch(e){}
        const pts=(s.points&&s.points())||[];
        out.push(nm+' | '+(txt||'')+' | '+(pts.length?JSON.stringify(pts.map(p=>({t:p.time,p:p.price}))):''));
      }
    }catch(e){}
  }}
  return out;
})()""")
print("resolucion:", js("_exposed_chartWidgetCollection.activeChartWidget.value()._resolutionWV.value()"))
print("TOTAL:", len(r))
for x in r: print(x[:220])
