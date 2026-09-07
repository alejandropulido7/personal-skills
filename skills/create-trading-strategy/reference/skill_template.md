# Plantilla de skill de estrategia generada

Copiar este esqueleto al crear `<nombre-skill>/SKILL.md`. Sustituir los valores `{{...}}`.
Debe reutilizar las skills existentes — NO reescribir la lógica de extracción/dibujo.

---

---
name: {{nombre-skill}}
description: Rutina completa de validación de la estrategia {{NOMBRE}} ({{ACTIVO}}) usando las reglas de {{archivo_yaml}}. Use when the user invokes "{{trigger}}" o pide validar la estrategia {{NOMBRE}}, dibujar los niveles y obtener Entrada/SL/TP con RR. Consume tradingview-ohlcv (OHLCV), tradingview-watchlist (símbolo desde watchlist) y tradingview-drawings (dibujo).
---

# {{nombre-skill}} — {{NOMBRE_ESTRATEGIA}} ({{ACTIVO}})

Rutina end-to-end. Ejecutar los pasos EN ORDEN. Máx 2 reintentos por etapa; si falla, informar.

## Prerrequisitos

- TradingView Desktop abierto de forma normal. Símbolo: **`{{SYMBOL}}`** (detectar desde la
  watchlist con `tradingview-watchlist/scripts/detect_nas100.py`; independiente del broker).
- Estrategia en `~/.gemini/config/trading-strategies/{{archivo_yaml}}` (fuente de verdad).
- OHLCV en `/tmp/ohlcv_{...}.csv` (tradingview-ohlcv).

## Scripts

| Paso | Script | Ubicación |
|---|---|---|
| OHLCV | `ohlcv_extract.py` | `tradingview-ohlcv/scripts/` |
| Estructura | `structure_analysis.py` | `scan-nas100/scripts/` (o propio) |
| Liquidez | `liquidity_pools.py` | `scan-nas100/scripts/` |
| {{indicador}} | `...` | `...` |
| Dibujo completo | `draw_all.py --side ...` | `tradingview-drawings/scripts/` |
| Verificación | `verify_drawings.py` | `tradingview-drawings/scripts/` |

## Pipeline

### 1. Leer la estrategia
Leer el YAML y extraer `context_rules`, `entry_rules`, `risk_management` y `chart_checklist`.

### 2. Extraer OHLCV
`tradingview-ohlcv/scripts/ohlcv_extract.py` → `/tmp/ohlcv_{...}.csv`.

### 3. Evaluar reglas
- Detectar símbolo desde watchlist: `tradingview-watchlist/scripts/detect_nas100.py`.
- Estructura por TF: swings 3/3 → `ALCISTA (HH/HL)` / `BAJISTA (LH/LL)` / `NEUTRO`.
- {{reglas específicas de la estrategia}}.
- Estado de sesión: `ABIERTA`/`CERRADA` (convertir hora a la zona correcta).

### 4 y 5. Dibujar niveles + checklist
`tradingview-drawings/scripts/draw_all.py` (auto-detecta símbolo; navega y dibuja).
Ajustar niveles por defecto a los de {{NOMBRE}}:
- Rays a conservar (máx 3) y sus colores/nombres.
- OB / FVG / zona: tipo y coords.
- SL/TP/Entrada: niveles.
- Checklist azul (tamaño 16, `#2196f3`, una regla por línea, ✅ cumplido / 🟠 pendiente).

### 6. Reporte técnico
1) Estrategia activada, 2) Coordenadas, 3) Entrada/SL/TP + RR, 4) Dibujo confirmado.

### 7. Screenshot (opcional)
`Page.captureScreenshot` → `~/Downloads/{{nombre}}.png` (el agente puede no leer imágenes:
reportar ruta y tamaño).

## Verificación post-dibujo
Re-enumerar `pane.dataSources()` (verify_drawings.py): rayos/líneas/OB/path/1 checklist.
Reportar resolución. Recrear rays perdidos si cambió la resolución.

## Gotchas (heredados de scan_nas100)
- `LineToolRect` → usar **`LineToolRectangle`**.
- Anclar rays a la vela del swing (nunca al último bar ni Date.now()).
- Recolectar antes de eliminar al iterar `dataSources()`.
- `LineToolPath` no soporta child `text`.
- Checklist: `fontsize==16` y `color=='#2196f3'`; verificar tras crear.
- Persistencia: preferir símbolo que guarde dibujos (CAPITALCOM), no Pepperstone.
- pandas-ta puede faltar (PyPI ≥3.12): fallback estructural pandas/numpy y documentarlo.

## Relacionadas
- `tradingview-ohlcv`, `tradingview-watchlist`, `tradingview-drawings`,
  `tradingview-debug-launch`, `create-trading-strategy`.
