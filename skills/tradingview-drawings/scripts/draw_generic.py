"""
draw_generic.py — Dibujo genérico multi-estrategia vía CDP 9222.
Recibe niveles desde un JSON y dibuja rays, rectángulo, SL/TP/Entrada y checklist.

Uso:
  python3 draw_generic.py --levels /tmp/levels.json [--symbol X] [--res 60]

JSON schema (generado por scripts de análisis):
  {"rays": [["Nombre", precio, "#color"], ...],
   "ob_hi": n, "ob_lo": n,
   "entry": n, "sl": n, "tp": n,
   "checklist": "texto con \\n",
   "mss": null | n}
"""
import json, os, sys, websocket, urllib.request

def get_ws_url():
    pages = json.load(urllib.request.urlopen("http://localhost:9222/json", timeout=5))
    for p in pages:
        if p.get("type")=="page" and "tradingview.com/chart" in p.get("url",""):
            return p["webSocketDebuggerUrl"]
    raise RuntimeError("no chart page (TradingView sin CDP?)")

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
    if "exceptionDetails" in r.get("result", {}):
        return {"__js_err__": r["result"]["exceptionDetails"].get("text","")}
    res = r.get("result", {}).get("result", {})
    if "exceptionDetails" in res: return {"__js_err__": res["exceptionDetails"].get("text","")}
    if "value" in res: return res["value"]
    return {"__desc__": res.get("description","")}

