"""
ict_levels.py — Análisis ICT multi-activo (Killzone + OB + FVG + Sweep).
Lee OHLCV de /tmp/ y genera /tmp/ict_levels.json para draw_generic.py.

Uso: python3 ict_levels.py
"""
import pandas as pd, numpy as np, json
from datetime import datetime, timezone, timedelta

def load(tf):
    df = pd.read_csv(f'/tmp/ohlcv_{tf}.csv')
    df['dt'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['dt_et'] = df['dt'] - pd.Timedelta(hours=4)
    return df

def swings(df, left=3, right=3):
    h,l = df['high'].values, df['low'].values
    n = len(df); hi=[]; lo=[]
    for i in range(left, n-right):
        if h[i]==h[i-left:i+right+1].max() and np.sum(h[i]==h[i-left:i+right+1])==1: hi.append((i,h[i]))
        if l[i]==l[i-left:i+right+1].min() and np.sum(l[i]==l[i-left:i+right+1])==1: lo.append((i,l[i]))
    return hi, lo

def structure_label(hi, lo):
    if len(hi)>=2 and len(lo)>=2:
        if hi[-1][1]>hi[-2][1] and lo[-1][1]>lo[-2][1]: return "ALCISTA"
        if hi[-1][1]<hi[-2][1] and lo[-1][1]<lo[-2][1]: return "BAJISTA"
    return "NEUTRO"

def killzone_status():
    """Returns active killzone name or None."""
    now = datetime.now(timezone.utc) - timedelta(hours=4)  # ET
    h = now.hour; m = now.minute
    hm = h + m/60
    if 2 <= hm < 5: return "LONDON_OPEN"
    if 8.5 <= hm < 11: return "NY_AM"
    if 13.5 <= hm < 16: return "NY_PM"
    return None

def detect_fvg(df):
    h,l = df['high'].values, df['low'].values
    fvgs = []
    for i in range(1, len(df)-1):
        if l[i+1] > h[i-1]: fvgs.append({'type':'bullish','hi':l[i+1],'lo':h[i-1],'mid':(l[i+1]+h[i-1])/2,'idx':i})
        elif h[i+1] < l[i-1]: fvgs.append({'type':'bearish','hi':l[i-1],'lo':h[i+1],'mid':(l[i-1]+h[i+1])/2,'idx':i})
    return fvgs[-5:]

def detect_ob(df):
    o,h,l,c = df['open'].values,df['high'].values,df['low'].values,df['close'].values
    atr = float(np.mean(np.abs(h[1:]-l[1:])[-14:])) if len(df)>14 else float(np.mean(h-l))
    obs = []
    for i in range(2, len(df)-1):
        move = c[i+1]-c[i]
        if c[i]<o[i] and move > atr*1.5: obs.append({'idx':i,'hi':max(o[i],c[i]),'lo':min(o[i],c[i]),'type':'bullish'})
        if c[i]>o[i] and move < -atr*1.5: obs.append({'idx':i,'hi':max(o[i],c[i]),'lo':min(o[i],c[i]),'type':'bearish'})
    return obs[-3:]

def main():
    data = {}
    for name, tf in [('1h',60),('15m',15),('5m',5)]:
        try: data[name] = load(tf)
        except: data[name] = None

    d1h = data.get('1h')
    if d1h is None: print("[ICT] ERROR: necesita 1H"); return

    hi, lo = swings(d1h); bias = structure_label(hi, lo)
    print(f"=== ICT Analysis ===")
    print(f"Bias 1H: {bias}")
    kz = killzone_status()
    print(f"Killzone activa: {kz or 'NINGUNA (no operar)'}")

    # Liquidity pools
    d1h['ny_date'] = d1h['dt_et'].dt.date
    daily = d1h.groupby('ny_date').agg(pdh=('high','max'),pdl=('low','min'))
    pdh = float(daily.iloc[-2]['pdh']) if len(daily)>=2 else float(daily.iloc[-1]['pdh'])
    pdl = float(daily.iloc[-2]['pdl']) if len(daily)>=2 else float(daily.iloc[-1]['pdl'])
    print(f"PDH: {pdh:.1f} | PDL: {pdl:.1f}")

    # Sweep detection
    cur = d1h.tail(10)
    swept = []
    if cur['high'].max() >= pdh*1.001: swept.append(("PDH", pdh, 'res'))
    if cur['low'].min() <= pdl*0.999: swept.append(("PDL", pdl, 'sup'))
    print(f"Sweep: {[s[0] for s in swept] or 'NINGUNO'}")

    # FVG + OB from 15m
    d15 = data.get('15m')
    fvgs = detect_fvg(d15) if d15 is not None else []
    obs = detect_ob(d15) if d15 is not None else []
    if fvgs: print(f"FVG(s): {[(f['type'],f['mid']) for f in fvgs[:2]]}")
    if obs: print(f"OB(s): {[(o['type'],o['hi'],o['lo']) for o in obs[:2]]}")

    # Entry levels (tight structural SL for intraday Killzones)
    price = float(d1h['close'].iloc[-1])
    side = 'long' if bias=='ALCISTA' else ('short' if bias=='BAJISTA' else 'neutral')
    if side=='long':
        entry = price
        ob_lo = min([o['lo'] for o in obs]) if obs else (price - 25.0)
        sl = max(ob_lo - 5.0, entry - 35.0)
        if (entry - sl) < 15.0: sl = entry - 20.0
        tp = entry + (entry - sl) * 2
    else:
        entry = price
        ob_hi = max([o['hi'] for o in obs]) if obs else (price + 25.0)
        sl = min(ob_hi + 5.0, entry + 35.0)
        if (sl - entry) < 15.0: sl = entry + 20.0
        tp = entry - (sl - entry) * 2

    rays = [("PDH", round(pdh,1), '#ef5350'), ("PDL", round(pdl,1), '#26a69a')]
    curr_price = float(d1h['close'].iloc[-1])

    chk = f"ICT: Bias={bias} KZ={kz or '-'} Sweep={[s[0] for s in swept] or '-'}"
    chk += f"\nFVG/OB={'SI' if fvgs or obs else 'NO'} | Price={price:.1f}"
    chk += f"\nSL {sl:.1f} | TP {tp:.1f} | R:R 1:2 | Sesgo: {side.upper()}"

    levels = {
        "side": side if side!='neutral' else 'long',
        "rays": rays,
        "ob_hi": round(max([o['hi'] for o in obs]+[price+5])),
        "ob_lo": round(min([o['lo'] for o in obs]+[price-5])),
        "entry": round(entry,1),
        "sl": round(sl,1),
        "tp": round(tp,1),
        "checklist": chk,
        "mss": None
    }
    with open('/tmp/ict_levels.json','w') as f: json.dump(levels, f, indent=1)
    print(f"\n[ICT] Niveles guardados en /tmp/ict_levels.json")

if __name__ == "__main__":
    main()