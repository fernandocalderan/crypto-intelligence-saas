# Crypto Intelligence SaaS

Base monorepo para un SaaS de inteligencia crypto con frontend en Next.js, backend en FastAPI, market data normalizado, signal engine MVP y alertas inmediatas para usuarios `pro`.

La salida del producto ya no se limita a alertas técnicas crudas. El backend ahora trabaja en dos capas:

- `señales individuales`: piezas técnicas base producidas por los 5 detectores
- `setups de confluencia`: agrupaciones por activo que combinan varias señales y deciden si merece la pena empujar una alerta PRO

Encima de eso, la capa de presentación transforma la lectura final en una `Señal PRO` o un `Setup PRO` con:

- estado operativo
- resumen accionable
- confirmaciones
- plan de acción con niveles indicativos
- warnings de calidad del dato

## Stack

- `apps/web`: Next.js + Tailwind + App Router
- `apps/api`: FastAPI + SQLAlchemy + Postgres + APScheduler
- `packages/core`: espacio reservado para contratos compartidos
- `packages/signal-engine`: detectores y scoring del MVP
- `infra/docker`: Dockerfiles de frontend y backend
- `infra/nginx`: reverse proxy base para futuro despliegue en VPS
- `infra/scripts`: scripts de bootstrap y desarrollo local
- `docs`: documentacion funcional y tecnica

## Arranque rapido local

Primer comando recomendado:

```bash
npm run dev
```

Que hace:

- crea `.env` a partir de `.env.example` si no existe
- instala dependencias Node en la raiz si faltan
- crea `apps/api/.venv` e instala dependencias Python si faltan
- arranca FastAPI en `http://localhost:8000`
- arranca Next.js en `http://localhost:3000`

Matiz importante:

- para probar persistencia real, scheduler y alertas push, necesitas Postgres disponible
- la forma mas simple de tener el stack completo es `docker compose up --build`

## Rutas utiles

Web:

- landing: `http://localhost:3000/`
- login: `http://localhost:3000/login`
- signup: `http://localhost:3000/signup`
- dashboard: `http://localhost:3000/dashboard`
- pricing: `http://localhost:3000/pricing`

API:

- health: `http://localhost:8000/health`
- activos: `http://localhost:8000/assets`
- snapshots de mercado: `http://localhost:8000/market/latest`
- senales live: `http://localhost:8000/signals/live`
- setups live: `http://localhost:8000/signals/setups`
- historico de setups: `http://localhost:8000/signals/setups/history`
- feed con gating por plan: `http://localhost:8000/signals/feed`
- auth: `http://localhost:8000/auth/login`, `http://localhost:8000/auth/register`, `http://localhost:8000/auth/me`
- billing: `http://localhost:8000/billing/checkout`, `http://localhost:8000/billing/confirm`
- alertas: `http://localhost:8000/alerts/me`, `http://localhost:8000/alerts/telegram/connect`, `http://localhost:8000/alerts/telegram/test`, `http://localhost:8000/alerts/telegram/connect-instructions`, `http://localhost:8000/alerts/preferences`
- debug alertas: `http://localhost:8000/alerts/debug/me`

## Arranque con Docker

```bash
docker compose up --build
```

Servicios:

- `web`: Next.js en `3000`
- `api`: FastAPI en `8000`
- `postgres`: Postgres en `5432`

## Flujo actual del producto

El sistema ya no es solo pull.

Hoy funciona asi:

1. el scheduler de market data genera snapshots normalizados
2. el backend calcula senales activas con `packages/signal-engine`
3. las senales nuevas se persisten en Postgres con hash de deduplicacion
4. si `ENABLE_CONFLUENCE_ENGINE=true`, el backend agrupa esas senales por activo y genera setups de confluencia
5. los setups `EXECUTABLE` se materializan en la tabla `setups` y pasan a tener lifecycle
6. el scheduler actualiza su estado automaticamente con cada nuevo snapshot (`ACTIVE`, `TP1_HIT`, `TP2_HIT`, `INVALIDATED`, `EXPIRED`)
7. el canal push usa setups por defecto; las senales individuales quedan como capa base y como feed interno
8. las señales y setups se transforman a una vista PRO antes de salir por API o Telegram
9. usuarios `pro` y `pro_plus` con Telegram configurado reciben push solo cuando hay setup elegible
10. usuarios `free` siguen viendo un feed limitado en el dashboard
11. el dashboard sigue pudiendo consultar feed on-demand aunque las alertas esten desactivadas

