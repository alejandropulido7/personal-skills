"""
crt_analysis.py — Análisis Candle Range Theory (CRT) para sesión NY.
Lee OHLCV de /tmp/ y genera /tmp/crt_levels.json para draw_generic.py.

CRT: opens fijos (09:30, 11:00, 13:00, 14:30 ET). Cada open forma un rango
de 5 velas 5m. Se detecta manipulación (sweep de un borde) o breakout limpio.

Uso: python3 crt_analysis.py
"""
import pandas as pd, numpy as np, json
from datetime import datetime, timezone, timedelta

def load(tf):
    df = pd.read_csv(f'/tmp/ohlcv_{tf}.csv')
    df['dt'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['dt_et'] = df['dt'] - pd.Timedelta(hours=4)
    return df

def get_current_open_time(now_et):
    """Returns (open_label, open_time_et) for the current CRT open window."""
    opens = [
        ("09:30 OOD", 9, 30),
        ("11:00", 11, 0),
        ("13:00", 13, 0),
        ("14:30", 14, 30),
    ]
    h = now_et.hour; m = now_et.minute
    hm = h * 60 + m
    current = None
    for label, oh, om in opens:
        open_hm = oh * 60 + om
        if hm >= open_hm:
            current = (label, oh, om)
    return current  # (name, hour, minute) or None if before 09:30

def main():
    try:
        d5 = load(5)
        d1h = load(60)
    except Exception as e:
        print(f"[CRT] ERROR: {e}")
        return

    d5['hm'] = d5['dt_et'].dt.strftime('%H:%M')
    d5['ny_date'] = d5['dt_et'].dt.date

    now_et = d5['dt_et'].iloc[-1]
    session_active = (now_et.hour >= 9 and (now_et.hour > 9 or now_et.minute >= 30)) and now_et.hour < 16
    print(f"=== CRT Analysis (NY) ===")
    print(f"Sesión NY: {'ABIERTA' if session_active else 'CERRADA'} ({now_et})")

    if not session_active:
        print("[CRT] Fuera de sesión NY. No operar.")
        return

    open_info = get_current_open_time(now_et)
    if open_info is None:
        print("[CRT] Antes del primer open (09:30 ET). Esperar.")
        return

    open_label, oh, om = open_info
    today = d5['ny_date'].iloc[-1]
    today_bars = d5[d5['ny_date']==today].copy()

    # Find the first 5 bars of 5m after the open time
    open_hm_start = f"{oh:02d}:{om:02d}"
    open_hm_end = f"{oh:02d}:{om+25:02d}" if om+25 < 60 else f"{oh+1:02d}:{om+25-60:02d}"
    open_bars = today_bars[(today_bars['hm'] >= open_hm_start) & (today_bars['hm'] < open_hm_end)]

    print(f"Open actual: {open_label} ({open_hm_start})")
    print(f"Velas en el rango de open (25m): {len(open_bars)}")

    if len(open_bars) < 3:
        print(f"[CRT] Open {open_label}: esperando formación del rango (faltan velas 5m)...")
        chk = f"CRT: Open={open_label}\nEsperando rango de open...\nVelas: {len(open_bars)}/5 necesarias"
        levels = {"side":"long","rays":[["Esperando",0,"#2196f3"]],"ob_hi":0,"ob_lo":0,"entry":0,"sl":0,"tp":0,"checklist":chk,"mss":None}
        with open('/tmp/crt_levels.json','w') as f: json.dump(levels, f, indent=1)
        return

    range_hi = open_bars['high'].max()
    range_lo = open_bars['low'].min()
    mid = (range_hi + range_lo) / 2
    print(f"Rango: H={range_hi:.1f} L={range_lo:.1f} Mid={mid:.1f}")

    # Detect manipulation: price swept one edge and reversed
    after_open = today_bars[today_bars['dt_et'] >= open_bars['dt_et'].iloc[-1]]
    swept_side = None
    manip = False
    eq_target = None
    swept_hi = False
    swept_lo = False

    if len(after_open) < 2:
        print("Esperando velas post-open...")
    else:
        recent_high = after_open['high'].max()
        recent_low = after_open['low'].min()
        swept_hi = recent_high >= range_hi * 1.001
        swept_lo = recent_low <= range_lo * 0.999
        last_close = after_open['close'].iloc[-1]

        # Manipulation: swept an edge AND closed back inside range
        if swept_hi and last_close < range_hi:
            swept_side = "HIGH"; manip = True; eq_target = range_lo
            print(f"Manipulación HIGH → equalización a LOW ({range_lo:.1f})")
        elif swept_lo and last_close > range_lo:
            swept_side = "LOW"; manip = True; eq_target = range_hi
            print(f"Manipulación LOW → equalización a HIGH ({range_hi:.1f})")
        else:
            swept_side = None; manip = False; eq_target = None
            # Check breakout
            if swept_hi and last_close >= range_hi:
                print(f"Breakout HIGH (no manip) — dirección LONG")
            elif swept_lo and last_close <= range_lo:
                print(f"Breakout LOW (no manip) — dirección SHORT")
            else:
                print(f"Sin manipulación ni breakout claro. Precio dentro del rango.")

    # Build levels
    side = "long" if (manip and eq_target == range_lo) or (not manip and swept_hi) else "short" if (manip and eq_target == range_hi) or (not manip and swept_lo) else "neutral"
    if side == "neutral":
        side = "long" if (range_hi - mid) > (mid - range_lo) else "short"

    entry = after_open['close'].iloc[-1] if len(after_open) else mid
    if manip:
        raw_sl = (recent_high + 5.0) if swept_side == "HIGH" else (recent_low - 5.0)
        sl = min(raw_sl, entry + 30.0) if swept_side == "HIGH" else max(raw_sl, entry - 30.0)
        if abs(entry - sl) < 15.0: sl = entry + 20.0 if swept_side == "HIGH" else entry - 20.0
        tp = eq_target if eq_target else (entry + (entry-sl)*2 if 'long' in side else entry - (sl-entry)*2)
    else:
        raw_sl = range_lo - 5.0 if side == "long" else range_hi + 5.0
        sl = max(raw_sl, entry - 30.0) if side == "long" else min(raw_sl, entry + 30.0)
        if abs(entry - sl) < 15.0: sl = entry - 20.0 if side == "long" else entry + 20.0
        tp = entry + (entry-sl)*2 if side == "long" else entry - (sl-entry)*2

    rays = [
        (f"RNG_H {range_hi:.1f}", round(range_hi,1), '#ef5350'),
        (f"RNG_L {range_lo:.1f}", round(range_lo,1), '#26a69a'),
    ]
    if manip:
        rays.append((f"EQ_TARGET {eq_target:.1f}", round(eq_target,1), '#2962ff'))

    chk = f"CRT: Open={open_label} | {(manip and 'MANIP '+swept_side) or 'ESPERANDO'}"
    chk += f"\nRango: H={range_hi:.1f} L={range_lo:.1f}"
    chk += f"\n{'Equalizacion->'+str(round(eq_target,1)) if manip else 'Sin setup claro'}"
    chk += f"\nSL {sl:.1f} | TP {tp:.1f} | Sesgo: {side.upper()}"

    levels = {
        "side": side if side!='neutral' else 'long',
        "rays": rays,
        "ob_hi": round(range_hi,1),
        "ob_lo": round(range_lo,1),
        "entry": round(entry,1),
        "sl": round(sl,1),
        "tp": round(tp,1),
        "checklist": chk,
        "mss": None
    }
    with open('/tmp/crt_levels.json','w') as f: json.dump(levels, f, indent=1)
    print(f"\n[CRT] Niveles guardados en /tmp/crt_levels.json")

if __name__ == "__main__":
    main()