# Crypto Intelligence SaaS - Contexto Tecnico

Snapshot tecnico del repositorio a fecha 2026-04-02. Este documento esta pensado para adjuntarlo a otro proyecto GPT y que ese modelo pueda razonar sobre la herramienta, su arquitectura, sus contratos, su comportamiento runtime y sus limites sin asumir cosas incorrectas.

## 1. Definicion del proyecto

`crypto-intelligence-saas` es un monorepo para un SaaS de inteligencia de mercado crypto. El producto combina:

- una capa de marketing y conversion
- un dashboard con acceso restringido por plan
- un backend FastAPI para auth, billing, market data, senales y alertas
- un motor de senales MVP con 5 detectores
- un motor de confluencia que agrupa senales por activo para construir setups PRO
- una capa Postgres para persistir usuarios, assets, snapshots, senales, setups, suscripciones y entregas de alertas

La propuesta comercial actual no es trading automatico. Es una capa de senales crypto accionables con score, tesis, evidencia visible y, para `pro`, distribucion push por Telegram.

Desde 2026-04-02 la salida del producto ya no es una alerta tecnica cruda. El backend trabaja en dos niveles:

- `senal individual`: detector base persistido en `signals`
- `setup de confluencia`: agrupacion por activo que decide si merece una alerta push PRO

Sobre cualquiera de las dos capas, el backend construye una vista `PRO` con estado operativo, resumen, confirmaciones, plan indicativo y warnings de calidad del dato.

## 2. Alcance actual del sistema

Implementado hoy:

- landing, pricing, login, signup y dashboard en Next.js
- backend FastAPI con endpoints de auth, billing, market data, signals, alerts y tracking
- ingesta de market data desde Binance y Bybit
- punto de extension opcional para Coinglass, hoy en estado stub
- 5 detectores de senales:
  - `volume_spike`
  - `range_breakout`
  - `funding_extreme`
  - `oi_divergence`
  - `liquidation_cluster`
- motor de confluencia para:
  - `Trend Continuation`
  - `Squeeze Reversal`
  - `Positioning Trap`
- capa `ProSignalView` para transformar la senal base en salida de producto
- capa `setup_view.py` para transformar setups de confluencia en salida PRO
- persistencia real de senales en la tabla `signals`
- persistencia real de setups ejecutables en la tabla `setups`
- deduplicacion de senales por hash con bucket temporal
- sistema push+pull de alertas:
  - feed on-demand para dashboard
  - dispatch inmediato por Telegram para usuarios elegibles
- historico de setups con evolucion de estado visible en dashboard
- flujo de checkout Stripe con modo mock para desarrollo
- logica de restriccion por planes `free`, `pro` y `pro_plus`
- tests minimos del subsistema de alertas
- Dockerfiles y `docker-compose.yml`

No implementado o solo parcialmente implementado:

- no existe Alembic ni framework formal de migraciones
- no hay suite amplia de tests para auth, billing, market data y UI
- no hay funcionalidad real basada en Redis, aunque `REDIS_URL` exista
- no hay persistencia real de analitica de eventos
- no hay reconciliacion por webhooks de Stripe
- no hay proveedor real de email para alertas
- no hay ingesta real de liquidaciones desde Coinglass
- `packages/core` existe, pero aun no aporta codigo compartido relevante

## 3. Estructura del monorepo

```text
apps/
  api/                    backend FastAPI
  web/                    frontend Next.js (App Router)
packages/
  core/                   placeholder para contratos compartidos
  signal-engine/          detectores de senales y scoring en Python
infra/
  docker/                 Dockerfiles
  nginx/                  capa futura de reverse proxy
  scripts/                scripts de local/dev/container
docs/                     documentacion funcional y tecnica
tests/                    tests minimos del sistema de alertas
```

Matices importantes:

- `packages/signal-engine` no esta instalado como paquete Python.
- `apps/api/services/signal_engine.py` localiza ese directorio dinamicamente y lo inyecta en `sys.path`.
- El Dockerfile del API copia `packages/signal-engine` a `/app/packages/signal-engine` para que esa resolucion siga funcionando dentro del contenedor.

## 4. Arquitectura runtime

### 4.1 Aplicacion web

