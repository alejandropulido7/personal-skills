---
name: create-trading-strategy
description: Crea una nueva estrategia de trading de principio a fin mediante una entrevista estructurada y profunda. Use when the user asks to create a new strategy, define a new trading system, or generate a strategy skill. Hace preguntas sobre concepto (SMC, ORB, CTR, ICT, indicadores, price action), activos, temporalidades, sesión/horario, condiciones de entrada, SL/TP, gestión de riesgo y reglas de salida; valida inconsistencias; y genera el YAML de estrategia + una skill de rutina (como scan_nas100) que usa las skills/MCP de tradingview (drawings, watchlist, ohlcv) para analizar y marcar el gráfico.
---

# create-trading-strategy — Generador de estrategias de trading

Convierte una idea de trading en una estrategia **completa, validada y ejecutable** como una
skill de rutina estilo `scan_nas100`. NO inventes reglas: entrevista al usuario, valida, y solo
entonces genera el YAML + la skill.

## Flujo (obligatorio, en orden)

1. **Abrir con las bases** — preguntar el nombre de la estrategia, activo(s) objetivo y el
   concepto central (SMC / ORB / CTR / ICT / indicadores / price action / breakout / otro).
2. **Cuestionario profundo** — recorrer TODAS las dimensiones de `reference/questionnaire.md`.
   Una pregunta por vez o en bloques cortos (máx 4-5 por mensaje) para no abrumar.
3. **Profundizar** — si una respuesta es vaga o incompleta ("condiciones claras", "TP lógico"),
   hacer preguntas de seguimiento específicas hasta que sea operativa.
4. **Validar consistencia** — revisar cada respuesta contra `reference/consistency_checks.md`.
   Si hay contradicciones o reglas inviables, **advertir y proponer la corrección** antes de
   continuar (no seguir con reglas rotas).
5. **Resumir y confirmar** — presentar el diseño completo (resumen) y pedir confirmación
   explícita antes de generar archivos.
6. **Generar** — crear:
   - `~/.gemini/config/trading-strategies/<Nombre>.yaml` (fuente de verdad de reglas).
   - `~/.gemini/config/skills/<nombre-skill>/SKILL.md` (rutina, siguiendo
     `reference/skill_template.md`).
   - (Opcional) scripts de análisis en `<nombre-skill>/scripts/` reutilizando los existentes.
7. **Avisar reinicio** — las skills nuevas requieren reiniciar agy.

## Reglas de generación

- **La skill generada DEBE consumir las skills/MCP existentes**, no reinventar:
  - `tradingview-watchlist` → detectar el símbolo real desde la watchlist (detect_nas100.py).
  - `tradingview-ohlcv` → extraer OHLCV (ohlcv_extract.py) y analizar estructura (pandas/numpy).
  - `tradingview-drawings` → dibujar niveles (draw_all.py y módulos).
  - `tradingview-debug-launch` → abrir TV normal; debug solo para scripting puntual.
  - MCP `tradingview-mcp` → coin_analysis / multi_timeframe_analysis / yahoo_price para
    contexto o activos que la watchlist no cubra.
- El YAML de estrategia **debe** incluir al menos: `strategy_name`, `asset(s)`, `symbol`,
  `timeframes`, `sessions`, `context_rules`, `entry_rules`, `risk_management` y
  `chart_checklist` (para marcar lo analizado/pendiente en el gráfico).
- La skill de rutina debe tener el pipeline: leer estrategia → extraer OHLCV → evaluar reglas →
  dibujar niveles + checklist → reporte técnico (Entrada/SL/TP/RR) → (opcional) screenshot.
- Poner gotchas reales (LineToolRectangle no LineToolRect, anclaje de rays a la vela del swing,
  recolección en 2 pasos al borrar, fontsize 16 y color #2196f3 del checklist, persistencia por
  broker: preferir CAPITALCOM:NAS100).
- Si la estrategia es multi-activo o usa la watchlist, incluir el paso de auto-detección de
  símbolo por activo.

## Comportamiento ante inconsistencias

- **Detectar** con `reference/consistency_checks.md`.
- **Comunicar** con formato claro:
  `⚠️ Inconsistencia: [regla A] vs [regla B]. → [por qué] → [corrección sugerida]`.
- **Decidir**: si es grave (imposible de operar), no generar hasta resolverla; si es menor,
  aplicar la corrección razonable y avisarlo.

## Conceptos

- Glosario de conceptos (SMC, ORB, CTR, ICT, etc.) en `reference/concepts.md` — úsalo para
  explicar opciones y proponer el que encaje con lo que el usuario describe.

## Relacionadas

- `scan-nas100` — ejemplo funcional de skill de estrategia generada.
- `tradingview-drawings`, `tradingview-watchlist`, `tradingview-ohlcv`, `tradingview-debug-launch`
  — skills consumidas por las rutinas generadas.
