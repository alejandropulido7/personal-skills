"""
draw_all.py — Rutina completa de dibujo SMC para NAS100 (scan_nas100).
Guarda en tradingview-drawings/scripts/. Uso:
  python3 draw_all.py [--symbol CAPITALCOM:NAS100] [--res 60] [--side long|short] [--mss 30180.0] [--text "<checklist>"]
Con CAPITALCOM:NAS100 los dibujos SÍ se guardan en el layout (visible en movil).
Crea (en la resolucion indicada, por defecto 1H):
  - 3 rays S/R anclados a la vela que genero cada nivel (NY LOW, LONDON LOW, PDH/PDL)
  - 1 ray extra OPCIONAL con el nivel MSS que se espera romper (--mss <precio>)
  - rectangulo Order Block
  - lineas SL / TP / ENTRADA
  - 1 texto checklist (azul #2196f3, tamano 16, una regla por linea, emojis ✅/🟠)
NO dibuja LineToolPath (prohibido: rompe el grafico).
Selecciona los 3 niveles clave segun la direccion del trade pasada con --side long|short.
NOTA de persistencia: TradingView guarda los dibujos por simbolo en el layout. En
PEPPERSTONE:NAS100 los dibujos inyectados NO persistian; en CAPITALCOM:NAS100 SI (verificado
2026-08-13). Usar siempre el símbolo capitalcom para que el scan sea persistente.
"""
import json, os, sys, time, websocket, urllib.request

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
def raw_js(e, ap=False):
    return call("Runtime.evaluate", {"expression": e, "returnByValue": True, "awaitPromise": ap})

def js(e, ap=False):
    r = raw_js(e, ap)
    # surface exception details if any
    if "exceptionDetails" in r.get("result", {}):
        return {"__js_err__": r["result"]["exceptionDetails"].get("text","")}
    res = r.get("result", {}).get("result", {})
    if "exceptionDetails" in res: return {"__js_err__": res["exceptionDetails"].get("text","")}
    if "value" in res: return res["value"]
    return {"__desc__": res.get("description","")}