Stack:

- Next.js 14
- App Router
- React 18
- Tailwind CSS

Responsabilidades:

- renderizar las paginas de marketing
- renderizar el dashboard server-side
- guardar la sesion en cookie HTTP-only
- proxyear auth, checkout, alerts y tracking hacia el backend

Paginas clave:

- `/`
- `/pricing`
- `/login`
- `/signup`
- `/dashboard`

### 4.2 Aplicacion API

Stack:

- FastAPI
- SQLAlchemy 2
- Psycopg 3
- APScheduler
- httpx
- Stripe Python SDK

Responsabilidades:

- autenticacion y perfil de usuario
- feeds de senales con gating por plan
- ingesta y normalizacion de market data
- persistencia de snapshots y senales
- orquestacion de checkout Stripe
- configuracion y dispatch de alertas

Comportamiento al arrancar:

1. ejecuta `init_db()`
2. arranca el scheduler de market data si esta habilitado
3. lanza una sincronizacion inicial de market data si esta habilitada

Comportamiento al apagar:

- detiene el scheduler background de APScheduler

### 4.3 Base de datos

Datastore principal:

- Postgres

Modelo actual de inicializacion:

- el schema se crea con `Base.metadata.create_all()`
- `apps/api/db/init_db.py` aplica parches de compatibilidad sobre `signals`
- no hay migraciones formales
- se siembran assets por defecto al arrancar
- el plan legacy `starter` se normaliza a `free`

### 4.4 Motor de senales

El motor de senales vive en `packages/signal-engine` y es un motor de reglas simple.

Hace lo siguiente:

- recibe snapshots de mercado normalizados
- evalua todos los detectores habilitados
- elimina duplicados de runtime por `(asset_symbol, signal_key, timeframe)`
- ordena por `(score, confidence)` descendente

El backend añade encima:

- adaptacion a modelo persistible
- hash de deduplicacion temporal
- persistencia en `signals`
- transformacion a `ProSignalView`
- motor de confluencia que agrupa senales por activo
- clasificacion de setups con score compuesto
- pipeline de alertas que, por defecto, usa setups en lugar de senales individuales

## 5. Flujo end-to-end

### 5.1 Flujo del dashboard

1. El navegador pide `/dashboard`.
2. Next server component lee la cookie `ci_session`.
3. Next llama al backend mediante `apps/web/lib/api.ts`:
   - `/assets`
   - `/signals/setups`
   - `/signals/setups/history`
   - `/signals/feed`
   - `/market/latest`
   - `/alerts/me`
4. El backend intenta cargar los ultimos snapshots desde Postgres.
5. Si faltan snapshots o falla el acceso a DB, intenta ingesta live.
6. Si la ingesta tambien falla y el fallback esta habilitado, devuelve snapshots mock.
7. El signal engine calcula las senales activas sobre esos snapshots normalizados.
8. El backend transforma las señales a `ProSignalResponse` y los setups a `SetupResponse`.
9. La web muestra `Setups PRO` como bloque principal y `Señales base` como capa secundaria.
10. Si el usuario esta en `free`, el feed y el historico de setups se recortan a teaser.
11. Si el usuario esta en `pro`, ve setups completos, historico y señales completas.
12. Si el usuario esta en `pro_plus`, ve lo mismo y mantiene espacio reservado para seguimiento futuro.
13. La card `Alertas PRO` refleja estado, canales y thresholds del usuario autenticado.

### 5.2 Flujo push de alertas

1. APScheduler ejecuta `ingest_market_snapshots()` cada cierto intervalo.
2. Se generan snapshots normalizados y se persisten en `market_snapshots`.
3. El backend calcula senales sobre esos snapshots.
4. `signal_persistence.py` transforma las salidas del engine y persiste solo las nuevas.
5. Si `ENABLE_CONFLUENCE_ENGINE=true`, el backend usa las senales del ciclo para generar setups por activo.
6. La deduplicacion de senales usa hash sobre:
   - `asset_symbol`
   - `signal_key`
   - `timeframe`
   - `direction`
   - bucket temporal de `ALERT_DEDUPE_WINDOW_MINUTES`