def main():
    levels_file = None
    symbol = None
    resolution = "60"
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--levels" and i+1 < len(args): levels_file = args[i+1]; i += 2
        elif args[i] == "--symbol" and i+1 < len(args): symbol = args[i+1]; i += 2
        elif args[i] == "--res" and i+1 < len(args): resolution = args[i+1]; i += 2
        else: i += 1

    if levels_file and os.path.exists(levels_file):
        with open(levels_file) as f: L = json.load(f)
    else: L = {}

    rays = L.get("rays", [["LONDON LOW 30070", 30070.4, '#26a69a'], ["ASIA LOW 30028", 30027.5, '#26a69a'], ["PDH 30170", 30169.6, '#ef5350']])
    ob_hi = L.get("ob_hi", 30110.0)
    ob_lo = L.get("ob_lo", 30070.4)
    entry = L.get("entry", 30090.0)
    sl = L.get("sl", 30055.0)
    tp = L.get("tp", 30160.0)
    checklist = L.get("checklist", "Niveles no especificados\nUsar --levels")
    mss = L.get("mss")

    payload = {"rays": rays, "ob_hi": ob_hi, "ob_lo": ob_lo, "entry": entry, "sl": sl, "tp": tp, "checklist": checklist, "symbol": symbol or "AUTO", "resolution": resolution, "mss": mss}

    SCRIPT = """
(async()=>{
  window.webpackChunktradingview.push([['__probe__'], {}, (r) => { window.__req = r; }]);
  const P = __PAYLOAD__;
  const w = _exposed_chartWidgetCollection.activeChartWidget.value();
  const m = w._modelWV.value().m_model;
  const pane = m._panes[0];
  const OUT = []; const log = (x)=>OUT.push(x);

  let targetSymbol = P.symbol;
  if(targetSymbol === 'AUTO' || !targetSymbol){
    try{ const cur = await w.getSymbol(); targetSymbol = String(cur); log('using current sym '+targetSymbol); }
    catch(e){ log('sym err '+e.message); targetSymbol = 'CAPITALCOM:NAS100'; }
  }

  try{
    const cur = await w.getSymbol();
    if(String(cur).toUpperCase() !== String(targetSymbol).toUpperCase()){
      await w.setSymbol(targetSymbol); log('nav -> '+targetSymbol);
      await new Promise(r=>setTimeout(r, 3500));
    } else { log('sym already '+cur); }
    const res = w._resolutionWV.value();
    if(String(res) !== String(P.resolution)){
      await w.setResolution(String(P.resolution)); log('res -> '+P.resolution);
      await new Promise(r=>setTimeout(r, 2500));
    } else { log('res already '+res); }
  }catch(e){ log('nav ERR '+e.message); }

  const bars = pane.dataSources()[0].bars();
  function findIdx(price, isRes){
    for(let i=0;i<bars.size();i++){
      const v=bars.valueAt(i); if(!v) continue;
      if(isRes && Math.abs(v[2]-price)<1.0) return i;
      if(!isRes && Math.abs(v[3]-price)<1.0) return i;
    }
    for(let i=0;i<bars.size();i++){
      const v=bars.valueAt(i); if(!v) continue;
      if(Math.abs(v[2]-price)<2.5 || Math.abs(v[3]-price)<2.5) return i;
    }
    return bars.last() ? bars.last().index : 299;
  }
  const last = bars.last(); const lastIdx = last ? last.index : 299;
  const lastClose = last ? last.value[4] : null;

  const all=[];
  for(const pn of m._panes){ for(const s of pn.dataSources()){ try{ all.push(s); }catch(e){} } }
  let cleared=0;
  for(const s of all){
    try{
      const n=s.name?s.name():'';
      if(/Horizontal ray|Horizontal line|Rectangle|Path|Text|Trend Line|RiskReward|Position/i.test(n)){
        pane.removeDataSource(s,true); cleared++;
      }
    }catch(e){}
  }
  log('cleared='+cleared);
  m.fullUpdate && m.fullUpdate();
  await new Promise(r=>setTimeout(r,400));

  const m695 = window.__req(695211);

  await m695.initLineTool('LineToolHorzRay');
  for(const [name, price, color] of P.rays){
    try{
      const idx = findIdx(price, color==='#ef5350');
      if(idx===null){ log('ray '+name+' no bar'); continue; }
      const l=m.createLineTool({linetool:'LineToolHorzRay', point:{index:idx, price}, pane, properties:null});
      const ch=l.properties().childs();
      if(ch.linecolor) ch.linecolor.setValue(color);
      if(ch.text) ch.text.setValue(name);
      log('ray '+name+' @'+idx);
    }catch(e){ log('ray ERR '+name+' '+e.message); }
  }

  if(P.mss !== null && P.mss !== undefined){
    try{
      const idx = findIdx(P.mss, true) ?? findIdx(P.mss, false) ?? lastIdx;
      const l=m.createLineTool({linetool:'LineToolHorzRay', point:{index:idx, price:P.mss}, pane, properties:null});
      const ch=l.properties().childs();
      if(ch.linecolor) ch.linecolor.setValue('#2962ff');
      if(ch.text) ch.text.setValue('MSS '+P.mss);
      log('mss ray @ '+P.mss);
    }catch(e){ log('mss ERR '+e.message); }
  }

  await m695.initLineTool('LineToolRectangle');
  try{
    const i0 = findIdx(P.ob_hi, true) ?? lastIdx;
    const l=m.createLineTool({linetool:'LineToolRectangle', point:{index:i0, price:P.ob_hi}, pane, properties:null});
    l.addPoint({index:lastIdx, price:P.ob_lo});
    const ch=l.properties().childs();
    if(ch.linecolor) ch.linecolor.setValue('#26a69a');
    if(ch.backgroundColor) ch.backgroundColor.setValue('rgba(38,166,154,0.15)');
    log('ob rect ok');
  }catch(e){ log('ob ERR '+e.message); }

  await m695.initLineTool('LineToolHorzLine');
  for(const [name,price,color] of [['SL '+P.sl,P.sl,'#ef5350'],['TP '+P.tp,P.tp,'#26a69a'],['ENTRADA '+P.entry,P.entry,'#ffb74d']]){
    try{
      const l=m.createLineTool({linetool:'LineToolHorzLine', point:{index:lastIdx, price}, pane, properties:null});
      const ch=l.properties().childs();
      if(ch.linecolor) ch.linecolor.setValue(color);
      if(ch.text) ch.text.setValue(name);
      log('line '+name);
    }catch(e){ log('line ERR '+name+' '+e.message); }
  }

  await m695.initLineTool('LineToolText');
  try{
    const l=m.createLineTool({linetool:'LineToolText', point:{index:lastIdx, price:(lastClose||P.entry)+35}, pane, properties:null});
    const ch=l.properties().childs();
    if(ch.text) ch.text.setValue(P.checklist);
    if(ch.color) ch.color.setValue('#2196f3');
    if(ch.fontsize) ch.fontsize.setValue(16);
    log('checklist ok');
  }catch(e){ log('text ERR '+e.message); }

  m.fullUpdate && m.fullUpdate();
  await new Promise(r=>setTimeout(r,500));

  const c={rays:0,lines:0,rect:0,path:0,text:0};
  for(const pn of m._panes){ for(const s of pn.dataSources()){
    try{ const n=s.name?s.name():'';
      if(n==='Horizontal ray')c.rays++; else if(n==='Horizontal line')c.lines++;
      else if(n==='Rectangle')c.rect++; else if(n==='Path')c.path++; else if(n==='Text')c.text++;
    }catch(e){}
  }}
  log('COUNTS '+JSON.stringify(c));
  return OUT;
})()
"""
    script = SCRIPT.replace("__PAYLOAD__", json.dumps(payload))
    with open('/tmp/draw_generic_latest.js', 'w') as f: f.write(script)
    res = js(script, ap=True)
    print(json.dumps(res, indent=1, ensure_ascii=False)[:3000])

if __name__ == "__main__":
    main()