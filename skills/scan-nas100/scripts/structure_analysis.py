import pandas as pd, numpy as np, json

def load(tf):
    df = pd.read_csv(f'/tmp/ohlcv_{tf}.csv')
    df['dt'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df['dt_ny'] = df['dt'] - pd.Timedelta(hours=4)  # EDT
    return df

def swings(df, left=3, right=3):
    h = df['high'].values; l = df['low'].values
    n = len(df)
    idx = df.index.tolist()
    swings_hi = []; swings_lo = []
    for i in range(left, n-right):
        win_h = h[i-left:i+right+1]
        win_l = l[i-left:i+right+1]
        if h[i] == win_h.max() and np.sum(h[i]==win_h)==1:
            swings_hi.append((i, h[i]))
        if l[i] == win_l.min() and np.sum(l[i]==win_l)==1:
            swings_lo.append((i, l[i]))
    return swings_hi, swings_lo

def structure_label(sw_hi, sw_lo):
    # returns recent HH/HL or LH/LL pattern
    if len(sw_hi)>=2 and len(sw_lo)>=2:
        last2_hi = sw_hi[-2:]; last2_lo = sw_lo[-2:]
        # check sequence order
        if last2_hi[-1][1] > last2_hi[0][1] and last2_lo[-1][1] > last2_lo[0][1]:
            return "ALCISTA (HH/HL)"
        if last2_hi[-1][1] < last2_hi[0][1] and last2_lo[-1][1] < last2_lo[0][1]:
            return "BAJISTA (LH/LL)"
    return "NEUTRO/RANGO"

for tf in [240,60,15,5]:
    df = load(tf)
    hi, lo = swings(df, 3, 3)
    label = structure_label(hi, lo)
    print(f"\n=== TF {tf}m ===")
    print(f"  Ultimo close: {df['close'].iloc[-1]:.1f}  @ {df['dt_ny'].iloc[-1]}")
    print(f"  Estructura (swings 3/3): {label}")
    print(f"  Ultimos 3 swing highs: {[(df['dt_ny'][i].strftime('%m-%d %H:%M'), round(p,1)) for i,p in hi[-3:]]}")
    print(f"  Ultimos 3 swing lows:  {[(df['dt_ny'][i].strftime('%m-%d %H:%M'), round(p,1)) for i,p in lo[-3:]]}")