7. Los setups `EXECUTABLE` se materializan en `setups`.
8. El scheduler actualiza el lifecycle de setups activos usando el ultimo precio por activo.
9. Si `ALERTS_PROCESS_ON_SCHEDULER=true`, `alert_engine.py` procesa las senales nuevas.
10. Por defecto, si el motor de confluencia esta habilitado y `ALERT_ON_INDIVIDUAL_SIGNALS=false`, el dispatch push usa setups de confluencia.
11. El anclaje de dedupe de entregas sigue reutilizando `alert_deliveries`, apoyandose en una senal nueva del setup como driver materializado.
12. Solo usuarios `pro` o `pro_plus` con suscripciones activas y canales configurados son elegibles.
13. Se crea `alert_deliveries` en estado `pending`.
14. Se intenta el envio por Telegram o email.
15. La entrega se marca como `sent` o `failed`.

Matiz importante:

- el dashboard y `signals/feed` siguen trabajando con senales individuales enriquecidas
- Telegram usa setups de confluencia por defecto
- el modo legacy puede restaurarse con:
  - `ENABLE_CONFLUENCE_ENGINE=false`
  - `ALERT_ON_INDIVIDUAL_SIGNALS=true`

### 5.3 Flujo de autenticacion

1. La web hace POST a `POST /api/auth/register` o `POST /api/auth/login`.
2. La route handler de Next reenvia la peticion a FastAPI.
3. El backend devuelve token firmado y perfil de usuario.
4. Next guarda el token en `ci_session` como cookie HTTP-only.
5. Los server components reutilizan esa cookie para pedir `/auth/me`, `/signals/feed`, `/alerts/me` y endpoints de billing.

### 5.4 Flujo de billing

1. El usuario hace click en el CTA del plan desde pricing.
2. El frontend hace POST a `POST /api/billing/checkout`.
3. Next lee la cookie `ci_session` y reenvia el token a FastAPI.
4. FastAPI crea una suscripcion pendiente y devuelve una URL de checkout.
5. En modo mock, esa URL vuelve a `/dashboard?checkout=success&session_id=...`.
6. El dashboard detecta `checkout=success`, llama a `/billing/confirm` y actualiza el plan del usuario si la confirmacion es correcta.

Limitacion importante:

- aun no existe una fuente de verdad basada en webhooks
- la activacion real de la suscripcion depende hoy de la confirmacion explicita via `/billing/confirm`

### 5.5 Flujo de configuracion de alertas

1. El usuario autenticado entra en `/dashboard`.
2. La web llama a `GET /api/alerts/me`.
3. Si es `free`, la UI muestra upgrade prompt y no permite activar alertas.
4. Si es `pro` o `pro_plus`, puede:
   - conectar `telegram_chat_id`
   - activar o desactivar Telegram
   - dejar email desactivado o preparado
   - ajustar `min_score`
   - ajustar `min_confidence`
5. Next proxyea a:
   - `GET /alerts/me`
   - `POST /alerts/telegram/connect`
   - `POST /alerts/preferences`

## 6. Modulos backend

### 6.1 Routers FastAPI

Rutas implementadas:

- `GET /`
- `GET /health`
- `GET /assets`
- `GET /market/latest`
- `GET /signals`
- `GET /signals/live`
- `GET /signals/setups`
- `GET /signals/setups/history`
- `GET /signals/feed`
- `GET /alerts/me`
- `GET /alerts/telegram/connect-instructions`
- `POST /alerts/telegram/connect`
- `POST /alerts/telegram/test`
- `POST /alerts/preferences`
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /billing/checkout`
- `POST /billing/confirm`
- `POST /events/track`

### 6.2 Implementacion de auth

La auth es custom. No es JWT.

Detalles:

- el hash de password usa `pbkdf2_hmac("sha256")`
- iteraciones: `390_000`
- el token es un payload firmado con HMAC-SHA256
- el payload contiene:
  - `sub`
  - `email`
  - `exp`
- el TTL es de 14 dias

Implicaciones:

- la auth es sencilla y autocontenida
- no hay refresh tokens
- no hay proveedor externo de identidad
- la validez del token depende totalmente de `AUTH_SECRET`

### 6.3 Implementacion de billing

Comportamiento del servicio:

- solo `pro` y `pro_plus` usan checkout
- `free` nunca hace checkout
- las filas de `subscriptions` se crean o actualizan via upsert
- el campo `user.plan` se actualiza directamente al confirmar una suscripcion activa

Modos:

- modo Stripe real si hay `STRIPE_SECRET_KEY` valido y `price_id` reales
- modo mock si:
  - `ENABLE_STRIPE_MOCK_CHECKOUT=true`, o
  - las credenciales siguen pareciendo placeholders

### 6.4 Servicio de market data

`apps/api/services/market_data/` contiene:

- `binance_client.py`
- `bybit_client.py`
- `coinglass_client.py`
- `normalizer.py`
- `repository.py`
- `scheduler.py`
- `__init__.py` como capa de orquestacion

La salida normalizada incluye:

- OHLC
- precio y cambio 24h
- volumen 24h y volumen medio
- rango de 20 dias
- funding rate y funding z-score derivado
- open interest y variacion de OI
- liquidaciones 1h
- momentum score
- payload raw de proveedores

Detalles importantes de implementacion:

- `funding_zscore` hoy es heuristico, no estadistico:
  - `abs(funding_rate) / 0.01`
- las liquidaciones normalmente salen de defaults, porque Coinglass aun no esta integrado
- la variacion de OI sale del proveedor si existe; si no, se intenta inferir desde el snapshot previo en DB; si tampoco, se usan defaults
- `source` es una cadena con proveedores concatenados por `+` y puede incluir `mock`

### 6.5 Persistencia y runtime de senales

Modulos clave:

- `apps/api/services/signal_engine.py`
- `apps/api/services/signal_persistence.py`
- `apps/api/services/pro_signal_view.py`

Comportamiento actual:

1. el runtime calcula payloads de detector con `compute_signal_payloads()`
2. la capa `ProSignalView` transforma esas salidas a un contrato de producto
3. el feed de API sigue pudiendo responder on-demand
4. el scheduler persiste las senales nuevas en `signals`
5. las senales persistidas se usan para el pipeline de alertas y como historico tecnico

Consecuencias:

- el dashboard no depende de leer `signals` para funcionar
- el sistema puede seguir degradando a modo pull si las alertas se desactivan
- la persistencia ya existe, pero el frontend principal sigue leyendo feed on-demand

Contrato de salida actual por senal:

- campos base heredados:
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
- campos PRO añadidos:
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

Regla de producto:

- el plan `free` conserva solo teaser y no recibe estado operativo, plan ni warnings

### 6.6 Motor de confluencia

Modulos clave:

- `packages/signal-engine/confluence.py`
- `packages/signal-engine/setup_scoring.py`
- `apps/api/services/confluence_engine.py`
- `apps/api/services/setup_view.py`
- `apps/api/services/setup_engine.py`

Reglas implementadas:

- `Trend Continuation`
  - requiere `volume_spike` + `range_breakout`
- `Squeeze Reversal`
  - requiere `funding_extreme` + `liquidation_cluster`
- `Positioning Trap`
  - requiere `oi_divergence`
  - gana peso si coincide con `funding_extreme`
  - tambien puede incorporar contexto de breakout opuesto fallando

Scoring compuesto del setup:

- 50% score medio de senales base
- 20% confianza agregada
- 20% contexto de mercado
- 10% bonus por confluencia fuerte

Penalizaciones:

- `mock_contamination`
- `liquidations_unverified`
- `oi_inferred`
- `snapshot_missing`

Matiz importante:

- `timeframe_misaligned` sigue generando warning y penaliza confianza
- no se usa como bloqueo duro del score porque es una limitacion estructural del snapshot agregado `1D`

Persistencia y lifecycle:

- solo los setups `EXECUTABLE` e `is_trade_executable=true` se materializan
- la tabla `setups` guarda score, confidence, niveles, resumen y snapshot_data
- estados soportados:
  - `ACTIVE`
  - `TP1_HIT`
  - `TP2_HIT`
  - `INVALIDATED`
  - `EXPIRED`
- por ahora el dedupe de setups persistidos es pragmatico:
  - no crea un nuevo setup si ya existe uno activo con el mismo `asset_symbol + setup_key + direction`
- la expiracion automatica actual usa una ventana fija de 72 horas

### 6.7 Motor de alertas

Modulos clave:

- `apps/api/services/alert_engine.py`
- `apps/api/services/telegram_service.py`
- `apps/api/services/email_alert_service.py`

Reglas de negocio implementadas:

- solo `pro` y `pro_plus` reciben alertas
- `free` no recibe push
- thresholds globales por defecto:
  - `ALERT_MIN_SCORE=6.5`
  - `ALERT_MIN_CONFIDENCE=0.55`
- thresholds del motor de setups:
  - `MIN_SETUP_SCORE=6.5`
  - `MIN_SETUP_CONFIDENCE=55`
- `0.55` de confianza se interpreta como `55%`
- el threshold efectivo de push para setups es `max(subscription.*, MIN_SETUP_*)`
- no se reenviara la misma senal al mismo usuario y mismo canal
- la deduplicacion de envio descansa en `alert_deliveries` con unique por:
  - `signal_id`
  - `user_id`
  - `channel`

Canales:

- Telegram: implementado con `httpx` contra Bot API
- Email: stub preparado, detras de flag, sin proveedor real

Salida push actual:

- Telegram recibe un setup PRO por defecto
- las senales individuales siguen pudiendo enviarse solo en modo legacy
- el mensaje incluye:
  - titular
  - tipo de setup
  - confluencia base
  - estado operativo
  - score y confianza
  - tesis
  - datos clave
  - confirmaciones
  - plan indicativo
  - warnings de riesgo/calidad

Tolerancia a fallos:

- si falta `TELEGRAM_BOT_TOKEN`, se loguea warning y el scheduler continua
- si falla un envio, se registra `failed` y se sigue con el resto
- si un usuario no tiene el canal configurado, no se intenta enviar
- `telegram_service.py` ahora diferencia y clasifica:
  - `bot_not_started`
  - `invalid_chat_id`
  - `unauthorized_bot_token`
  - `telegram_http_error`
  - `timeout`
- hay 1 retry rapido solo para timeout o fallo transitorio de red

Observabilidad actual:

- al arrancar, el API loguea snapshot de runtime de alertas con flags efectivos y token saneado
- cada tick del scheduler deja:
  - `scheduler_tick_started`
  - `snapshots_persisted_count`
  - `new_signals_persisted_count`
  - `alerts_candidates_count`
  - `alert_deliveries_created_count`
  - `alert_deliveries_sent_count`
  - `alert_deliveries_failed_count`
  - `alert_skip_reasons`
- cada descarte en dispatch queda trazado con razones tipo:
  - `skipped_plan`
  - `skipped_no_chat_id`
  - `skipped_channel_disabled`
  - `skipped_threshold`
  - `skipped_duplicate`

## 7. Detectores de senales

Todos los detectores exponen `detect(data) -> signal | None`.

### 7.1 Volume Spike

Disparo:

- `volume_24h / avg_volume_24h >= 1.8`
- `abs(change_24h) >= 1.5`

Direccion:

- bullish si el cambio de precio es positivo
- bearish si el cambio de precio es negativo

Componentes de score:

- ratio de volumen
- cambio absoluto de precio
- momentum score

### 7.2 Range Breakout

Disparo:

- el precio rompe el maximo o minimo del rango de 20 dias al menos en `0.4%`

Componentes de score:

- fuerza del breakout
- ratio de volumen
- cambio absoluto de precio

### 7.3 Funding Extreme

Disparo:

- `abs(funding_rate) >= 0.02`
- `abs(funding_zscore) >= 2.0`

Interpretacion:

- contrarian
- funding positivo implica senal bearish
- funding negativo implica senal bullish

### 7.4 OI Divergence

Setup bullish:

- `price_change <= -1.0`
- `oi_change >= 6.0`

Setup bearish:

- `price_change >= 1.0`
- `oi_change <= -5.0`

### 7.5 Liquidation Cluster

Disparo:

- ratio de liquidaciones totales vs media `>= 2.5x`
- dominancia del lado principal `>= 0.68`

Interpretacion:

- dominancia de liquidaciones de longs -> bullish tactical reversal
- dominancia de liquidaciones de shorts -> bearish tactical reversal

### 7.6 Modelo de scoring

Utilidades de scoring:

- la normalizacion de componentes se clamp a `0.0 - 1.0`
- el score final se mapea a `1.0 - 10.0`
- la confianza se deriva de score y numero de evidencias

Matiz importante:

- los timeframes `1H`, `4H` y `8H` de las senales son etiquetas definidas por cada detector
- los snapshots normalizados que consumen los detectores son hoy agregados de tipo diario (`timeframe = "1D"`)
- por tanto, el motor actual sigue siendo un MVP heuristico y no un sistema multi-timeframe riguroso

### 7.7 Capa PRO de clasificacion operativa

La clasificacion operativa se construye en `apps/api/services/pro_signal_view.py`.

Estados usados:

- `EXECUTABLE`
- `WATCHLIST`
- `WAIT_CONFIRMATION`
- `DISCARD`

Reglas resumidas:

- `EXECUTABLE` exige score alto, confianza alta, confirmaciones suficientes, niveles indicativos disponibles y ausencia de contaminacion mock critica
- `WATCHLIST` indica interes claro, pero sin trigger suficientemente limpio
- `WAIT_CONFIRMATION` indica tesis valida con confirmacion incompleta
- `DISCARD` indica lectura demasiado debil o degradada

Regla conservadora critica:

- una señal con `mock_contamination` nunca escala a `EXECUTABLE`

## 8. Modelo de datos

Tablas actuales:

- `users`
- `assets`
- `market_snapshots`
- `signals`
- `setups`
- `subscriptions`
- `alert_subscriptions`
- `alert_deliveries`

Uso real hoy:

- `users`: usada activamente
- `assets`: usada activamente y sembrada al arrancar
- `market_snapshots`: usada activamente
- `subscriptions`: usada activamente
- `signals`: usada activamente por runtime de alertas
- `setups`: usada activamente para historico de setups PRO y lifecycle
- `alert_subscriptions`: usada activamente
- `alert_deliveries`: usada activamente

Relaciones relevantes:

- un asset -> muchos market snapshots
- un asset -> muchas signals
- un asset -> muchos setups
- un user -> muchas subscriptions
- un user -> muchas alert_subscriptions
- un user -> muchas alert_deliveries

Campos importantes de `signals`:

- `asset_symbol`
- `signal_key`
- `timeframe`
- `direction`
- `score`
- `confidence`
- `thesis`
- `evidence_json`
- `source_snapshot_time`
- `signal_hash`
- `is_active`
- `created_at`

Matiz importante de compatibilidad:

- `signals` conserva algunos campos legacy para no romper schema anterior
- `init_db.py` intenta parchear tablas ya existentes sin requerir Alembic
- `setups` se crea via `Base.metadata.create_all()`; aun no existe migracion formal

## 9. Detalles frontend

### 9.1 Modelo de render

El frontend usa Next App Router con mezcla de:

- server components para paginas como `/dashboard`
- client components para auth, pricing, tracking y configuracion de alertas

### 9.2 Modelo de sesion

Cookie de sesion:

- nombre: `ci_session`
- tipo: HTTP-only
- same-site: `lax`
- duracion: 14 dias

Acceso server-side:

- `apps/web/lib/server-session.ts` lee la cookie
- `apps/web/lib/api.ts` la usa para llamar rutas autenticadas del backend

### 9.3 Rutas proxy de Next

Existen route handlers para:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/billing/checkout`
- `POST /api/events`

