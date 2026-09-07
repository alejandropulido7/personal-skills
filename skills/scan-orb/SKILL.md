---
name: scan-orb
description: Rutina de validación ORB (Opening Range Breakout) para la sesión NY. Detecta el rango de apertura 09:30-09:45 ET, volumen y breakout. Use when the user invokes "scan_orb" or asks to scan/validate un setup ORB. Consume tradingview-ohlcv, tradingview-watchlist y tradingview-drawings.
---
# scan_orb — Opening Range Breakout (NY)

Rutina ORB end-to-end. Solo válida durante sesión NY (09:30-16:00 ET). Ejecutar pasos EN ORDEN.

## Prerrequisitos

- TradingView Desktop abierto (modo normal). Símbolo activo auto-detectado.
- Estrategia: `${STRATEGIES_DIR:-${HOME}/.hermes/trading-strategies}/ORB_NY_Breakout.yaml`
- OHLCV en `/tmp/ohlcv_{60,5}.csv`

## Scripts

| Paso | Script | Ubicación |
|---|---|---|
| OHLCV | `ohlcv_extract.py` | `tradingview-ohlcv/scripts/` |
| Análisis ORB | `orb_analysis.py` | `scan-orb/scripts/` |
| Dibujo genérico | `draw_generic.py --levels /tmp/orb_levels.json` | `tradingview-drawings/scripts/` |
| Verificación | `verify_drawings.py` | `tradingview-drawings/scripts/` |

## Pipeline

### 1. Leer la estrategia
Leer `ORB_NY_Breakout.yaml`: `sessions`, `entry_rules` (rango 09:30-09:45, volumen 1.5×, breakout), `risk_management`.

### 2. Extraer OHLCV (1H, 5m)
Ejecutar `tradingview-ohlcv/scripts/ohlcv_extract.py`. Salida: `/tmp/ohlcv_60.csv`, `_5.csv`.

### 3. Evaluar reglas ORB
Ejecutar `scan-orb/scripts/orb_analysis.py`:
- Sesión NY activa? (09:30-16:00 ET)
- Rango ORB (09:30-09:45): high/low
- Volumen breakout ratio
- EMA20 1H como filtro de tendencia
- Breakout LONG / SHORT detectado
- Genera `/tmp/orb_levels.json`

### 4. Dibujar niveles + checklist
```bash
python3 "${SKILLS_DIR:-${HOME}/.hermes/skills}/tradingview-drawings/scripts/draw_generic.py" \
  --levels /tmp/orb_levels.json --res 5
```
Dibuja: rays del rango ORB (H rojo, L verde), rectángulo del rango, líneas SL/TP/Entrada, checklist.

### 5. Reporte técnico
- Estrategia: ORB_NY_Breakout
- Rango ORB High/Low
- Breakout dirección + volumen ratio
- Entrada / SL / TP + R:R

### 6. Screenshot (opcional)
`Page.captureScreenshot` → `~/Downloads/orb_scan.png`

## Verificación post-dibujo
Counts: rays ≥ 2, lines ≥ 3, rect ≥ 1, text ≥ 1, path == 0.

## Gotchas
- `LineToolRect` → usar `LineToolRectangle`
- NO usar `LineToolPath`
- Recuerda que el ORB se forma después de 3 velas 5m desde las 09:30 ET
- Volumen puede no estar disponible en algunos símbolos; si no, usar solo price action

## Relacionadas
- `tradingview-ohlcv`, `tradingview-drawings`, `tradingview-watchlist`, `create-trading-strategy`