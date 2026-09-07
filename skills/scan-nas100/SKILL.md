---
name: scan-nas100
description: Rutina completa de validación SMC del NAS100 (PEPPERSTONE:NAS100) para la sesión de Nueva York basada en la estrategia NAS100_NY_Liquidity_Sweep. Use when the user invokes "scan_nas100" or asks to scan/validate the NAS100 NY liquidity sweep setup, draw the levels, and get entry/SL/TP with RR. Consumes OHLCV CSVs from tradingview-ohlcv and draws with tradingview-drawings.
---

# scan_nas100 — Validación SMC NAS100 (NY Liquidity Sweep)

Rutina end-to-end verificada. Ejecutar los pasos EN ORDEN, sin omitir ninguno. Si una etapa
falla, máx 2 reintentos y luego informar al usuario (no continuar a ciegas).

> **IMPORTANTE — usar los scripts guardados, NO recrearlos desde cero.** Cada paso del
> pipeline tiene su script en `scripts/` (de esta skill o de `tradingview-ohlcv` /
> `tradingview-drawings`). Copiar/encontrar el script, ajustar solo los parámetros, y
> ejecutarlo. Si un script falla, depurar el fallo; no reescribir toda la lógica.

## Prerrequisitos

- TradingView Desktop **abierto de forma normal**. Usa el símbolo **`CAPITALCOM:NAS100`**
  (verified: en este broker los dibujos SÍ se guardan en el layout y se ven en el móvil; en
  `PEPPERSTONE:NAS100` los dibujos inyectados NO persistían).
- La estrategia en `${STRATEGIES_DIR:-${HOME}/.hermes/trading-strategies}/NAS100_NY_Liquidity_Sweep.yaml`
  (leer SIEMPRE antes de evaluar; es la fuente de verdad de reglas y checklist).
- OHLCV en `/tmp/ohlcv_{240,60,15,5}.csv` (skill `tradingview-ohlcv`).

> **Persistencia de dibujos:** la causa de que "se borren los dibujos al cambiar de activo"
> NO es el modo debug — es el símbolo. En `CAPITALCOM:NAS100` los dibujos creados por
> `draw_all.py` se guardan en el layout (sincronizan al móvil). Preferir siempre este broker.
> Abrir TradingView normalmente (sin flag host) es suficiente tras la primera configuración.

> **REGLAS ANTI-BLOQUEO (obligatorias):**
> 1. **Mercado en vivo = precios variables.** El precio de referencia para calcular Entrada/SL/TP
>    es SIEMPRE el **cierre de la última vela 5m** del CSV recién extraído. No "quedarse pensando"
>    en que el precio cambia: congelar en el último cierre 5m y ejecutar.
> 2. **El símbolo activo es la fuente de verdad.** El OHLCV puede venir de otra sesión/símbolo
>    (p.ej. PEPPERSTONE ~4400 vs CAPITALCOM ~30000). Re-extraer SIEMPRE tras navegar a
>    `CAPITALCOM:NAS100` y verificar que el rango de precios coincide con el gráfico antes de
>    dibujar.
> 3. **No sobre-analizar**: 1 pasada de scripts (estructura/liquidez/engulfing) + 1 ejecución de
>    `draw_all.py` + 1 verificación. Si el setup no está maduro (falta MSS o engulfing), se dibuja
>    el estado PENDIENTE con los niveles de espera y se reporta. No re-iterar el análisis.

> **REGLAS DE DIBUJO Y SESGO (obligatorias):**
> 1. **PROHIBIDO usar `LineToolPath`** (path de tendencia) — rompe el gráfico. No dibujar path
>    en ningún caso. Reemplazar por rays/lines ancladas a niveles reales.
> 2. **Emojis en checklist**: usar `✅` para lo cumplido y `🟠` para lo pendiente. Nada de `[X]`/`[ ]`.
>    La plantilla del checklist (estado `analyzed`) marca con ✅/🟠: Tend4H, 1H/15m, NY, Sweep,
>    MSS, Engulf5m. La sección `pending` usa `🟠` para cada condición que falta.
> 3. **Niveles "por esperar" SIEMPRE marcados con horizontal_ray.** Si el checklist dice
>    "ESPERAR: MSS ruptura del swing", DEBE existir un horizontal_ray en el precio del MSS
>    (y si se espera sweep de un pool, un ray en ese pool). Nunca dejar un nivel citado en el
>    texto sin su correspondiente ray en el gráfico.
> 4. **Decisión libre de mayor probabilidad (sin contradicciones).** Si el precio da señales de
>    posible reversión en contra de la tendencia predominante (sweep + MSS + engulfing en contra),
>    APLICAR esa reversión como sesgo. NO contradecirse entre "analizado" y "pendiente": si decides
>    un sesgo (LONG/SHORT/ESPERAR), todo el checklist, rays y niveles de entrada deben ser
>    coherentes con ese único sesgo. Decidir con la mayor probabilidad según los datos.
> 5. **Anti-contradicción = preguntar si te bloqueas.** Si durante el análisis el estado te deja
>    en contradicción (ej. tendencia neutra pero sweep alcista, MSS no claro, dos sesgos plausibles),
>    NO quedarse en el estado thinking: preguntar al usuario las opciones disponibles (LONG/SHORT/
>    ESPERAR) y proceder con la elegida sin dudar.