Pantalla de dashboard hoy:

- `Setups PRO` como bloque principal
- `Historico de Setups` debajo, consumiendo `/signals/setups/history`
- `Señales base` como bloque tecnico secundario
- configuracion de alertas y Telegram en la misma pagina
- `GET /api/alerts/me`
- `GET /api/alerts/telegram/connect-instructions`
- `POST /api/alerts/telegram/connect`
- `POST /api/alerts/telegram/test`
- `POST /api/alerts/preferences`

Su objetivo es:

- evitar exponer la gestion directa del token al cliente
- setear o borrar cookies desde la capa Next
- proxyear tracking, checkout y alertas hacia FastAPI

### 9.4 Estrategia de fallback

`apps/web/lib/api.ts` contiene fallbacks hardcodeados de:

- assets
- signals
- signal feed
- market snapshots
- alert settings

Esto implica:

- la UI puede seguir renderizando aunque el backend falle
- la UI puede mostrar mock data sin conectividad API
- cualquier GPT que evolucione el sistema debe distinguir entre "la UI renderiza" y "el backend funciona de verdad"

### 9.5 Dashboard y gating

Comportamiento:

- el plan `free` solo ve las 2 primeras senales
- el numero de senales bloqueadas se muestra en un banner de upgrade
- las senales bloqueadas se renderizan como placeholders visuales
- las senales visibles en `free` salen en modo teaser:
  - titular
  - score
  - direccion
  - tesis corta
