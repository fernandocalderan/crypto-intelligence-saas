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

### market_snapshots

- `id`
- `asset_id`
- `source`
- `timeframe`
- `open_price`
- `high_price`
- `low_price`
- `close_price`
- `price_usd`
- `change_24h`
- `volume_24h`
- `avg_volume_24h`
- `range_high_20d`
- `range_low_20d`
- `funding_rate`
- `funding_zscore`
- `open_interest`
- `oi_change_24h`
- `long_liquidations_1h`
- `short_liquidations_1h`
- `avg_liquidations_1h`
- `momentum_score`
- `raw_payload`
- `captured_at`
- `created_at`

### subscriptions

- `id`
- `user_id`
- `provider`
- `plan`
- `status`
- `stripe_customer_id`
- `stripe_subscription_id`
- `stripe_checkout_session_id`
- `stripe_price_id`
- `cancel_at_period_end`
- `current_period_end`
- `created_at`
- `updated_at`

## Relaciones

- un `asset` puede tener muchas `signals`
- un `asset` puede tener muchos `market_snapshots`
- un `user` puede recibir muchas `signals`
- un `user` puede tener muchas `subscriptions`
- una `signal` referencia un `asset` y opcionalmente un `user`

## Ingesta

- Binance y Bybit se normalizan hacia un `MarketSnapshot`
- `normalizer.py` consolida OHLCV, ticker, funding, open interest y fallback de liquidaciones
- `scheduler.py` ejecuta jobs cada `MARKET_DATA_SCHEDULE_MINUTES`
- `repository.py` persiste snapshots históricos y expone el último snapshot por activo
- `GET /market/latest` devuelve la última foto normalizada disponible por símbolo
- `subscriptions` persiste checkout, plan y estado efectivo del acceso del usuario
- si la ingesta o la base fallan, el sistema puede degradar a datos mock con `MARKET_DATA_USE_MOCK_FALLBACK=true`