> **REGLA DE COHERENCIA DE NIVELES Y SL AJUSTADO (obligatoria, optimizada para sesión NY):**
> - **LONG**: `Entrada > MSS`. La entrada se coloca POR ENCIMA del nivel MSS que se espera romper
>   (con buffer +5-10 pts sobre el MSS o retest del OB 5m). NUNCA entrada por debajo del MSS.
> - **SHORT**: `Entrada < MSS`. La entrada se coloca POR DEBAJO del nivel MSS a romper.
> - **SL AJUSTADO (Protección Estructural Local)**:
>   * LONG: SL por debajo del Order Block local 5m/15m o del mínimo de la vela gatillo 5m,
>     con buffer de 5-10 pts (Rango objetivo SL: 20-35 pts). Si el sweep fue profundo,
>     NO usar el mínimo macro si supera 40 pts de distancia; proteger tras el OB/Swing Low 5m.
>   * SHORT: SL por encima del Order Block local 5m/15m o del máximo de la vela gatillo 5m,
>     con buffer de 5-10 pts (Rango objetivo SL: 20-35 pts).
> - **TP**: `TP = Entrada ± 2×riesgo` (RR ≥ 1:2), con riesgo = |Entrada − SL|. Con un SL
>   ajustado de 25-35 pts, el TP de 50-70 pts es altamente alcanzable en la sesión de NY.
> - **Checklist previo al dibujo**: verificar que se cumpla el orden
>   `sweep/OB <→ MSS <→ Entrada` para el sesgo elegido. Si se detecta incoherencia
>   (p.ej. LONG con Entrada < MSS), recalcular la Entrada al lado correcto ANTES de dibujar.
> - Esta regla está definida en el YAML como `entry_rules.level_coherence_rule`. Si algún dibujo
>   previo quedó incoherente, limpiarlo y redibujar.

## Scripts disponibles (reutilizar)

| Paso | Script | Ubicación |
|---|---|---|
| 2. OHLCV | `ohlcv_extract.py` | `tradingview-ohlcv/scripts/` |
| 3a. Estructura | `structure_analysis.py` | `scan-nas100/scripts/` |
| 3b. Liquidez | `liquidity_pools.py` | `scan-nas100/scripts/` |
| 3c. Engulfing 5m | `engulfing_5m.py` | `scan-nas100/scripts/` |
| 4-5. Dibujo completo | `draw_all.py --side long|short [--text "..."]` | `tradingview-drawings/scripts/` |
| 4. Rays anclados | `draw_rays_anchored.py` | `tradingview-drawings/scripts/` |
| 4. OB rectángulo | `draw_ob_rectangle.py` | `tradingview-drawings/scripts/` |
| 4. Líneas + texto | `draw_lines_path_text.py` | `tradingview-drawings/scripts/` |
| 5. Checklist azul | `draw_checklist_blue.py` | `tradingview-drawings/scripts/` |
| limpieza | `clean_rays_by_name.py` | `tradingview-drawings/scripts/` |
| verificación | `verify_drawings.py` | `tradingview-drawings/scripts/` |

> `draw_all.py` ejecuta TODO el dibujo (limpiar + 3 rays + OB + SL/TP/Entrada + checklist azul)
> en una sola llamada. **NO dibuja path** (prohibido: rompe el gráfico). Es el script preferido;
> los otros son módulos individuales para retoques.

## Pipeline

### 1. Leer la estrategia

Leer `NAS100_NY_Liquidity_Sweep.yaml` y extraer `context_rules`, `entry_rules`,
`risk_management` y `chart_checklist` (este último es el que se dibuja en el gráfico).

### 2. Extraer OHLCV (4H, 1H, 15m, 5m)

Ejecutar `tradingview-ohlcv/scripts/ohlcv_extract.py` (conmuta resoluciones y restaura la
original). Salida: `/tmp/ohlcv_240.csv`, `_60.csv`, `_15.csv`, `_5.csv`.

### 3. Evaluar matemáticamente context_rules y entry_rules

Ejecutar los scripts de análisis (con pandas/numpy, o pandas-ta si está disponible):

- `structure_analysis.py` → estructura por TF (swings 3/3): `ALCISTA (HH/HL)` / `BAJISTA (LH/LL)` / `NEUTRO`.
- `liquidity_pools.py` → PDH/PDL (día previo NY), H/L de Asia (20-08 NY), Londres (08-13 NY),
  NY (13-20 NY), swings intradiarios.