- las senales visibles en `pro` muestran:
  - estado operativo
  - resumen
  - confirmaciones
  - plan indicativo
  - warnings de calidad del dato
- `pro_plus` añade un campo reservado para seguimiento futuro
- el bloque `Alertas PRO`:
  - muestra upgrade prompt para `free`
  - permite a `pro` y `pro_plus` configurar Telegram y thresholds
  - refleja disponibilidad real del sistema segun flags y token
  - muestra diagnostico de entrega:
    - ultimo envio exitoso
    - ultimo fallo
    - ultimo `error_code`
    - thresholds efectivos
    - recuento de deliveries recientes
    - numero de señales elegibles recientes
  - incluye accion `Revalidar Telegram` contra `GET /alerts/debug/me`

## 10. Configuracion y variables de entorno

Variables core:

- `APP_ENV`
- `APP_BASE_URL`
- `NEXT_PUBLIC_API_URL`
- `INTERNAL_API_URL`
- `DATABASE_URL`
- `REDIS_URL`
- `AUTH_SECRET`

Variables de market data:

- `MARKET_DATA_SYMBOLS`
- `MARKET_DATA_SCHEDULE_MINUTES`
- `MARKET_DATA_USE_MOCK_FALLBACK`
- `ENABLE_MARKET_DATA_SCHEDULER`
- `MARKET_DATA_RUN_INITIAL_SYNC`
- `ENABLE_BINANCE_MARKET_DATA`
- `ENABLE_BYBIT_MARKET_DATA`
- `ENABLE_COINGLASS_MARKET_DATA`
- `COINGLASS_API_KEY`

