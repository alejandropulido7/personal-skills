---
name: scan-crt
description: Rutina de validación Candle Range Theory (CRT) para sesión NY. Identifica opens (09:30, 11:00, 13:00, 14:30 ET), manipulación y equalización. Use when the user invokes "scan_crt" or asks to scan/validate un setup CRT. Consume tradingview-ohlcv, tradingview-watchlist y tradingview-drawings.
---
# scan_crt — Candle Range Theory (NY Equalization)

Rutina CRT end-to-end. Solo válida durante sesión NY (09:30-16:00 ET). Basada en opens fijos por hora de reloj. Ejecutar pasos EN ORDEN.

## Prerrequisitos

- TradingView Desktop abierto (modo normal). Símbolo activo auto-detectado.
- Estrategia: `~/.gemini/config/trading-strategies/CRT_NY_Equalization.yaml`
- OHLCV en `/tmp/ohlcv_{60,5}.csv`

## Scripts

| Paso | Script | Ubicación |
|---|---|---|
| OHLCV | `ohlcv_extract.py` | `tradingview-ohlcv/scripts/` |
| Análisis CRT | `crt_analysis.py` | `scan-crt/scripts/` |
| Dibujo genérico | `draw_generic.py --levels /tmp/crt_levels.json` | `tradingview-drawings/scripts/` |
| Verificación | `verify_drawings.py` | `tradingview-drawings/scripts/` |

## Pipeline

### 1. Leer la estrategia
Leer `CRT_NY_Equalization.yaml`: `context_rules` (open_times), `entry_rules` (equalización/breakout), `risk_management`.

### 2. Extraer OHLCV (1H, 5m)
Ejecutar `tradingview-ohlcv/scripts/ohlcv_extract.py`. Salida: `/tmp/ohlcv_60.csv`, `_5.csv`.

### 3. Evaluar reglas CRT
Ejecutar `scan-crt/scripts/crt_analysis.py`:
- Sesión NY activa?
- Open actual (09:30 OOD / 11:00 / 13:00 / 14:30 ET)
- Rango del open (primeras 5 velas 5m)
- Manipulación (sweep de un borde del rango + reversión)
- Equalización o breakout
- Genera `/tmp/crt_levels.json`

### 4. Dibujar niveles + checklist
```bash
python3 ~/.gemini/config/skills/tradingview-drawings/scripts/draw_generic.py \
  --levels /tmp/crt_levels.json --res 5
```
Dibuja: rays del rango del open, rectángulo del rango, EQ target (si hay manipulación), líneas SL/TP/Entrada, checklist.

### 5. Reporte técnico
- Estrategia: CRT_NY_Equalization
- Open actual + rango
- Manipulación detectada → equalización / breakout
- Entrada / SL / TP + R:R

### 6. Screenshot (opcional)
`Page.captureScreenshot` → `~/Downloads/crt_scan.png`

## Verificación post-dibujo
Counts: rays ≥ 2, lines ≥ 3, rect ≥ 1, text ≥ 1, path == 0.

## Gotchas
- `LineToolRect` → usar `LineToolRectangle`
- NO usar `LineToolPath`
- Los opens son fijos por reloj (ET): 09:30, 11:00, 13:00, 14:30
- El rango necesita al menos 3 velas 5m para formarse (~15 min tras el open)
- CRT en NY solo: si es fuera de 09:30-16:00 ET, abortar

## Relacionadas
- `tradingview-ohlcv`, `tradingview-drawings`, `tradingview-watchlist`, `create-trading-strategy`, `scan-orb`