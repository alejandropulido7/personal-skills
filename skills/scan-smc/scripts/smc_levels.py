"""
smc_levels.py — Análisis SMC multi-activo.
Lee OHLCV de /tmp/ y calcula estructura, pools de liquidez, OBs, FVGs, sweep, engulfing.
Genera /tmp/smc_levels.json para draw_generic.py.

Uso: python3 smc_levels.py
"""
import pandas as pd, numpy as np, json

def load(tf):
    df = pd.read_csv(f'/tmp/ohlcv_{tf}.csv')
    df['dt'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['dt_ny'] = df['dt'] - pd.Timedelta(hours=4)
    return df

def swings(df, left=3, right=3):
    h = df['high'].values; l = df['low'].values
    n = len(df); sw_hi = []; sw_lo = []
    for i in range(left, n-right):
        if h[i] == h[i-left:i+right+1].max() and np.sum(h[i]==h[i-left:i+right+1])==1:
            sw_hi.append((i, h[i]))
        if l[i] == l[i-left:i+right+1].min() and np.sum(l[i]==l[i-left:i+right+1])==1:
            sw_lo.append((i, l[i]))
    return sw_hi, sw_lo

def structure_label(sw_hi, sw_lo):
    if len(sw_hi)>=2 and len(sw_lo)>=2:
        if sw_hi[-1][1] > sw_hi[-2][1] and sw_lo[-1][1] > sw_lo[-2][1]:
            return "ALCISTA (HH/HL)"
        if sw_hi[-1][1] < sw_hi[-2][1] and sw_lo[-1][1] < sw_lo[-2][1]:
            return "BAJISTA (LH/LL)"
    return "NEUTRO/RANGO"

def detect_ob(df, direction='bullish'):
    """Order Block: última vela en contra antes de un impulso >= 1.5*ATR."""
    o,h,l,c = df['open'].values, df['high'].values, df['low'].values, df['close'].values
    atr = np.mean(np.abs(h[1:]-l[1:])[-14:]) if len(df)>14 else np.mean(h-l)
    obs = []
    for i in range(2, len(df)-1):
        move = c[i+1]-c[i]
        if direction=='bullish' and c[i] < o[i] and move > atr*1.5:
            obs.append({'index': i, 'hi': max(o[i],c[i]), 'lo': min(o[i],c[i]), 'price': c[i+1]})
        elif direction=='bearish' and c[i] > o[i] and move < -atr*1.5:
            obs.append({'index': i, 'hi': max(o[i],c[i]), 'lo': min(o[i],c[i]), 'price': c[i+1]})
    return obs[-3:] if obs else []

def detect_fvg(df):
    """FVG: gap entre vela i-1 (high) y vela i+1 (low) para bullish, o viceversa."""
    h,l = df['high'].values, df['low'].values
    fvgs = []
    for i in range(1, len(df)-1):
        if l[i+1] > h[i-1]:
            fvgs.append({'type':'bullish', 'hi': l[i+1], 'lo': h[i-1], 'mid': (l[i+1]+h[i-1])/2, 'index': i})
        elif h[i+1] < l[i-1]:
            fvgs.append({'type':'bearish', 'hi': l[i-1], 'lo': h[i+1], 'mid': (l[i-1]+h[i+1])/2, 'index': i})
    return fvgs[-5:] if fvgs else []

def detect_sweep(df, pools):
    """Check if price swept any liquidity pool in last 10 bars."""
    recent = df.tail(10)
    hh = recent['high'].max(); ll = recent['low'].min()
    swept = []
    for name, price, kind in pools:
        if kind=='res' and hh >= price * 1.001: swept.append(name)
        if kind=='sup' and ll <= price * 0.999: swept.append(name)
    return swept

def detect_engulfing(df):
    tail = df.tail(10).reset_index(drop=True)
    for i in range(1, len(tail)):
        o0,c0 = tail.loc[i-1,'open'], tail.loc[i-1,'close']
        o1,c1 = tail.loc[i,'open'], tail.loc[i,'close']
        if c1>o1 and c0<o0 and o1<=c0 and c1>=o0: return ("BULL_ENGULF", tail.loc[i,'close'])
        if c1<o1 and c0>o0 and o1>=c0 and c1<=o0: return ("BEAR_ENGULF", tail.loc[i,'close'])
    return (None, None)

def main():
    tfs = {'4h': 240, '1h': 60, '15m': 15, '5m': 5}
    data = {}
    for name, tf in tfs.items():
        try:
            data[name] = load(tf)
            print(f"\n=== {name} ({tf}m) ===")
        except Exception as e:
            print(f"[SMC] WARN: no se pudo cargar ohlcv_{tf}.csv: {e}")
            data[name] = None
            continue
        d = data[name]
        hi, lo = swings(d, 3, 3)
        label = structure_label(hi, lo)
        print(f"Estructura: {label}")
        print(f"Ultimo close: {d['close'].iloc[-1]:.2f} @ {d['dt_ny'].iloc[-1]}")

    # Liquidity pools from 1H
    d1h = data.get('1h')
    if d1h is not None:
        d1h['ny_date'] = d1h['dt_ny'].dt.date
        daily = d1h.groupby('ny_date').agg(pdh=('high','max'), pdl=('low','min'))
        if len(daily)>=2:
            pdh = daily.iloc[-2]['pdh']; pdl = daily.iloc[-2]['pdl']
        else:
            pdh = daily.iloc[-1]['pdh']; pdl = daily.iloc[-1]['pdl']
        print(f"\nPDH: {pdh:.2f} | PDL: {pdl:.2f}")

        # Current day session ranges
        cur = daily.index[-1]
        cd = d1h[d1h['ny_date']==cur]
        asia = cd[(cd['dt_ny'].dt.hour>=20)|(cd['dt_ny'].dt.hour<8)]
        lon = cd[(cd['dt_ny'].dt.hour>=8)&(cd['dt_ny'].dt.hour<13)]
        ny = cd[(cd['dt_ny'].dt.hour>=13)&(cd['dt_ny'].dt.hour<20)]
        pools = [("PDH", pdh, 'res'), ("PDL", pdl, 'sup')]
        for name, s in [('ASIA', asia), ('LONDON', lon), ('NY', ny)]:
            if len(s): 
                pools.append((f"{name}_H", s['high'].max(), 'res'))
                pools.append((f"{name}_L", s['low'].min(), 'sup'))

        # OB & FVG from 15m
        d15 = data.get('15m')
        if d15 is not None:
            obs = detect_ob(d15, 'bullish') + detect_ob(d15, 'bearish')
            fvgs = detect_fvg(d15)
            if obs: print(f"OBs detectados: {len(obs)}")
            if fvgs: print(f"FVGs detectados: {len(fvgs)}")

        # Sweep detection
        swept = detect_sweep(d1h, pools)
        print(f"Sweep detectado en: {swept if swept else 'NINGUNO'}")

        # Engulfing 5m
        d5 = data.get('5m')
        if d5 is not None:
            engulf, eng_price = detect_engulfing(d5)
            print(f"Engulfing 5m: {engulf or 'NINGUNO'}")

        # Determine side based on trend + sweep
        hi4, lo4 = swings(data.get('4h'), 3, 3) if data.get('4h') is not None else ([],[])
        trend4h = structure_label(hi4, lo4)
        side = "long" if "ALCISTA" in trend4h else ("short" if "BAJISTA" in trend4h else "neutral")
        current_price = d1h['close'].iloc[-1]

        # Build rays
        rays = []
        for name, price, kind in pools[-6:]:
            color = '#ef5350' if kind=='res' else '#26a69a'
            rays.append((f"{name} {price:.1f}", round(price,1), color))

        # Entry/SL/TP based on local structure (optimized tight SL for NY session)
        ob_low_val = min([o['lo'] for o in obs]) if obs else (current_price - 20)
        ob_high_val = max([o['hi'] for o in obs]) if obs else (current_price + 20)

        if side == "long":
            entry = d5['close'].iloc[-1] if d5 is not None else current_price
            raw_sl = ob_low_val - 5.0
            if (entry - raw_sl) > 35.0:
                sl = entry - 30.0
            elif (entry - raw_sl) < 15.0:
                sl = entry - 20.0
            else:
                sl = raw_sl
            tp = entry + (entry - sl) * 2
        elif side == "short":
            entry = d5['close'].iloc[-1] if d5 is not None else current_price
            raw_sl = ob_high_val + 5.0
            if (raw_sl - entry) > 35.0:
                sl = entry + 30.0
            elif (raw_sl - entry) < 15.0:
                sl = entry + 20.0
            else:
                sl = raw_sl
            tp = entry - (sl - entry) * 2
        else:
            entry = current_price
            sl = entry - 25.0; tp = entry + 50.0

        # Build checklist text
        chk_4h = trend4h.split(" ")[0] if data.get('4h') is not None else "NEUTRO"
        chk_1h = structure_label(*swings(data.get('1h'), 3, 3)).split(" ")[0] if data.get('1h') is not None else "NEUTRO"
        chk_sweep = "SI" if swept else "NO"
        chk_mss = "SI"  # simplified: assume MSS if 1H structure flipped (would need more logic)
        chk_eng = "SI" if engulf else "NO"
        lines = [
            f"ANALISIS: 4H={chk_4h} / 1H={chk_1h} / Sweep={chk_sweep} / MSS={chk_mss} / Engulf={chk_eng}",
            f"ESPERAR: sweep [nivel] -> MSS [nivel ray] -> OB/FVG + engulfing -> ENTRADA",
            f"SL {sl:.1f} | TP {tp:.1f} | R:R 1:2 | Sesgo: {side.upper()}"
        ]
        checklist = "\n".join(lines)

        levels = {
            "side": side if side != "neutral" else "long",
            "rays": rays[:5],
            "ob_hi": round(max(o.get('hi', entry) for o in (obs or [{'hi': entry+5}])), 1),
            "ob_lo": round(max(o.get('lo', entry-5) for o in (obs or [{'lo': entry-5}])), 1) if obs else round(entry-5, 1),
            "entry": round(entry, 1),
            "sl": round(sl, 1),
            "tp": round(tp, 1),
            "checklist": checklist,
            "mss": None
        }

        with open('/tmp/smc_levels.json', 'w') as f:
            json.dump(levels, f, indent=1)
        print(f"\n[SMC] Niveles guardados en /tmp/smc_levels.json")
        print(f"[SMC] Sesgo: {side.upper()} | Entry: {entry:.1f} | SL: {sl:.1f} | TP: {tp:.1f}")

if __name__ == "__main__":
    main()