Flags de senales:

- `ENABLE_VOLUME_SPIKE_SIGNAL`
- `ENABLE_RANGE_BREAKOUT_SIGNAL`
- `ENABLE_FUNDING_EXTREME_SIGNAL`
- `ENABLE_OI_DIVERGENCE_SIGNAL`
- `ENABLE_LIQUIDATION_CLUSTER_SIGNAL`

Variables de alertas:

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

Variables de billing:

- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_PRO`
- `STRIPE_PRICE_PRO_PLUS`
- `ENABLE_STRIPE_MOCK_CHECKOUT`

Matices importantes:

- `SIGNAL_ENGINE_USE_MOCK_DATA` existe en config y en `.env.example`, pero el runtime actual no la usa realmente
- `REDIS_URL` existe, pero no hay servicio Redis en `docker-compose.yml` ni funcionalidad activa que dependa hoy de Redis
- `ENABLE_EMAIL_ALERTS` puede activarse, pero el canal email seguira siendo stub si no se implementa un proveedor real
- combinaciones invalidas de flags de alertas se loguean al arrancar, por ejemplo:
  - Telegram habilitado sin token
  - alert processing on scheduler sin scheduler de market data
  - `ALERT_MAX_PER_RUN <= 0`

## 11. Desarrollo local y contenedores

### 11.1 Desarrollo local

Comando raiz:

```bash
npm run dev
```

Que hace:

1. copia `.env.example` a `.env` si falta
2. instala dependencias Node si faltan
3. crea el virtualenv Python en `apps/api/.venv`
4. instala requirements Python
5. arranca FastAPI en `:8000`
6. arranca Next en `:3000`

Matiz importante:

- el script local no levanta Postgres
- aun asi, el backend puede arrancar en modo degradado porque los errores de init DB se capturan y existe fallback mock para datos de mercado
- para probar persistencia real de senales y alertas, conviene usar Postgres real o `docker compose`

### 11.2 Docker

Comando raiz:

```bash
docker compose up --build
```

Servicios:

- `web`
- `api`
- `postgres`

Matices del entorno container:

- el contenedor API ejecuta `python -m db.init_db` antes de levantar `uvicorn`
- `web` espera al healthcheck de `api`
- no existe contenedor Redis

## 12. Estado de testing

Existe una base minima de tests en `tests/` con `pytest`.

Cobertura actual:

- deduplicacion de hash de senales
- comportamiento de thresholds
- gating por plan
- no duplicacion de entrega por usuario/canal
- formatter de Telegram
- clasificacion `ProSignalView`
- bloqueo de `EXECUTABLE` bajo contaminacion mock
- presencia de estado, plan y warnings en el formatter PRO

Lo que sigue faltando:

- tests de auth
- tests de billing
- tests de scheduler end-to-end
- tests de UI
- tests de integracion real con Telegram y Stripe

## 13. Limitaciones tecnicas y deuda de diseno

Estos puntos son importantes para cualquier GPT o ingeniero que evolucione el proyecto:

1. No hay Alembic; el schema se mantiene con `create_all()` y parches manuales.
2. El sistema de suscripciones sirve para validar el MVP, pero carece de reconciliacion por webhook.
3. Las senales basadas en liquidaciones dependen casi siempre de datos mock/default hasta integrar un proveedor real.
4. Los timeframes de los snapshots y los timeframes de las senales no estan verdaderamente alineados.
5. El signal engine se importa via `sys.path` en lugar de empaquetarse de forma formal.
6. El tracking de eventos solo loguea del lado servidor y no persiste nada.
7. La persistencia de senales existe, pero el frontend principal aun no consume un historico materializado; sigue usando feed on-demand enriquecido.
8. El canal email de alertas es solo un stub.
9. No hay retries, colas ni backoff para alertas.
10. Los fallbacks del frontend pueden ocultar fallos reales del backend durante QA manual.
11. Los niveles del `action_plan` son indicativos; no deben interpretarse como execution algorítmica precisa.

## 14. Reglas de evolucion segura

Si otro GPT o ingeniero modifica este repositorio, conviene preservar estas restricciones salvo refactor deliberado:

- mantener frontend y backend desacoplados por contrato HTTP
- mantener la logica de detectores separada del codigo de rutas FastAPI
- preservar la semantica de la cookie `ci_session` salvo rediseño completo de auth
- tratar el modo Stripe mock como parte del workflow de desarrollo
- no asumir Redis
- no eliminar los fallbacks mock sin reemplazar la ergonomia de desarrollo local
- mantener el pipeline de alertas gobernado por flags
- si se van a tocar schemas con frecuencia, introducir primero una estrategia de migraciones

Siguientes pasos tecnicos recomendados:

1. Introducir Alembic.
2. Anadir webhooks Stripe para reconciliacion real.
3. Sustituir el fallback de liquidaciones por integracion real.
4. Implementar proveedor real de email.
5. Anadir retries y/o cola para alertas.
6. Exponer historico de senales persistidas como producto visible.
7. Convertir `packages/signal-engine` en un paquete Python instalable o en un modulo gestionado de forma formal.

## 15. Modelo mental correcto para otro GPT

Si otro GPT va a trabajar sobre este proyecto, el modelo mental correcto es este:

- esto no es solo un repo de algoritmos de senales; es una base de SaaS comercial
- conversion, billing, gating y alertas son preocupaciones de primer nivel
- el backend esta hecho para ser tolerante a fallos y rapido de iterar en local
- la `Señal PRO` es hoy una capa central de producto, no solo cosmética de UI
- el producto hoy combina dos modos:
  - pull: dashboard consulta feed y snapshots
  - push: scheduler detecta senales nuevas y las distribuye a `pro`
- varias capas aun estan en modo MVP: migraciones, email real, liquidaciones reales, webhook de Stripe y colas de alertas

En resumen: hay una base comercial y tecnica real para evolucionar el producto. Ya existe persistencia de senales y pipeline de alertas, pero varias piezas siguen deliberadamente simplificadas para priorizar velocidad de iteracion y validacion del modelo de negocio.
