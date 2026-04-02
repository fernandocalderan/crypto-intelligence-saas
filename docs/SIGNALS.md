# Signals

## Riesgo principal

Un dashboard sin señales bien definidas no tiene valor comercial claro. El scoring debe estar definido antes de sofisticar la infraestructura.

## MVP implementado: 5 señales

1. `Volume Spike`
2. `Range Breakout`
3. `Funding Extreme`
4. `OI Divergence`
5. `Liquidation Cluster`

## Módulos

Los detectores viven en `packages/signal-engine/`:

- `volume_spike.py`
- `range_breakout.py`
- `funding_extreme.py`
- `oi_divergence.py`
- `liquidation_cluster.py`
- `scoring.py`
- `formatter.py`
- `engine.py`

Cada detector expone `detect(data) -> signal | None`.

## Framework de scoring

- `score` se calcula de `1` a `10`
- `confidence` se deriva del score y de la evidencia disponible
- `engine.py` ordena señales por score/confidence y elimina duplicados por activo, tipo y timeframe

## Output estándar

Cada señal devuelve:

- `id`
- `signal_key`
- `asset_symbol`
- `signal_type`
- `timeframe`
- `direction`
- `score`
- `confidence`
- `thesis`
- `evidence`
- `source`
- `generated_at`

## Inputs usados por el MVP

- precio y cambio 24h
- volumen 24h vs media
- rango de 20 días
- funding rate y z-score de funding
- variación de open interest
- liquidaciones 1h vs media
- momentum score

## Lógica resumida

- `Volume Spike`: activa cuando el volumen supera claramente su baseline y el precio acompaña.
- `Range Breakout`: activa cuando el precio sale del rango de 20 días con margen suficiente.
- `Funding Extreme`: activa en extremos de funding y actúa de forma contrarian.
- `OI Divergence`: activa cuando precio y open interest divergen de forma relevante.
- `Liquidation Cluster`: activa tras limpieza agresiva de posicionamiento en una sola dirección.

## Endpoint

- `GET /signals/live`
- `GET /signals` se mantiene como alias compatible

## Rollback

Cada señal se puede desactivar individualmente desde config/env:

- `ENABLE_VOLUME_SPIKE_SIGNAL`
- `ENABLE_RANGE_BREAKOUT_SIGNAL`
- `ENABLE_FUNDING_EXTREME_SIGNAL`
- `ENABLE_OI_DIVERGENCE_SIGNAL`
- `ENABLE_LIQUIDATION_CLUSTER_SIGNAL`

También se puede forzar el dataset mock con `SIGNAL_ENGINE_USE_MOCK_DATA=true`.

## Regla práctica

Si no puedes explicar en una frase por qué la señal existe y por qué su score sube o baja, todavía no está lista para venderse.
