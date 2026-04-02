# Data Model

## Tablas iniciales

### users

- `id`
- `email`
- `password_hash`
- `plan`
- `is_active`
- `created_at`

### assets

- `id`
- `symbol`
- `name`
- `category`
- `is_active`
- `created_at`

### signals

- `id`
- `public_id`
- `asset_id`
- `user_id`
- `signal_type`
- `timeframe`
- `confidence`
- `score`
- `thesis`
- `created_at`

## Relaciones

- un `asset` puede tener muchas `signals`
- un `user` puede recibir muchas `signals`
- una `signal` referencia un `asset` y opcionalmente un `user`