def main():
    side = "long"
    symbol = None   # None -> auto-detect from watchlist (CAPITALCOM:NAS100, etc.)
    resolution = "60"
    checklist = None
    mss_level = None   # nivel MSS esperado -> se dibuja como horizontal ray adicional
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--side" and i+1 < len(args): side = args[i+1]; i += 2
        elif args[i] == "--text" and i+1 < len(args): checklist = args[i+1]; i += 2
        elif args[i] == "--symbol" and i+1 < len(args): symbol = args[i+1]; i += 2
        elif args[i] == "--res" and i+1 < len(args): resolution = args[i+1]; i += 2
        elif args[i] == "--mss" and i+1 < len(args):
            mss_level = float(args[i+1]); i += 2
        else: i += 1

    # AUTO-DETECT symbol from the watchlist if not provided (independent of broker).
    # Real detection happens INSIDE the JS (avoids a second CDP connection that can
    # disturb the session). Here we only default it for the JS fallback.
    if symbol is None:
        symbol = "CAPITALCOM:NAS100"  # fallback; JS will auto-detect from watchlist

    # levels per side (optimized tight 25-35pt SL for intraday NY session)
    if side == "short":
        rays = [
            ("ASIA HIGH 29765", 29764.9, '#ef5350'),
            ("NY HIGH 29818",   29818.4, '#ef5350'),
            ("PDL 29421",       29421.2, '#26a69a'),
        ]
        ob_hi, ob_lo = 29818.4, 29795.9
        entry, sl, tp = 29805.0, 29835.0, 29745.0
    else:
        rays = [
            ("ASIA LOW 30028",   30027.5, '#26a69a'),
            ("LONDON LOW 30070", 30070.4, '#26a69a'),
            ("PDH 30170",        30169.6, '#ef5350'),
        ]
        ob_hi, ob_lo = 30081.4, 30055.0
        entry, sl, tp = 30090.0, 30060.0, 30150.0

    if checklist is None:
        checklist = (
            "ANALISIS: Tend4H=✅/🟠 / 1H=✅/🟠 / NY=✅/🟠\n"
            "Sweep=✅/🟠 / MSS=✅/🟠 / Engulf5m=✅/🟠\n"
            "ESPERAR: sweep [nivel] -> MSS [ray] -> engulfing 5m\n"
            "ENTRADA: al cierre engulfing 5m (solo market order)\n"
            "R:R 1:2 | SL [nivel] | TP [nivel] | Sesgo: [LONG/SHORT/ESPERAR]"
        )

    # REGLA DE COHERENCIA DE NIVELES (yaml entry_rules.level_coherence_rule):
    # LONG: Entrada > MSS (entrada por encima del nivel MSS a romper)
    # SHORT: Entrada < MSS (entrada por debajo del nivel MSS a romper)
    if mss_level is not None:
        if side == "long" and entry <= mss_level:
            print(f"⚠️  INCOHERENCIA: LONG con ENTRADA {entry} <= MSS {mss_level}. "
                  f"Recalculando Entrada = MSS + buffer (por encima del MSS).")
            entry = mss_level + 9.0
        elif side == "short" and entry >= mss_level:
            print(f"⚠️  INCOHERENCIA: SHORT con ENTRADA {entry} >= MSS {mss_level}. "
                  f"Recalculando Entrada = MSS - buffer (por debajo del MSS).")
            entry = mss_level - 9.0

    payload = {
        "rays": rays, "ob_hi": ob_hi, "ob_lo": ob_lo,
        "entry": entry, "sl": sl, "tp": tp, "checklist": checklist,
        "symbol": symbol, "resolution": resolution, "mss": mss_level,
    }
    script = r"""
(async()=>{
  window.webpackChunktradingview.push([['__probe__'], {}, (r) => { window.__req = r; }]);
  const P = __PAYLOAD__;
  const w = _exposed_chartWidgetCollection.activeChartWidget.value();
  const m = w._modelWV.value().m_model;
  const pane = m._panes[0];
  const OUT = [];
  const log = (x)=>OUT.push(x);

  // 0) AUTO-DETECT symbol from watchlist if P.symbol is the fallback marker.
  //    Opens the watchlist panel, reads data-symbol-full for 'NAS100', and uses it.
  let targetSymbol = P.symbol;
  try{
    // click watchlist button if panel closed
    (function(){
      const all=document.querySelectorAll('button');
      for(const el of all){
        const aria=(el.getAttribute('aria-label')||'').trim();
        if(/Lista de seguimiento/.test(aria)){ el.click(); return; }
      }
    })();
    // small wait for the panel
    await new Promise(r=>setTimeout(r, 1200));
    // read rows
    let found=[];
    for(let attempt=0; attempt<4 && found.length===0; attempt++){
      const rows=document.querySelectorAll('[data-symbol-full]');
      for(const r of rows){
        const short=(r.getAttribute('data-symbol-short')||'').toUpperCase();
        if(short==='NAS100'){
          found.push({full:r.getAttribute('data-symbol-full'), active:r.getAttribute('data-active')==='true'});
        }
      }
      if(found.length===0){ await new Promise(r=>setTimeout(r, 1500)); }
    }
    if(found.length){
      const best = found.find(x=>x.active) || found[0];
      targetSymbol = best.full;
      log('auto-detect symbol: '+targetSymbol);
    } else {
      log('WARN: NAS100 no encontrado en watchlist, usando '+targetSymbol);
    }
  }catch(e){ log('detect ERR '+e.message); }

  // 0b) NAVIGATE to target symbol + resolution (so drawings persist on the right symbol)
  try{
    const cur = await w.getSymbol();
    if(String(cur).toUpperCase() !== String(targetSymbol).toUpperCase()){
      await w.setSymbol(targetSymbol);
      log('nav symbol -> '+targetSymbol);
      await new Promise(r=>setTimeout(r, 3500));
    } else { log('symbol already '+cur); }
    const res = w._resolutionWV.value();
    if(String(res) !== String(P.resolution)){
      await w.setResolution(String(P.resolution));
      log('nav res -> '+P.resolution);
      await new Promise(r=>setTimeout(r, 2500));
    } else { log('res already '+res); }
  }catch(e){ log('nav ERR '+e.message); }

  const bars = pane.dataSources()[0].bars();

  // find index of the generating candle for each level price (first bar whose high/low matches)
  function findIdx(price, isRes){
    for(let i=0;i<bars.size();i++){
      const v=bars.valueAt(i); if(!v) continue;
      if(isRes && Math.abs(v[2]-price)<0.5) return i;  // high
      if(!isRes && Math.abs(v[3]-price)<0.5) return i; // low
    }
    return null;
  }
  const last = bars.last();
  const lastIdx = last ? last.index : 299;
  const lastClose = last ? last.value[4] : null;

  // 1) CLEAR drawings (two-pass)
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

  // 2) rays
  await m695.initLineTool('LineToolHorzRay');
  for(const [name, price, color] of P.rays){
    try{
      const idx = findIdx(price, color==='#ef5350');
      if(idx===null){ log('ray '+name+' no bar found'); continue; }
      const l=m.createLineTool({linetool:'LineToolHorzRay', point:{index:idx, price}, pane, properties:null});
      const ch=l.properties().childs();
      ch.linecolor && ch.linecolor.setValue(color);
      if(ch.text) ch.text.setValue(name);
      log('ray '+name+' @idx '+idx);
    }catch(e){ log('ray ERR '+name+' '+e.message); }
  }

  // 2b) MSS ray extra (nivel que se espera romper) — opcional
  if(P.mss !== null && P.mss !== undefined){
    try{
      const idx = findIdx(P.mss, true) ?? findIdx(P.mss, false) ?? lastIdx;
      const l=m.createLineTool({linetool:'LineToolHorzRay', point:{index:idx, price:P.mss}, pane, properties:null});
      const ch=l.properties().childs();
      ch.linecolor && ch.linecolor.setValue('#2962ff');
      if(ch.text) ch.text.setValue('MSS '+P.mss);
      log('mss ray @ '+P.mss);
    }catch(e){ log('mss ray ERR '+e.message); }
  }

  // 3) OB rectangle
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

  // 4) SL/TP/ENTRADA lines
  await m695.initLineTool('LineToolHorzLine');
  const lines=[
    ['SL '+P.sl,   P.sl,   '#ef5350'],
    ['TP '+P.tp,   P.tp,   '#26a69a'],
    ['ENTRADA '+P.entry, P.entry, '#ffb74d'],
  ];
  for(const [name,price,color] of lines){
    try{
      const l=m.createLineTool({linetool:'LineToolHorzLine', point:{index:lastIdx, price}, pane, properties:null});
      const ch=l.properties().childs();
      ch.linecolor && ch.linecolor.setValue(color);
      if(ch.text) ch.text.setValue(name);
      log('line '+name);
    }catch(e){ log('line ERR '+e.message); }
  }

  // NO LineToolPath (prohibido: rompe el grafico). Toda referencia visual = ray/line.

  // 5) checklist single text (blue, 16)
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

  // verify counts
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
    script = script.replace("__PAYLOAD__", json.dumps(payload))
    res = js(script, ap=True)
    print(json.dumps(res, indent=1, ensure_ascii=False)[:3000])

if __name__ == "__main__":
    main()
