import pandas as pd, numpy as np

df = pd.read_csv('/tmp/ohlcv_5.csv')
df['dt'] = pd.to_datetime(df['time'], unit='s', utc=True)
df['dt_ny'] = df['dt'] - pd.Timedelta(hours=4)

# Show last 40 5m bars compactly
tail = df.tail(40).copy()
print("=== Últimas 40 velas 5m (NY time) ===")
for _, r in tail.iterrows():
    body = r['close']-r['open']
    dirn = '▲' if body>0 else ('▼' if body<0 else '·')
    print(f"{r['dt_ny'].strftime('%m-%d %H:%M')} O{r['open']:.1f} H{r['high']:.1f} L{r['low']:.1f} C{r['close']:.1f} {dirn}")

# Engulfing detection (5m): bullish engulfing = current body engulfs prev body with close>open
print("\n=== Detección vela envolvente (5m) últimas 10 velas ===")
vals = tail.reset_index(drop=True)
for i in range(1, len(vals)):
    o0,c0 = vals.loc[i-1,'open'], vals.loc[i-1,'close']
    o1,c1 = vals.loc[i,'open'], vals.loc[i,'close']
    bull_engulf = c1>o1 and c0<o0 and o1<=c0 and c1>=o0
    bear_engulf = c1<o1 and c0>o0 and o1>=c0 and c1<=o0
    if bull_engulf or bear_engulf:
        tag = "BULL_ENGULF" if bull_engulf else "BEAR_ENGULF"
        print(f"{vals.loc[i,'dt_ny'].strftime('%m-%d %H:%M')} {tag} (c {vals.loc[i,'close']:.1f})")
