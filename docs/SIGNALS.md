# Signals

## Objetivo de producto

El MVP ya no expone solo alertas técnicas crudas.

Cada lectura del motor se transforma en una `Señal PRO`: una vista más vendible y más útil operativamente que obliga a responder estas preguntas:

- qué está pasando
- qué importancia tiene
- si es ejecutable o no
- qué confirmaciones existen
- qué plan de acción indicativo tiene
- qué limitaciones de dato contaminan la lectura

## Señal base vs Señal PRO

### Señal base del engine

Sale directamente de `packages/signal-engine/` y mantiene estos campos:

- `asset_symbol`
- `signal_key`
- `signal_type`
- `timeframe`
- `direction`
- `score`
- `confidence`
- `thesis`
- `evidence`
- `source`
- `generated_at`

### Señal PRO

Se construye en la capa backend y añade:

- `headline`
- `execution_state`
- `execution_reason`
- `summary`
- `model_score`
- `confidence_pct`
- `thesis_short`
- `key_data`
- `confirmations`
- `action_plan`
- `data_quality_warnings`
- `is_mock_contaminated`
- `is_trade_executable`
- `detail_level`
- `pro_plus_follow_up`

La persistencia central de `signals` no cambia de forma agresiva. La señal PRO se deriva en tiempo de salida.

## Estados operativos

### `EXECUTABLE`

Solo si se cumple todo:

- `score >= 8.0`
- `confidence >= 75%`
- sin contaminación mock crítica
- con trigger e invalidación calculables
- con confirmaciones mínimas de flujo/estructura

### `WATCHLIST`

Señal interesante con estructura suficiente para seguirla, pero todavía no para tratarla como entrada inmediata.

### `WAIT_CONFIRMATION`

La tesis existe, pero faltan confirmaciones relevantes. Suele ser el estado normal cuando:

- el volumen sí acompaña
- el precio sí se mueve
- pero el OI, funding o la calidad del dato no terminan de confirmar

### `DISCARD`

Señal demasiado débil o demasiado degradada para venderse como lectura accionable.

## Confirmaciones

Las confirmaciones se derivan de `evidence_json` y del snapshot normalizado asociado.

Se devuelven con severidad:

- `positive`
- `warning`
- `negative`

Ejemplos:

- `✅ Volumen anómalo`
- `✅ Expansión direccional`
- `⚠ OI sin confirmación clara`
- `⚠ Volumen todavía justo`
- `⛔ Snapshot ausente`

## Warnings de calidad del dato

La capa PRO distingue entre:

- confirmaciones operativas
- warnings de calidad/procedencia del dato

Warnings actuales:

- `mock_contamination`
- `oi_inferred`
- `liquidations_unverified`
- `timeframe_misaligned`
- `snapshot_missing`

Regla de producto:

- si hay `mock_contamination`, la señal nunca sube a `EXECUTABLE`

## Plan de acción

El MVP genera un plan prudente, no un sistema de ejecución automática.

Campos:

- `action_now`
- `bias`
- `trigger_level`
- `invalidation_level`
- `tp1`
- `tp2`
- `levels_are_indicative`
- `note`

Los niveles salen de:

- precio actual
- cambio 24h
- rango 20d

Esto significa:

- son niveles indicativos
- no son precisión de scalping
- no sustituyen validación manual ni gestión de riesgo

## Detectores del MVP

Los detectores viven en `packages/signal-engine/`:

- `volume_spike.py`
- `range_breakout.py`
- `funding_extreme.py`
- `oi_divergence.py`
- `liquidation_cluster.py`

## Reglas resumidas por detector

- `Volume Spike`: exige volumen fuera de baseline y movimiento direccional.
- `Range Breakout`: exige salida del rango de 20 días con cierta expansión.
- `Funding Extreme`: usa lectura contrarian frente a extremos de funding.
- `OI Divergence`: detecta desequilibrio entre precio y open interest.
- `Liquidation Cluster`: intenta leer limpieza agresiva de posicionamiento.

## Gating por plan

### free

Solo recibe teaser:

- titular
- score
- dirección
- una frase de tesis
- CTA implícito de upgrade en UI

No ve:

- estado operativo
- confirmaciones
- plan
- warnings de calidad del dato

### pro

Ve la lectura completa:

- estado operativo
- resumen
- confirmaciones
- plan
- warnings

### pro_plus

Ve lo mismo que `pro` y además un `pro_plus_follow_up` reservado para futuras actualizaciones de seguimiento.

## Ejemplo de salida Telegram PRO

```text
🟠 SOL — Volume Spike
WAIT_CONFIRMATION · BEARISH · PRO

SOL imprime un spike de volumen con expansión direccional, pero el dato está contaminado por fallback mock y no conviene tratarlo como entrada inmediata.

Score: 9.4/10
Confianza: alta (88.9%)
Estado: WAIT_CONFIRMATION

Tesis:
Entrada de flujo y expansión, pero con confirmación incompleta.

Datos clave:
• Precio: $78.66
• Cambio 24h: -6.7%
• Volumen 24h: $3.0B
• Funding: -0.0001
• OI: -0.1%
• Base: 1D · binance+bybit+mock

Confirmaciones:
✅ Volumen anómalo
✅ Expansión direccional
⚠ OI sin confirmación clara

Plan:
• Acción: wait
• Bias: bearish
• Trigger: $78.42
• Invalidación: $80.50
• TP1 / TP2: $75.90 / $73.80

Riesgo / calidad del dato:
⛔ Parte del contexto usa fallback mock o defaults del MVP.
⚠ El timeframe de la señal no está perfectamente alineado con el snapshot base.
```

## Limitaciones reales del MVP

- sigue siendo un sistema heurístico
- no hay niveles institucionales ni precisión de execution algorítmica
- puede haber contaminación mock en snapshots y liquidaciones
- el timeframe del snapshot base es `1D`, mientras varias señales viven en `4H`, `8H` o `1H`
- el valor comercial está en la lectura priorizada y el descarte explícito, no en prometer exactitud falsa

## Rollback

Si la capa PRO rompe el feed o la UI:

1. revertir solo la capa de presentación
2. mantener intactos detectores, persistencia y scheduler
3. dejar Telegram en el formatter anterior hasta corregir
