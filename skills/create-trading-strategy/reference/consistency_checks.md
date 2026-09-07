# Validación de consistencia de la estrategia

Revisar cada respuesta contra estas reglas. Formato de aviso:
`⚠️ Inconsistencia: [regla A] vs [regla B] → por qué → corrección sugerida`.

## Entrada vs dirección/contexto
- **Filtro de tendencia contradice la entrada**: si el contexto exige "solo longs en tendencia
  alcista" pero la entrada es un sweep sell-side para comprar, verificar que el sweep es
  *en contra* de la tendencia y la entrada *a favor* (correcto en SMC). Si se mezclan
  direcciones sin explicar, advertir.
- **Entrada en contra de tendencia sin filtro claro**: operar contra tendencia exige SL más
  ajustado y confirmación extra (MSS + engulfing). Si no se especifica, recomendar añadirla.
- **Trigger ambiguo**: "entrar cuando se vea el movimiento" no es operativo. Exigir evento
  concreto (cierre de vela, ruptura de nivel, cruce de EMA, engulfing).

## Sesión vs activo
- **Horario de sesión sin zona horaria**: siempre convertir (ej. "09:30 NY" → EDT/EST + UTC).
  Advertir si solo dan hora local sin zona.
- **Sesión NY con activo asiático/JPY**: si el activo tiene poca liquidez en la ventana
  elegida, advertir y proponer ajustar la ventana.
- **Enforce_session=true pero sin horario definido**: requerir start/end.
- **Multi-activo con una sola ventana**: verificar que la sesión aplica a todos (mercados con
  horarios distintos → advertir).

## Temporalidades
- **Entrada en TF mayor que contexto**: la temporalidad de entrada debe ser ≤ las de contexto.
  Si entrada = 1H y contexto = 5m, advertir (invertir o corregir).
- **Demasiadas temporalidades**: máx 3-4 en el pipeline; si son más, sugerir consolidar.

## Riesgo y gestión
- **Riesgo por trade > 1%**: recomendado ≤1%. >2% → advertencia fuerte (ruina probable a
  largo plazo).
- **Riesgo diario total > 3%**: advertir (con 2 pérdidas diarias se alcanza el límite semanal
  razonable).
- **R:R incoherente con la estructura del TP**: si SL se define por estructura y TP por RR,
  verificar que el TP cae en zona de sentido (no en medio del aire). Si el TP con RR=2 cae en
  una resistencia fuerte, advertir y sugerir TP en estructura.
- **SL en el lado equivocado**: para long, SL debe estar DEBAJO del extremo (mecha) + buffer;
  para short, ARRIBA. Si el usuario lo define al revés, corregir.
- **TP = SL (R:R 1:1) con intención de "rentable"**: advertir que 1:1 con winrate <50% no es
  rentable; sugerir R:R ≥1.5 o exigir ventaja (winrate/edge).
- **Trailing sin punto de activación**: definir cuándo se activa (ej. tras +1R) y el paso.
- **Máx trades diarios sin límite de pérdidas**: el número de trades debe combinarse con el
  stop diario (si 5 trades × 1% = 5% riesgo diario > 3%, advertir).

## Activos / símbolo
- **Activo con broker que no persiste dibujos**: preferir CAPITALCOM para NAS100 (Pepperstone
  no guarda). Si el usuario elige un broker sin persistencia, advertir y sugerir el que sí.
- **Símbolo inexistente o ambiguo**: verificar con MCP (yahoo_price / stock_prices) o con la
  watchlist. Si no se resuelve, preguntar el símbolo completo (exchange:symbol).
- **Multi-activo con reglas idénticas a un activo específico**: confirmar si aplica igual.

## Indicadores
- **Parámetros inválidos**: ventana RSI>100 o <2, EMA≤0, etc. → corregir.
- **Indicador contradictorio con el concepto**: ej. "uso SMC (no indicadores)" + "entrada por
  cruce de RSI" — no es contradictorio si se usan como confirmación, pero preguntar cuál manda.
- **Dependencia de indicador no disponible**: verificar que existe en pandas-ta o en MCP
  (coin_analysis). Si no, proponer equivalente.

## Checklist / gráfico
- **Reglas de entrada sin checklist en gráfico**: recomendar añadir `chart_checklist` para
  marcar lo analizado/pendiente (estilo scan_nas100).
- **Dibujo de niveles sin anclaje**: recordar regla de anclaje de rays a la vela generadora.

## Otras
- **Backtest vs forward**: si el usuario pide "rentable" sin datos, aclarar que el diseño
  genera la estrategia pero la rentabilidad requiere backtest/forward test (ofrecer
  `backtest_strategy` / `walk_forward_backtest_strategy` del MCP).
- **Reglas ambiguas tras 2 rondas de preguntas**: si una regla sigue sin claridad, NO
  inventarla: preguntar con opciones concretas ("¿prefieres A, B o C?").
