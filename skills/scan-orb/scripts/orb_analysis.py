"""
orb_analysis.py — Análisis ORB (Opening Range Breakout) para sesión NY.
Lee OHLCV de /tmp/ y genera /tmp/orb_levels.json para draw_generic.py.

Uso: python3 orb_analysis.py
"""
import pandas as pd, numpy as np, json

def load(tf):
    df = pd.read_csv(f'/tmp/ohlcv_{tf}.csv')
    df['dt'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['dt_et'] = df['dt'] - pd.Timedelta(hours=4)
    return df

def main():
    try:
        d5 = load(5)
        d1h = load(60)
    except Exception as e:
        print(f"[ORB] ERROR: {e}")
        return

    d5['hm'] = d5['dt_et'].dt.strftime('%H:%M')
    d5['ny_date'] = d5['dt_et'].dt.date

    # Session check
    now_et = d5['dt_et'].iloc[-1]
    session_open = now_et.hour >= 9 and (now_et.hour > 9 or now_et.minute >= 30)
    session_close = now_et.hour < 16
    session_active = session_open and session_close
    print(f"=== ORB Analysis ===")
    print(f"Sesión NY: {'ABIERTA' if session_active else 'CERRADA'} ({now_et})")

    if not session_active:
        print("[ORB] Fuera de sesión NY (09:30-16:00 ET). No operar.")
        return

    # Current NY day data
    today = d5['ny_date'].iloc[-1]
    today_bars = d5[d5['ny_date']==today].copy()

    # ORB range: first 15 min (09:30-09:45) or first 30 min (09:30-10:00)
    orb_15 = today_bars[(today_bars['hm']>='09:30') & (today_bars['hm']<'09:45')]
    orb_30 = today_bars[(today_bars['hm']>='09:30') & (today_bars['hm']<'10:00')]

    if len(orb_15) < 2:
        print("[ORB] Esperando formación del rango ORB (09:30-09:45)...")
        level_file = {
            "side": "long", "rays": [["ORB H esperando", 0, '#ef5350'], ["ORB L esperando", 0, '#26a69a']],
            "ob_hi": 0, "ob_lo": 0, "entry": 0, "sl": 0, "tp": 0,
            "checklist": "ORB no formado aun\nEsperar 09:45 ET para el rango\nSesión NY ABIERTA",
            "mss": None
        }
        with open('/tmp/orb_levels.json','w') as f: json.dump(level_file, f, indent=1)
        return

    orb_h = orb_15['high'].max()
    orb_l = orb_15['low'].min()
    print(f"ORB (09:30-09:45): H={orb_h:.1f} L={orb_l:.1f}")

    # Also check 30-min range 
    if len(orb_30) >= 3:
        print(f"ORB (09:30-10:00): H={orb_30['high'].max():.1f} L={orb_30['low'].min():.1f}")

    # VWAP-like reference: EMA of 1H
    d1h['ema20'] = d1h['close'].ewm(span=20).mean()
    ema20 = d1h['ema20'].iloc[-1]
    print(f"EMA20 1H: {ema20:.1f}")

    # Volume confirmation
    recent = today_bars.tail(20)
    avg_vol = recent['volume'].mean() if 'volume' in recent.columns else 100
    last_vol = recent['volume'].iloc[-1] if 'volume' in recent.columns else 0
    vol_ratio = last_vol / avg_vol if avg_vol > 0 else 1
    print(f"Volumen: último={last_vol:.0f} media20={avg_vol:.0f} ratio={vol_ratio:.1f}x")

    # Breakout detection
    last_close = today_bars['close'].iloc[-1]
    breakout_long = last_close > orb_h
    breakout_short = last_close < orb_l

    # Determine side
    hi1h, lo1h = [], []
    side = "long" if breakout_long else ("short" if breakout_short else "neutral")

    if breakout_long:
        print("BREAKOUT LONG detectado")
    elif breakout_short:
        print("BREAKOUT SHORT detectado")
    else:
        print("Sin breakout: precio dentro del rango ORB")

    # Entry/SL/TP (tightened for intraday execution)
    if side == "long":
        entry = last_close
        raw_sl = orb_l - 5.0
        sl = max(raw_sl, entry - 30.0)
        if (entry - sl) < 15.0: sl = entry - 20.0
        tp = entry + (entry - sl) * 2
    elif side == "short":
        entry = last_close
        raw_sl = orb_h + 5.0
        sl = min(raw_sl, entry + 30.0)
        if (sl - entry) < 15.0: sl = entry + 20.0
        tp = entry - (sl - entry) * 2
    else:
        entry = (orb_h + orb_l) / 2
        sl = entry - 20.0
        tp = entry + 40.0

    # Volume filter
    vol_ok = vol_ratio >= 1.5

    rays = [
        (f"ORB_H {orb_h:.1f}", round(orb_h,1), '#ef5350'),
        (f"ORB_L {orb_l:.1f}", round(orb_l,1), '#26a69a'),
        (f"EMA20 {ema20:.1f}", round(ema20,1), '#2962ff'),
    ]

    chk = f"ORB: NY={'ABIERTA' if session_active else 'CERRADA'} H={orb_h:.1f} L={orb_l:.1f}"
    chk += f"\nBreakout: {'LONG' if breakout_long else ('SHORT' if breakout_short else 'NO')}"
    chk += f"\nVol={vol_ratio:.1f}x {'✅' if vol_ok else ''}"
    chk += f"\nSL {sl:.1f} | TP {tp:.1f} | R:R 1:2 | Sesgo: {side.upper()}"

    levels = {
        "side": side if side!='neutral' else 'long',
        "rays": rays,
        "ob_hi": round(orb_h,1),
        "ob_lo": round(orb_l,1),
        "entry": round(entry,1),
        "sl": round(sl,1),
        "tp": round(tp,1),
        "checklist": chk,
        "mss": None
    }
    with open('/tmp/orb_levels.json','w') as f: json.dump(levels, f, indent=1)
    print(f"\n[ORB] Niveles guardados en /tmp/orb_levels.json")

if __name__ == "__main__":
    main()