## Señal base vs Setup PRO

La señal base del engine sigue siendo un detector heurístico.

Esa capa base sigue existiendo para:

- persistencia técnica
- feed interno
- inspección del motor
- compatibilidad legacy

Por encima, el motor de confluencia crea setups por activo:

- `Trend Continuation`
- `Squeeze Reversal`
- `Positioning Trap`

Y luego la capa `PRO` añade:

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

No cambia la persistencia central de `signals`. Cambia la forma en que se decide qué lectura merece salir como alerta vendible.

## Historico de setups

El motor de setups ya no es solo runtime.

Ahora existe una tabla `setups` para materializar setups `EXECUTABLE` y seguir su evolucion:

- `ACTIVE`
- `TP1_HIT`
- `TP2_HIT`
- `INVALIDATED`
- `EXPIRED`

La persistencia actual prioriza producto y tracking:

- solo se materializan setups ejecutables
- se evita duplicar setups activos equivalentes por `asset + setup_key + direction`
- el scheduler actualiza el estado usando el ultimo precio normalizado por activo
- el dashboard muestra una seccion `Historico de Setups`
- `free` ve teaser
- `pro` y `pro_plus` ven detalle completo con lifecycle y niveles

## Motor de confluencia

Familias operativas actuales:

- Continuación:
  - `volume_spike`
  - `range_breakout`
- Reversión / squeeze:
  - `funding_extreme`
  - `liquidation_cluster`
- Posicionamiento fallido:
  - `oi_divergence`

Setups implementados:

- `trend_continuation`
  - requiere `volume_spike` + `range_breakout` en la misma dirección
- `squeeze_reversal`
  - requiere `funding_extreme` + `liquidation_cluster` en la misma dirección operativa
- `positioning_trap`
  - requiere `oi_divergence`
  - gana prioridad si además coincide con `funding_extreme` o con contexto de breakout opuesto fallando

Scoring compuesto del setup:

- 50% media de score de señales base
- 20% media de confianza agregada
- 20% contexto de mercado
- 10% bonus por confluencia fuerte

Penalizaciones actuales:

- mock contamination crítica
- liquidaciones no verificadas
- OI inferido
- timeframe desalineado como warning operacional, no como bloqueo duro del score

## Estados operativos

- `EXECUTABLE`: score alto, confirmaciones suficientes, sin contaminación mock crítica y con niveles indicativos disponibles.
- `WATCHLIST`: setup interesante, pero aún no conviene tratarlo como entrada inmediata.
- `WAIT_CONFIRMATION`: hay tesis, pero faltan confirmaciones de flujo o estructura.
- `DISCARD`: señal demasiado débil o con calidad de dato insuficiente para sostener una lectura PRO.

Regla de producto importante:

- una señal contaminada por mock nunca sale como `EXECUTABLE`

## Alertas inmediatas

Canal actual:

- Telegram como canal prioritario

Canal preparado:

- email, detras de flag y aun sin proveedor real

Reglas base:

- solo `pro` y `pro_plus` reciben alertas push
- thresholds globales por defecto:
  - `ALERT_MIN_SCORE=6.5`
  - `ALERT_MIN_CONFIDENCE=0.55`
- thresholds del motor de setups:
  - `MIN_SETUP_SCORE=6.5`
  - `MIN_SETUP_CONFIDENCE=55`
- el dashboard muestra el threshold configurado por el usuario y el threshold efectivo real del push
- deduplicacion por hash con ventana temporal de `5` minutos
- por defecto, Telegram ya no envía señales individuales
- para volver al comportamiento legacy:
  - `ENABLE_CONFLUENCE_ENGINE=false`
  - `ALERT_ON_INDIVIDUAL_SIGNALS=true`
- si falta `TELEGRAM_BOT_TOKEN`, el sistema registra fallo y sigue funcionando

UI actual:

- el dashboard incluye una card de `Alertas PRO`
- `free` ve upgrade prompt
- `pro` puede guardar `telegram_chat_id`, activar/desactivar canales, definir thresholds y revalidar Telegram
- el feed muestra estado operativo, confirmaciones, plan y warnings de calidad
- `pro_plus` mantiene el mismo detalle y un hook reservado para seguimiento futuro

## Diagnostico de alertas Telegram

El pipeline ahora deja trazabilidad suficiente para saber por que una alerta no salio.

Qué revisar:

1. `GET /alerts/debug/me`
2. logs del backend en cada tick del scheduler
3. estado de `alert_deliveries`
4. card `Alertas PRO` en `/dashboard`

El endpoint debug devuelve, sin secretos:

- plan actual
- si el usuario puede recibir alertas
- si Telegram esta disponible en runtime
- si el bot esta configurado
- si la suscripcion Telegram esta activa
- si hay `telegram_chat_id`
- thresholds efectivos
- ultimo envio `sent`
- ultimo envio `failed`
- ultimo error conocido
- numero de deliveries recientes
- numero de señales recientes elegibles

Skip reasons y causas visibles en logs:

- `skipped_plan`
- `skipped_no_chat_id`
- `skipped_channel_disabled`
- `skipped_threshold`
- `skipped_duplicate`

Errores Telegram que ahora se distinguen:

- `bot_not_started`
- `invalid_chat_id`
- `unauthorized_bot_token`
- `telegram_http_error`
- `timeout`

Causas tipicas de fallo:

- `Bad Request: chat not found`
  Suele significar que el usuario no pulso `Start` en el bot o que el `chat_id` guardado no corresponde a ese bot.
- `Telegram bot token not configured`
  El canal estaba habilitado en algun momento, pero el entorno no tenia `TELEGRAM_BOT_TOKEN` cargado.
- `skipped_threshold`
  Hay señales nuevas, pero no superan el umbral efectivo del usuario/canal.
- `skipped_duplicate`
  Ya existe `alert_delivery` para la misma señal, usuario y canal.

Checklist corto de validacion:

1. comprobar `ENABLE_ALERTS=true`
2. comprobar `ENABLE_TELEGRAM_ALERTS=true`
3. comprobar `TELEGRAM_BOT_TOKEN` presente
4. abrir `/alerts/debug/me`
5. verificar que el plan no sea `free`
6. verificar `telegram_subscription_active=true`
7. verificar `telegram_chat_id_present=true`
8. lanzar `POST /alerts/telegram/test`
9. revisar `last_error_code` y `last_error_known` si falla
10. revisar logs del scheduler para `alerts_candidates_count` y `alert_deliveries_*`

## Gating por plan

### free

Ve solo teaser:

- titular
- score
- dirección
- una línea de tesis
- CTA de upgrade

### pro

Ve señal completa:

- estado operativo
- resumen
- confirmaciones
- plan de acción
- warnings de calidad del dato

### pro_plus

Ve lo mismo que `pro` y además recibe un hook reservado para futuras actualizaciones de seguimiento.

## Variables de entorno relevantes

Core:

- `DATABASE_URL`
- `AUTH_SECRET`
- `NEXT_PUBLIC_API_URL`
- `INTERNAL_API_URL`

Market data:

- `MARKET_DATA_SYMBOLS`
- `MARKET_DATA_SCHEDULE_MINUTES`
- `MARKET_DATA_USE_MOCK_FALLBACK`
- `ENABLE_MARKET_DATA_SCHEDULER`
- `MARKET_DATA_RUN_INITIAL_SYNC`
- `ENABLE_BINANCE_MARKET_DATA`
- `ENABLE_BYBIT_MARKET_DATA`
- `ENABLE_COINGLASS_MARKET_DATA`

Alertas:

- `ENABLE_ALERTS`
- `ENABLE_TELEGRAM_ALERTS`
- `ENABLE_EMAIL_ALERTS`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_BOT_USERNAME`
- `ALERT_MIN_SCORE`
- `ALERT_MIN_CONFIDENCE`
- `ALERT_DEDUPE_WINDOW_MINUTES`
- `ALERT_MAX_PER_RUN`
- `ALERTS_PROCESS_ON_SCHEDULER`
- `ENABLE_CONFLUENCE_ENGINE`
- `ALERT_ON_INDIVIDUAL_SIGNALS`
- `MIN_SETUP_SCORE`
- `MIN_SETUP_CONFIDENCE`
- `SETUP_REQUIRE_NO_MOCK_FOR_EXECUTABLE`

Billing:

- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_PRICE_PRO`
- `STRIPE_PRICE_PRO_PLUS`
- `ENABLE_STRIPE_MOCK_CHECKOUT`

## Comandos utiles

```bash
npm run dev
docker compose up --build
npm run build:web
npm run lint:web
npm run install:api
PYTHONPATH=apps/api apps/api/.venv/bin/pytest tests -q
PYTHONPATH=apps/api apps/api/.venv/bin/python -m compileall apps/api
```

## Modelo actual

La base hoy incluye:

- `users`
- `assets`
- `market_snapshots`
- `signals`
- `setups`
- `subscriptions`
- `alert_subscriptions`
- `alert_deliveries`

Capacidades ya implementadas:

- ingesta desde Binance y Bybit con fallback mock
- feed de senales PRO con gating por plan
- endpoint de setups de confluencia para inspección operativa
- persistencia e historico de setups ejecutables con evolucion de estado
- persistencia real de senales para historico tecnico y alertas
- confluence engine para agrupar señales por activo y disparar setups de mayor calidad
- auth basica con cookie `ci_session`
- checkout Stripe con modo mock para desarrollo
- dashboard con `Setups PRO`, `Historico de Setups`, upgrade flow, configuracion de alertas y cards de señal enriquecidas
- tests minimos del sistema de alertas, `ProSignalView` y motor de confluencia

## Billing local

- si usas credenciales y `price_id` reales de Stripe, desactiva `ENABLE_STRIPE_MOCK_CHECKOUT`
- en desarrollo, `ENABLE_STRIPE_MOCK_CHECKOUT=true` permite probar registro, upgrade y acceso sin cobro real

## Smoke Test Telegram

1. define `TELEGRAM_BOT_TOKEN` y opcionalmente `TELEGRAM_BOT_USERNAME` en `.env`
2. arranca el stack con `npm run dev` o `docker compose up --build`
3. registra un usuario y súbelo a `pro` o `pro_plus`
4. abre Telegram, busca tu bot y pulsa `Start`
5. entra en `/dashboard`
6. en `Alertas PRO > Telegram`, pega tu `telegram_chat_id` y pulsa `Conectar Telegram`
7. activa `Activar alertas por Telegram` y guarda
8. pulsa `Enviar prueba`
9. verifica que el mensaje llegue al chat

Formato actual del mensaje Telegram:

- titular con activo, setup y estado operativo
- bloque de confluencia (`signal_keys` que componen el setup)
- resumen de la tesis
- score y confianza
- datos clave
- confirmaciones
- plan con niveles indicativos
- riesgo y calidad del dato

Matiz de producto:

- el mensaje Telegram ya no intenta vender “entrada automática”
- por defecto, Telegram empuja setups de confluencia, no señales individuales
- si la calidad del dato es degradada o hay contaminación mock, el mensaje lo dice explícitamente

Troubleshooting mínimo:

- si falta `TELEGRAM_BOT_TOKEN`, la UI mostrará `Telegram no disponible temporalmente`
- si el bot no fue iniciado, la prueba devolverá un mensaje para pulsar `Start`
- si el plan es `free`, el backend bloqueará conexión y prueba real
- si el `chat_id` es inválido, la API devolverá un error controlado sin romper el dashboard

## Documentacion relevante

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/DATA_MODEL.md](docs/DATA_MODEL.md)
- [docs/SIGNALS.md](docs/SIGNALS.md)
- [docs/alerts-system.md](docs/alerts-system.md)
- [TECHNICAL_CONTEXT.md](TECHNICAL_CONTEXT.md)

## Siguientes pasos recomendados

- introducir Alembic
- anadir webhooks Stripe para reconciliacion real
- conectar proveedor real de email
- evaluar retries/backoff para alertas
- anadir historico de performance agregado por setup y ratios win/loss
- sustituir liquidaciones mock por proveedor real
