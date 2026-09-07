# Conceptos de estrategias (glosario para la entrevista)

Úsalo para explicar opciones al usuario y proponer el enfoque que encaje con lo que describe.

## SMC (Smart Money Concepts)
- **Order Block (OB):** última vela en contra antes de un movimiento impulsivo; zona de
  reacción. Se dibuja como rectángulo.
- **Fair Value Gap (FVG):** hueco de 3 velas (desequilibrio) donde el precio tiende a volver.
- **Market Structure Shift (MSS):** ruptura con cuerpo del último swing que confirma la
  reversión tras un sweep.
- **Liquidity Sweep:** barrido de un nivel (PDH/PDL, high/low de sesión, swing) para cazar
  stops antes de la reversión.
- **PDH/PDL:** high/low del día anterior (liquidez obvia).
- **Break of Structure (BOS):** continuación de tendencia rompiendo estructura.

## ORB (Opening Range Breakout)
- Rango formado en los primeros N minutos de la sesión (ej. primeros 15 min de NY).
- Estrategia: entrada cuando el precio rompe el high/low del rango con volumen, en dirección
  de la ruptura. Ideal para intradía en índices.

## CTR (Central Trading Range / Consolidación)
- Rango central de una sesión/periodo (punto de equilibrio).
- Estrategia: operar la ruptura del CTR (continuación) o el rebote en los bordes (reversión),
  según contexto.

## ICT (Inner Circle Trader — enfoque institucional)
- **SMT Divergence:** divergencia entre 2 activos correlacionados (ej. NAS100 vs S&P) para
  detectar máximos/mínimos falsos.
- **FVG / Order Block / Breaker:** bloques de órdenes y desequilibrios.
- **PDH/PDL, Asia/London range:** liquidez de sesiones.
- **Killzones:** ventanas horarias de alta probabilidad (Londres/NY open).
- **Judas swing / liquidity grab:** barrido de liquidez antes del movimiento real.

## Indicadores técnicos (pandas-ta / MCP)
- **RSI:** sobrecompra/sobreventa, divergencias.
- **MACD:** cruces, momentum.
- **EMA/SMA:** cruces y dirección de tendencia (ej. EMA 20/50/200).
- **Bollinger:** compresión (squeeze) y ruptura.
- **ATR:** volatilidad → tamaño de SL / trailing.
- **Supertrend:** sigue tendencia, cambia de lado.
- **VWAP:** precio medio ponderado por volumen (referencia institucional intradía).
- **Donchian / Keltner:** canales de ruptura.
- **Stochastic / CCI:** osciladores.

## Price Action
- **Engulfing:** vela que envuelve el cuerpo de la anterior (reversión).
- **Pin bar / hammer:** mecha larga, rechazo.
- **Inside bar:** consolidación antes de breakout.
- **Soporte/Resistencia y swings:** estructura.

## Enfoques de tiempo
- **Scalping:** segundos-minutos, TF 1m/5m.
- **Intradía (day trading):** TF 5m/15m/1H, cierra posición en el día.
- **Swing:** 1H/4H/D, retiene días.
- **Position:** D/S, semanas.

## Sesiones
- **Sydney:** 21:00–06:00 UTC. **Tokyo/Asia:** 00:00–09:00 UTC.
- **London:** 07:00–16:00 UTC (aprox.). **New York:** 12:30–21:00 UTC (EDT 08:30–17:00, o
  09:30–16:00 EST).
- Convertir siempre a la zona del usuario / a UTC en el análisis.

## Conceptos de riesgo
- **R:R (riesgo/beneficio):** cuánto ganas por cada 1 que arriesgas (ej. 1:2).
- **Riesgo por trade (%):** fracción del capital arriesgada por operación.
- **Break-even:** mover SL al precio de entrada tras alcanzar X R.
- **Trailing stop:** SL que sigue al precio.
- **Drawdown:** caída acumulada; mantener < 15-20%.
- **Expectancy:** (winrate × beneficio medio) − (lossrate × pérdida media) — debe ser > 0.