- `engulfing_5m.py` → detección de vela envolvente 5m.

Interpretar las reglas de entrada (estado):

- `liquidity_sweep`: ¿el precio barrió un nivel en contra de la tendencia? (¿qué nivel, a qué lado?)
- `market_structure_shift`: ¿rompió con cuerpo el último swing válido?
- `trigger`: ¿vela envolvente 5m en favor de la tendencia? → si todo se cumple, ENTRADA en
  el cierre de esa vela (Market Order).
- `fakeout_breakout`: probabilidad según fuerza de tendencia → colocar texto en el gráfico.
- **Estado de sesión NY:** `ABIERTA` si 09:30–16:00 EDT, si no `CERRADA`.

### 4 y 5. Dibujar niveles + checklist (script único)

Ejecutar `tradingview-drawings/scripts/draw_all.py`. **El script detecta automáticamente el
símbolo NAS100 desde la watchlist** (abre el panel, lee `data-symbol-full` de la fila
NAS100 — independiente del broker: capitalcom, pepperstone, etc.) y navega a él antes de
dibujar:

```bash
python3 "${SKILLS_DIR:-${HOME}/.hermes/skills}/tradingview-drawings/scripts/draw_all.py" \
  --res 60 --side long --text "<checklist con \n>"
```

- **`--symbol` OPCIONAL** (por defecto auto-detecta desde la watchlist vía
  `tradingview-watchlist/scripts/detect_nas100.py`; si no encuentra, usa
  `CAPITALCOM:NAS100`). `--res` por defecto `60`=1H.
- `--side long|short` selecciona los 3 rays a conservar + niveles SL/TP/Entrada por defecto.
  ⚠️ Los niveles por defecto son valores de ejemplo de la última sesión — en el flujo real
  **recalcular los niveles con los scripts del paso 3** (sobre los OHLCV frescos del símbolo
  detectado) y pasarlos vía `--text`/edición de niveles si difieren.
- El script limpia dibujos previos, dibuja rays (anclados a la vela generadora), rectángulo OB,
  líneas SL/TP/ENTRADA y el checklist azul (tamaño 16) en un solo paso. **NO dibuja path.**
- **Regla MSS por esperar:** si el checklist incluye "ESPERAR MSS", pasar el precio del último
  swing válido como nivel adicional al script (editar `rays` en `draw_all.py` o `--text`) y
  asegurar que exista un horizontal_ray en ese nivel.
- Tras dibujar, verificar conteo de rays (puede perderse alguno al navegar de símbolo/resolución).

### 6. Reporte técnico en consola

Estructura fija: 1) Estrategia activada, 2) Coordenadas exactas (niveles dibujados),
3) Niveles de riesgo (Entrada/SL/TP + RR), 4) Ejecución de la tool de dibujo confirmada.

### 7. Screenshot (opcional, si el usuario lo pide)

Guardar una captura del gráfico vía CDP (`Page.captureScreenshot`) en
`~/Downloads/nas100_scan.png`. El agente puede no poder leer imágenes: confirmar el tamaño
del archivo y reportar la ruta al usuario, no intentar "ver" la imagen.

## Verificación post-dibujo

Re-enumerar `pane.dataSources()` (script `verify_drawings.py`) y confirmar que existen:
**3+ rays S/R** (pools + nivel MSS/sweep esperado, si aplica), rectángulo OB,
líneas SL/TP/Entrada y **1 solo texto** de checklist. **NO debe existir ningún Path.**
Reportar resolución al usuario. Si el conteo de rays no es el esperado (por cambio de
resolución), recrear los faltantes anclados a su vela generadora.

## Gotchas verificados (2026-08-12, TV Desktop 3.3.0)

- `LineToolRect` → usar **`LineToolRectangle`** (el primero lanza "Cannot create unknown line tool").
- Anclar rays SIEMPRE al índice de la vela del swing (ver skill drawings), nunca al último bar.
- Al iterar `dataSources()` y eliminar en el mismo bucle se saltan elementos: recolectar primero
  y eliminar después.
- **NO usar `LineToolPath`** para tendencias: rompe el gráfico y no soporta child `text`.
  Toda referencia visual debe ser ray/line anclada a un nivel real.
- El `LineToolText` guarda `\n` y `fontsize`/`color` en childs: verificar que `fontsize==16` y
  `color=='#2196f3'` tras crear (a veces setValue no persiste si el child no existe).
- pandas-ta puede no estar disponible (PyPI exige ≥3.12): usar fallback estructural pandas/numpy
  y documentarlo (ver skill `tradingview-ohlcv`).

## Relacionadas

- `tradingview-ohlcv` — extracción de CSVs.
- `tradingview-drawings` — reglas de dibujo y anclaje.
- `tradingview-debug-launch` — arranque/verificación del CDP.
