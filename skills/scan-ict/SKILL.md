---
name: scan-ict
description: Rutina de validación ICT (Inner Circle Trader) para sesiones NY/London. Detecta killzones, FVG, OB, Breaker, sweeps. Use when the user invokes "scan_ict" or asks to scan/validate una configuración ICT. Consume tradingview-ohlcv, tradingview-watchlist y tradingview-drawings.
---
# scan_ict — ICT Killzone (multi-activo)

Rutina ICT end-to-end. Solo operar dentro de killzones. Ejecutar pasos EN ORDEN.

## Prerrequisitos

- TradingView Desktop abierto (modo normal). Símbolo activo auto-detectado.
- Estrategia: `~/.gemini/config/trading-strategies/ICT_Killzone.yaml`
- OHLCV en `/tmp/ohlcv_{60,15,5}.csv`

## Scripts

| Paso | Script | Ubicación |
|---|---|---|
| OHLCV | `ohlcv_extract.py` | `tradingview-ohlcv/scripts/` |
| Análisis ICT | `ict_levels.py` | `scan-ict/scripts/` |
| Dibujo genérico | `draw_generic.py --levels /tmp/ict_levels.json` | `tradingview-drawings/scripts/` |
| Verificación | `verify_drawings.py` | `tradingview-drawings/scripts/` |

## Pipeline

### 1. Leer la estrategia
Leer `ICT_Killzone.yaml`: `sessions` (London/NY AM/NY PM), `entry_rules`, `risk_management`, `chart_checklist`.

### 2. Extraer OHLCV (1H, 15m, 5m)
Ejecutar `tradingview-ohlcv/scripts/ohlcv_extract.py`. Salida: `/tmp/ohlcv_60.csv`, `_15.csv`, `_5.csv`.

### 3. Evaluar reglas ICT
Ejecutar `scan-ict/scripts/ict_levels.py`:
- Bias HTF (1H HH/HL/LH/LL)
- Killzone activa: LONDON_OPEN (02-05 ET), NY_AM (08:30-11 ET), NY_PM (13:30-16 ET)
- Liquidez: PDH/PDL
- Sweep detectado
- FVG y Order Block (15m)
- Genera `/tmp/ict_levels.json`

### 4. Dibujar niveles + checklist
```bash
python3 ~/.gemini/config/skills/tradingview-drawings/scripts/draw_generic.py \
  --levels /tmp/ict_levels.json --res 60
```
Dibuja rays FVG/OB/SR, rectángulo del OB, líneas SL/TP/Entrada, checklist azul ICT.

### 5. Reporte técnico
- Estrategia: ICT_Killzone
- Killzone activa / Bias / Sweep / FVG/OB
- Entrada / SL / TP + R:R
- SMT divergence (opcional: comparar con activo correlacionado)

### 6. Screenshot (opcional)
`Page.captureScreenshot` → `~/Downloads/ict_scan.png`

## Verificación post-dibujo
Conteo: rays ≥ 2, lines ≥ 3, rect ≥ 1, text ≥ 1, path == 0.

## Gotchas
- `LineToolRect` → usar `LineToolRectangle`
- Anclar rays a la vela del swing
- Recolectar antes de eliminar al iterar `dataSources()`
- NO usar `LineToolPath`
- Checklist azul `#2196f3`, tamaño 16

## Relacionadas
- `tradingview-ohlcv`, `tradingview-drawings`, `tradingview-watchlist`, `create-trading-strategy`, `scan-smc`