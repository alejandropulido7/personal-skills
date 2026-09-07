---
name: scan-smc
description: Rutina de validación SMC multi-activo. Analiza estructura, pools de liquidez, Order Blocks, FVG, sweep y engulfing. Use when the user invokes "scan_smc" or asks to scan/validate a SMC setup for any asset in the watchlist. Consume tradingview-ohlcv, tradingview-watchlist y tradingview-drawings.
---
# scan_smc — Smart Money Concepts (multi-activo)

Rutina end-to-end SMC. Ejecutar pasos EN ORDEN. Máx 2 reintentos por etapa.

## Prerrequisitos

- TradingView Desktop abierto (modo normal o debug). El símbolo activo se auto-detecta desde el gráfico.
- Estrategia: `${STRATEGIES_DIR:-${HOME}/.hermes/trading-strategies}/SMC_MultiAsset.yaml`
- OHLCV en `/tmp/ohlcv_{240,60,15,5}.csv`

## Scripts

| Paso | Script | Ubicación |
|---|---|---|
| OHLCV | `ohlcv_extract.py` | `tradingview-ohlcv/scripts/` |
| Análisis SMC | `smc_levels.py` | `scan-smc/scripts/` |
| Dibujo genérico | `draw_generic.py --levels /tmp/smc_levels.json` | `tradingview-drawings/scripts/` |
| Verificación | `verify_drawings.py` | `tradingview-drawings/scripts/` |

## Pipeline

### 1. Leer la estrategia
Leer `SMC_MultiAsset.yaml`: `context_rules`, `entry_rules`, `risk_management`, `chart_checklist`.

### 2. Extraer OHLCV (4H, 1H, 15m, 5m)
Ejecutar `tradingview-ohlcv/scripts/ohlcv_extract.py`. Salida: `/tmp/ohlcv_240.csv`, `_60.csv`, `_15.csv`, `_5.csv`.

### 3. Evaluar reglas SMC
Ejecutar `scan-smc/scripts/smc_levels.py`:
- Estructura por TF (HH/HL/LH/LL)
- Pools de liquidez (PDH/PDL, sesiones Asia/Londres/NY)
- Order Blocks y Fair Value Gaps (15m)
- Sweep de liquidez
- Vela envolvente 5m
- Genera `/tmp/smc_levels.json`

### 4. Dibujar niveles + checklist
```bash
python3 "${SKILLS_DIR:-${HOME}/.hermes/skills}/tradingview-drawings/scripts/draw_generic.py" \
  --levels /tmp/smc_levels.json --res 60
```
El script auto-detecta el símbolo del gráfico activo y dibuja: rays de niveles S/R, rectángulo OB, líneas SL/TP/Entrada, checklist azul.

### 5. Reporte técnico
- Estrategia: SMC_MultiAsset
- Sesgo: LONG / SHORT / ESPERAR
- Niveles: Entrada / SL / TP + R:R
- Checklist de cumplimiento

### 6. Screenshot (opcional)
`Page.captureScreenshot` → `~/Downloads/smc_scan.png`

## Verificación post-dibujo
Revisar que `draw_generic.py` reporte counts: rays ≥ 2, lines ≥ 3, rect ≥ 1, text ≥ 1, path == 0.

## Gotchas
- `LineToolRect` → usar `LineToolRectangle`
- Anclar rays a la vela del swing, no al último bar
- Recolectar antes de eliminar al iterar `dataSources()`
- NO usar `LineToolPath` (rompe el gráfico)
- Checklist azul `#2196f3`, tamaño 16

## Relacionadas
- `tradingview-ohlcv`, `tradingview-drawings`, `tradingview-watchlist`, `create-trading-strategy`, `scan-nas100`