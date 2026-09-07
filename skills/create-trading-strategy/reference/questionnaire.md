# Cuestionario profundo para diseñar una estrategia

Recorrer TODAS las dimensiones. Una pregunta por vez o en bloques de 4-5. No saltar ninguna:
cada una alimenta una parte del YAML y de la skill.

## 1. Identidad y concepto
- Nombre de la estrategia (título corto, ej. "NAS100_NY_Liquidity_Sweep").
- Concepto central (elige uno o combina): SMC, ORB, CTR, ICT (SMT, FVG, Order Blocks, Breaker),
  indicadores (RSI, MACD, EMA, Bollinger, Supertrend, ATR, VWAP), price action (engulfing,
  pin bar, inside bar), breakout/breakdown, rango (range trading), tendencia (trend following),
  reversión, scalping/intradía/swing.
- ¿Quieres que use conceptos que no conozcas? Explico cada uno (ver concepts.md) antes de que
  elijas.

## 2. Mercado y activos
- Tipo de activos: índices (NAS100, US30, SPX500), pares FX, metales (XAUUSD), cripto, acciones.
- ¿Activos específicos? ¿Usa la watchlist actual del usuario (leer con tradingview-watchlist) o
  una lista fija?
- ¿Un solo activo o multi-activo? Si multi-activo: ¿misma reglas para todos o variaciones?
- Broker preferido (p.ej. CAPITALCOM:NAS100 — persiste dibujos).

## 3. Temporalidades
- Temporalidad de entrada (ej. 5m).
- Temporalidad de contexto/tendencia (ej. 4H/1H).
- Temporalidad(es) de confirmación (ej. 15m).
- ¿Misma configuración para todos los activos?

## 4. Sesión y horario
- Sesión(es): New York, London, Asia, Sydney, Tokyo.
- Horario exacto de operación (ej. 09:30–16:00 EST).
- ¿Enforzar sesión? (solo operar dentro de la ventana).

## 5. Contexto / filtro de tendencia
- ¿Cómo defines la dirección operativa? (HH/HL alcista, LH/LL bajista, por EMAs, por VWAP, etc.)
- ¿Operas solo a favor de la tendencia, en contra, o ambos?
- ¿Hay filtros de volatilidad o de sesión (noticias, apertura)?

## 6. Condiciones de entrada
- Condición(es) exacta(s) de entrada (en orden, sin ambigüedad):
  ej. "sweep del nivel + MSS + vela envolvente 5m a favor".
- ¿Dirección: long, short, o ambos (depende de la estructura)?
- ¿Necesitas un trigger/confirmación final (vela envolvente, cierre de vela, tick)?
- ¿Tipo de orden: market al cierre, stop, limit?

## 7. Stop Loss
- ¿Cómo se define el SL? (detrás del extremo del sweep/swing + buffer, ATR, % fijo, bajo
  estructura, etc.)
- ¿SL por activo o por estrategia?
- ¿Buffer extra para spread/ruido? (ej. 10-15 pts)

## 8. Take Profit
- ¿TP fijo por ratio R:R (ej. 1:2), en estructura (frente a nivel), o ambos?
- ¿Trailing stop? ¿Mover SL a break-even tras X?
- ¿Salida parcial (escalonada) o todo en una orden?

## 9. Gestión de riesgo
- Riesgo por trade (% del capital). Recomendado: 0.5–1%.
- Riesgo máximo diario (stop total) — recomendado: 2–3%.
- Máximo número de trades por día/sesión.
- ¿Máx. trades simultáneos / por activo?

## 10. Reglas de salida adicionales
- ¿Salida por tiempo (time exit)?
- ¿Salida si se invalida la tesis (MSS en contra)?
- ¿Salida por noticia / evento?

## 11. Marcar en el gráfico
- ¿Qué niveles quieres ver marcados? (Order Block, FVG, S/R, PDH/PDL, sesiones, SL/TP/Entrada).
- ¿Checklist en el gráfico (lo analizado + lo pendiente)? (recomendado: sí, estilo scan_nas100).

## 12. Datos de verificación (opcional)
- ¿Tienes periodo de prueba / datos históricos para backtest?
- ¿Preferencia de intervalo para validación (diario/horario)?
