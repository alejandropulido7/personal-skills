---
name: tradingview-watchlist
description: Lee la "Lista de seguimiento" (watchlist) del TradingView Desktop activo desde el DOM (vía CDP 9222) y devuelve los símbolos con su precio y cambio %. Use when the user asks to see/scan the assets in their watchlist, list their followed symbols, or analyze the symbols currently in the watchlist. Requires TradingView Desktop running in debug mode.
---

# tradingview-watchlist — Leer la Lista de seguimiento

Extrae los activos que el usuario tiene en la watchlist del TradingView Desktop (panel lateral
"Instrumentos" / "Lista de seguimiento") con su precio, variación y cambio %. Sirve de insumo
para escanear/analizar los símbolos seguidos.

## Prerequisito

- TradingView Desktop en modo debug (CDP 9222). Si no: usar skill `tradingview-debug-launch`.

## Script

```bash
python3 "${SKILLS_DIR:-${HOME}/.hermes/skills}/tradingview-watchlist/scripts/read_watchlist.py"
```

Lee `document.body.innerText` desde el panel del gráfico, recorta desde la cabecera
`Símbolo / Última / Cbo / Cambio%` y muestra las filas agrupadas por moneda/índice.
(Verificado 2026-08-13: el DOM no expone `data-symbol` completo en todas las versiones;
el texto del panel es la vía fiable.)

## Detectar símbolo completo (con broker) desde la watchlist

```bash
python3 "${SKILLS_DIR:-${HOME}/.hermes/skills}/tradingview-watchlist/scripts/detect_nas100.py" [--short NAS100]
```

Abre el panel de la lista (si está cerrado) y lee la fila con `data-symbol-full` — devuelve
el símbolo COMPLETO con broker (p.ej. `CAPITALCOM:NAS100`), sin depender de qué proveedor
tenga el activo en la watchlist. Salida: filas JSON + `BEST_SYMBOL=<full>` de la fila activa.
Lo usa `draw_all.py` para auto-detectar el símbolo del scan.

Nota (verificado): el panel de la lista debe leerse en la MISMA sesión CDP en la que se abre
(el widgetbar se cierra solo al cambiar de símbolo entre llamadas).

## Uso típico

- "¿Qué activos tengo en la lista de seguimiento?" → ejecutar el script y listar.
- "Analiza los activos de mi watchlist" → leer la lista, y para cada símbolo correr
  `coin_analysis`/`multi_timeframe_analysis` del MCP o el scan correspondiente.

## Notas

- El texto incluye agrupaciones (NZD, GBP, EUR, AUD...) y, al final, el símbolo activo del
  chart con su panel de detalle. Filtrar solo las filas con estructura
  `Símbolo / Última / Cbo / Cambio%`.
- El símbolo actual del chart (p.ej. `CAPITALCOM:NAS100`) aparece al final con su detalle
  (Mercado abierto, descripción), no como fila de watchlist.
- Para el broker NAS100 preferir `CAPITALCOM:NAS100` (dibujos persistentes, ver:
  `tradingview-drawings` y `scan-nas100`).

## Relacionadas

- `tradingview-debug-launch` — CDP 9222.
- `scan-nas100` — análisis SMC del NAS100.
- `tradingview-drawings` — dibujo de niveles.
