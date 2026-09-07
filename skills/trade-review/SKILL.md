---
name: trade-review
description: Rutina de revisión posterior (post-mortem) de operaciones de trading sugeridas o ejecutadas. Extrae el OHLCV reciente de TradingView, analiza la trayectoria del precio desde el gatillo/entrada, determina si se activó el setup, si tocó TP o SL, o si permanece en curso, calcula métricas de rendimiento (MFE, MAE, R:R alcanzado, duración del trade) y anota el gráfico de TradingView Desktop con el resultado. Use when the user asks to review a previous setup, evaluate trade performance post-entry, verify execution outcome, or audit strategy efficiency.
---

# trade-review — Revisión Posterior de Operaciones (Post-Mortem)

Rutina completa y matemática para auditar el desempeño de las estrategias sugeridas tras el paso del tiempo en la sesión. Permite verificar objetivamente si el setup se activó, cómo se comportó el precio frente a los niveles de Entrada, Stop Loss y Take Profit, y extraer aprendizajes clave para optimizar la gestión de riesgo.

## Propósito y Casos de Uso

- **Auditoría Post-Entrada:** Evaluar si el precio cumplió con el gatillo (MSS / vela envolvente) y alcanzó el objetivo de ganancia (TP) o el nivel de invalidación (SL).
- **Métricas de Eficiencia:**
  - **MFE (Maximum Favorable Excursion):** Cuánto corrió a favor el trade en puntos y en múltiplos de R antes de cerrar o revertir.
  - **MAE (Maximum Adverse Excursion):** Cuánto drawdown o retroceso en contra soportó la posición.
  - **Duración:** Cantidad de velas (5m / 15m) y minutos transcurridos en la operación.
  - **R:R Realizado:** Rendimiento exacto obtenido en relación al riesgo asumido.
- **Retroalimentación Visual:** Inyectar una etiqueta / badge informativo en TradingView Desktop con el balance de la operación.

## Scripts Disponibles

| Script | Ubicación | Descripción |
|---|---|---|
| `review_trade.py` | `trade-review/scripts/` | Evalúa matemáticamente el trade desde `/tmp/nas100_levels.json` o parámetros CLI, calcula MFE/MAE/PnL y genera el reporte. |
| `ohlcv_extract.py` | `tradingview-ohlcv/scripts/` | Extrae las velas recientes desde TradingView Desktop para contar con el histórico completo. |

## Pipeline de Ejecución

### 1. Actualizar Datos de Mercado (OHLCV)
Ejecutar la extracción para obtener las velas más recientes de la sesión:
```bash
python3 "${SKILLS_DIR:-${HOME}/.hermes/skills}/tradingview-ohlcv/scripts/ohlcv_extract.py"
```

### 2. Ejecutar la Revisión del Trade
Ejecutar `review_trade.py` apuntando al archivo de niveles de la estrategia analizada:
```bash
python3 "${SKILLS_DIR:-${HOME}/.hermes/skills}/trade-review/scripts/review_trade.py" --levels /tmp/nas100_levels.json --draw
```

O especificando parámetros manuales:
```bash
python3 "${SKILLS_DIR:-${HOME}/.hermes/skills}/trade-review/scripts/review_trade.py" \
  --side long \
  --entry 29105.0 \
  --sl 29075.0 \
  --tp 29165.0 \
  --draw
```

### 3. Reporte de Resultados
El script genera un reporte estructurado que incluye:
1. **Estado de Activación:** Si el precio rompió el nivel de entrada o gatillo y en qué timestamp exacto.
2. **Resultado Final:** `TP_HIT` (Ganancia completa), `SL_HIT` (Pérdida acotada), `OPEN` (Posición activa en mercado), o `NOT_TRIGGERED`.
3. **Métricas Clave:**
   - PnL en puntos y R realizado.
   - MFE (Máxima ganancia flotante alcanzada).
   - MAE (Máximo drawdown soportado).
   - Duración de la posición.
4. **Visualización en TradingView:** Si `--draw` está habilitado, añade el badge de resultado sobre la barra de entrada en el gráfico.

## Integración con Otras Skills
- Consume datos generados por `scan-nas100`, `scan-smc`, `scan-ict`, `scan-orb` y `scan-crt`.
- Guarda el resultado evaluado en `/tmp/trade_review_result.json` para histórico o análisis estadístico posterior.
