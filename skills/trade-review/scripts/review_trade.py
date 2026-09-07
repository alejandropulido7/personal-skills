#!/usr/bin/env python3
"""
review_trade.py — Rutina de revisión posterior (post-mortem) de operaciones de trading.
Analiza la trayectoria del precio a partir del archivo de niveles (/tmp/nas100_levels.json)
o argumentos CLI, calcula MFE, MAE, estado del trade (WIN/LOSS/OPEN/NO_TRIGGER) y
opcionalmente actualiza el gráfico en TradingView Desktop.

Uso:
  python3 review_trade.py [--levels /tmp/nas100_levels.json] [--draw]
  python3 review_trade.py --side long --entry 29105 --sl 29075 --tp 29165 [--draw]
"""
import sys, os, json, time
import pandas as pd
import numpy as np

def load_ohlcv(tf=5):
    path = f"/tmp/ohlcv_{tf}.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró el archivo de OHLCV: {path}")
    df = pd.read_csv(path)
    df['dt'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['dt_ny'] = df['dt'] - pd.Timedelta(hours=4)
    return df

def parse_args():
    levels_file = "/tmp/nas100_levels.json"
    side = None
    entry = None
    sl = None
    tp = None
    mss = None
    draw = False
    start_time_str = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--levels" and i + 1 < len(args):
            levels_file = args[i + 1]; i += 2
        elif args[i] == "--side" and i + 1 < len(args):
            side = args[i + 1].lower(); i += 2
        elif args[i] == "--entry" and i + 1 < len(args):
            entry = float(args[i + 1]); i += 2
        elif args[i] == "--sl" and i + 1 < len(args):
            sl = float(args[i + 1]); i += 2
        elif args[i] == "--tp" and i + 1 < len(args):
            tp = float(args[i + 1]); i += 2
        elif args[i] == "--mss" and i + 1 < len(args):
            mss = float(args[i + 1]); i += 2
        elif args[i] == "--start" and i + 1 < len(args):
            start_time_str = args[i + 1]; i += 2
        elif args[i] == "--draw":
            draw = True; i += 1
        else:
            i += 1

    if (entry is None or sl is None or tp is None) and os.path.exists(levels_file):
        with open(levels_file, 'r') as f:
            L = json.load(f)
            side = side or L.get("side", "long").lower()
            entry = entry or float(L.get("entry", 0))
            sl = sl or float(L.get("sl", 0))
            tp = tp or float(L.get("tp", 0))
            mss = mss or (float(L.get("mss")) if L.get("mss") is not None else None)

    return {
        "side": side or "long",
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "mss": mss,
        "draw": draw,
        "start_time_str": start_time_str
    }

def analyze_trade(df, side, entry, sl, tp, mss=None, start_time_str=None):
    if entry is None or sl is None or tp is None or entry == 0:
        return {"error": "Niveles de entrada, SL o TP no válidos."}

    risk = abs(entry - sl)
    reward = abs(tp - entry)
    rr_target = reward / risk if risk > 0 else 0

    # Filter by start time if provided, or default to today's NY session open (09:30 EDT)
    today = df['dt_ny'].dt.date.iloc[-1]
    if start_time_str:
        start_dt = pd.to_datetime(start_time_str)
        if start_dt.tzinfo is None:
            start_dt = start_dt.tz_localize('UTC')
        df_eval = df[df['dt_ny'] >= start_dt].copy()
    else:
        # Default: from today 09:30 EDT onwards
        today_ny_open = pd.to_datetime(f"{today} 09:30:00").tz_localize('UTC')
        df_eval = df[df['dt_ny'] >= today_ny_open].copy()
        if len(df_eval) == 0:
            df_eval = df[df['dt_ny'].dt.date == today].copy()

    if len(df_eval) == 0:
        return {"error": "No hay velas en el rango de evaluación seleccionado."}

    triggered = False
    trigger_idx = None
    trigger_time = None
    outcome = "NOT_TRIGGERED"
    exit_price = None
    exit_time = None
    exit_reason = None
    duration_bars = 0
    duration_minutes = 0

    max_fav = 0.0
    max_adv = 0.0

    # Step 1: Detect activation
    for i, (_, row) in enumerate(df_eval.iterrows()):
        h, l, c, o = row['high'], row['low'], row['close'], row['open']
        t = row['dt_ny']

        if not triggered:
            # Condition to trigger: reversal candle closing across MSS / Entry level
            if side == "long":
                # Must close above MSS (or entry) with bullish body
                trigger_level = mss if (mss is not None and mss > 0) else entry
                if c >= trigger_level and c >= o and (i > 0 or h >= entry):
                    triggered = True
                    trigger_idx = i
                    trigger_time = t
            elif side == "short":
                # Must close below MSS (or entry) with bearish body
                trigger_level = mss if (mss is not None and mss > 0) else entry
                if c <= trigger_level and c <= o and (i > 0 or l <= entry):
                    triggered = True
                    trigger_idx = i
                    trigger_time = t

        if triggered:
            duration_bars += 1
            # Track excursions
            if side == "long":
                fav = h - entry
                adv = entry - l
                if fav > max_fav: max_fav = fav
                if adv > max_adv: max_adv = adv

                # Check SL and TP
                hit_sl = l <= sl
                hit_tp = h >= tp

                if hit_tp and not hit_sl:
                    outcome = "TP_HIT"
                    exit_price = tp
                    exit_time = t
                    exit_reason = f"Target Profit alcanzado (+{reward:.1f} pts)"
                    break
                elif hit_sl and not hit_tp:
                    outcome = "SL_HIT"
                    exit_price = sl
                    exit_time = t
                    exit_reason = f"Stop Loss tocado (-{risk:.1f} pts)"
                    break
                elif hit_sl and hit_tp:
                    # In same bar: conservative assumes SL or checks bar direction
                    if c >= o:
                        outcome = "TP_HIT"; exit_price = tp; exit_time = t; exit_reason = "TP alcanzado en vela alcista"
                    else:
                        outcome = "SL_HIT"; exit_price = sl; exit_time = t; exit_reason = "SL tocado en vela bajista"
                    break
            elif side == "short":
                fav = entry - l
                adv = h - entry
                if fav > max_fav: max_fav = fav
                if adv > max_adv: max_adv = adv

                hit_sl = h >= sl
                hit_tp = l <= tp

                if hit_tp and not hit_sl:
                    outcome = "TP_HIT"
                    exit_price = tp
                    exit_time = t
                    exit_reason = f"Target Profit alcanzado (+{reward:.1f} pts)"
                    break
                elif hit_sl and not hit_tp:
                    outcome = "SL_HIT"
                    exit_price = sl
                    exit_time = t
                    exit_reason = f"Stop Loss tocado (-{risk:.1f} pts)"
                    break
                elif hit_sl and hit_tp:
                    if c <= o:
                        outcome = "TP_HIT"; exit_price = tp; exit_time = t; exit_reason = "TP alcanzado en vela bajista"
                    else:
                        outcome = "SL_HIT"; exit_price = sl; exit_time = t; exit_reason = "SL tocado en vela alcista"
                    break

    current_price = df_eval['close'].iloc[-1]
    current_time = df_eval['dt_ny'].iloc[-1]
    duration_minutes = duration_bars * 5

    if triggered and outcome == "NOT_TRIGGERED":
        outcome = "OPEN"
        exit_price = current_price
        exit_time = current_time
        cur_pnl = (current_price - entry) if side == "long" else (entry - current_price)
        cur_r = cur_pnl / risk if risk > 0 else 0
        exit_reason = f"Trade en curso ({cur_pnl:+.1f} pts | {cur_r:+.2f}R)"

    mfe_r = max_fav / risk if risk > 0 else 0
    mae_r = max_adv / risk if risk > 0 else 0

    if outcome == "TP_HIT":
        pnl_pts = reward
        realized_r = rr_target
    elif outcome == "SL_HIT":
        pnl_pts = -risk
        realized_r = -1.0
    elif outcome == "OPEN":
        pnl_pts = (current_price - entry) if side == "long" else (entry - current_price)
        realized_r = pnl_pts / risk if risk > 0 else 0
    else:
        pnl_pts = 0.0
        realized_r = 0.0

    return {
        "side": side.upper(),
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "risk_pts": round(risk, 1),
        "reward_pts": round(reward, 1),
        "rr_target": round(rr_target, 2),
        "triggered": triggered,
        "trigger_time": trigger_time.strftime("%Y-%m-%d %H:%M EDT") if trigger_time is not None else "No activado",
        "outcome": outcome,
        "exit_price": round(exit_price, 1) if exit_price is not None else None,
        "exit_time": exit_time.strftime("%Y-%m-%d %H:%M EDT") if exit_time is not None else None,
        "exit_reason": exit_reason,
        "pnl_pts": round(pnl_pts, 1),
        "realized_r": round(realized_r, 2),
        "mfe_pts": round(max_fav, 1),
        "mfe_r": round(mfe_r, 2),
        "mae_pts": round(max_adv, 1),
        "mae_r": round(mae_r, 2),
        "duration_bars": duration_bars,
        "duration_minutes": duration_minutes,
        "current_price": round(current_price, 1),
        "current_time": current_time.strftime("%Y-%m-%d %H:%M EDT")
    }

def draw_review_on_chart(res):
    try:
        import websocket, urllib.request
        pages = json.load(urllib.request.urlopen("http://localhost:9222/json", timeout=3))
        ws_url = next(p["webSocketDebuggerUrl"] for p in pages if p.get("type")=="page" and "tradingview.com/chart" in p.get("url",""))
        ws = websocket.create_connection(ws_url, timeout=10, suppress_origin=True)

        mid = 0
        def call(m, p=None):
            nonlocal mid; mid += 1
            ws.send(json.dumps({"id": mid, "method": m, "params": p or {}}))
            while True:
                r = json.loads(ws.recv())
                if r.get("id") == mid: return r

        badge_text = f"📊 REVISION TRADE: {res['outcome']} ({res['realized_r']:+.2f}R)\n"
        badge_text += f"PnL: {res['pnl_pts']:+.1f} pts | MFE: {res['mfe_r']:.2f}R | MAE: {res['mae_r']:.2f}R\n"
        badge_text += f"Estado: {res['exit_reason']} ({res['duration_minutes']} min)"

        color = '#26a69a' if 'TP' in res['outcome'] or res['realized_r'] > 0 else ('#ef5350' if 'SL' in res['outcome'] else '#ffb74d')

        payload = {"text": badge_text, "color": color, "price": res['entry'] + 20.0}
        js_code = f"""
(async()=>{{
  const w = _exposed_chartWidgetCollection.activeChartWidget.value();
  const m = w._modelWV.value().m_model;
  const pane = m._panes[0];
  const last = pane.dataSources()[0].bars().last();
  const idx = last ? last.index : 299;
  
  window.webpackChunktradingview.push([['__probe__'], {{}}, (r) => {{ window.__req = r; }}]);
  const m695 = window.__req(695211);
  await m695.initLineTool('LineToolText');
  const l = m.createLineTool({{linetool:'LineToolText', point:{{index:idx, price:{payload['price']}}}, pane, properties:null}});
  const ch = l.properties().childs();
  if(ch.text) ch.text.setValue({json.dumps(payload['text'])});
  if(ch.color) ch.color.setValue('{payload['color']}');
  if(ch.fontsize) ch.fontsize.setValue(14);
  m.fullUpdate && m.fullUpdate();
  return 'badge drawn';
}})()
"""
        call("Runtime.evaluate", {"expression": js_code, "returnByValue": True, "awaitPromise": True})
        print("  [CDP] Badge de revisión trazado en el gráfico de TradingView.")
    except Exception as e:
        print(f"  [CDP Info] No se pudo inyectar el badge directo: {e}")

def print_report(r):
    print("\n" + "="*60)
    print("       📋 REPORTE DE REVISIÓN POSTERIOR DE TRADE")
    print("="*60)
    print(f"  Dirección / Sesgo : {r['side']}")
    print(f"  Entrada           : {r['entry']}")
    print(f"  Stop Loss         : {r['sl']} (Riesgo: {r['risk_pts']} pts)")
    print(f"  Take Profit       : {r['tp']} (Recompensa: {r['reward_pts']} pts)")
    print(f"  Target R:R        : 1:{r['rr_target']}")
    print("-" * 60)
    print(f"  Activación        : {'✅ ACTIVADO' if r['triggered'] else '❌ NO ACTIVADO'}")
    print(f"  Hora de Gatillo   : {r['trigger_time']}")
    print(f"  Resultado         : 🏆 {r['outcome']}" if r['outcome']=='TP_HIT' else (f"  Resultado         : 🛑 {r['outcome']}" if r['outcome']=='SL_HIT' else f"  Resultado         : ⏳ {r['outcome']}"))
    print(f"  Detalle de Cierre : {r['exit_reason']}")
    print(f"  PnL en Puntos     : {r['pnl_pts']:+.1f} pts")
    print(f"  R:R Realizado     : {r['realized_r']:+.2f}R")
    print("-" * 60)
    print(f"  MFE (Max Favor)   : +{r['mfe_pts']:.1f} pts (+{r['mfe_r']:.2f}R)")
    print(f"  MAE (Max Drawdown): -{r['mae_pts']:.1f} pts (-{r['mae_r']:.2f}R)")
    print(f"  Duración          : {r['duration_bars']} velas 5m ({r['duration_minutes']} min)")
    print(f"  Precio Actual     : {r['current_price']} @ {r['current_time']}")
    print("="*60 + "\n")

def main():
    args = parse_args()
    try:
        df = load_ohlcv(5)
    except Exception as e:
        print(f"[ERROR] {e}")
        return

    res = analyze_trade(df, args['side'], args['entry'], args['sl'], args['tp'], args['mss'], args['start_time_str'])
    if "error" in res:
        print(f"[ERROR] {res['error']}")
        return

    with open('/tmp/trade_review_result.json', 'w') as f:
        json.dump(res, f, indent=2)

    print_report(res)

    if args['draw']:
        draw_review_on_chart(res)

if __name__ == "__main__":
    main()
