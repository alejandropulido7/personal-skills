import pandas as pd, numpy as np

df = pd.read_csv('/tmp/ohlcv_60.csv')
df['dt'] = pd.to_datetime(df['time'], unit='s', utc=True)
df['dt_ny'] = df['dt'] - pd.Timedelta(hours=4)  # EDT

# Daily aggregates (by NY day)
df['ny_date'] = df['dt_ny'].dt.date
daily = df.groupby('ny_date').agg(pdh=('high','max'), pdl=('low','min'), oc=('open','first'), cc=('close','last')).reset_index()
print("=== Daily (NY) OHLC — últimos 7 días ===")
print(daily.tail(7).to_string(index=False))

# Determine most recent complete NY day (previous trading day) and current partial day
dates = sorted(daily['ny_date'])
prev_day = daily.iloc[-2]['ny_date'] if len(daily) >= 2 else daily.iloc[-1]['ny_date']
cur_day  = daily.iloc[-1]['ny_date']

# Session levels for the current (partial) NY day
d = df[df['ny_date']==cur_day].copy()
d['hm'] = d['dt_ny'].dt.strftime('%H:%M')
print(f"\n=== {cur_day} NY día actual (parcial) — levels ===")
asia = d[(d['dt_ny'].dt.hour>=20) | (d['dt_ny'].dt.hour<8)]
london = d[(d['dt_ny'].dt.hour>=8) & (d['dt_ny'].dt.hour<13)]
ny = d[(d['dt_ny'].dt.hour>=13) & (d['dt_ny'].dt.hour<20)]
for name, s in [('ASIA(prev20-08)', asia), ('LONDON(08-13)', london), ('NY(13-20)', ny)]:
    if len(s):
        print(f"  {name}: H={s['high'].max():.1f}  L={s['low'].min():.1f}  (n={len(s)})")

# Previous trading day -> PDH / PDL
prev = df[df['ny_date']==prev_day]
print(f"\n  Prev day: {prev_day}")
print(f"  PDH (prev high): {prev['high'].max():.1f}")
print(f"  PDL (prev low):  {prev['low'].min():.1f}")
print(f"  Cierre previo (prev close): {prev['close'].iloc[-1]:.1f}")

# Current price
print(f"\n  Precio actual (close 1H): {d['close'].iloc[-1]:.1f}")
