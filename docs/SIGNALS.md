# Signals

## Riesgo principal

Un dashboard sin señales bien definidas no tiene valor comercial claro. El scoring debe estar definido antes de sofisticar la infraestructura.

## Propuesta MVP: 5 señales

1. `Momentum Breakout`
2. `Relative Strength`
3. `Capital Rotation`
4. `Funding + OI Stress`
5. `Mean Reversion Exhaustion`

## Framework de scoring

Cada señal debería devolver:

- `score` de 0 a 100
- `confidence` de 0 a 100
- `timeframe`
- `thesis`
- `invalidates_if`
- `generated_at`

## Inputs sugeridos

- estructura de precio
- volumen relativo
- open interest
- funding rate
- breadth del mercado
- performance relativa frente a BTC y ETH

## Regla práctica

Si no puedes explicar en una frase por qué la señal existe y por qué su score sube o baja, todavía no está lista para venderse.

