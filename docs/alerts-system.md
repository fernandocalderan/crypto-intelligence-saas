# Alerts System

## Objetivo

El sistema de alertas convierte `crypto-intelligence-saas` de un modelo solo pull a un modelo push + pull:

- el dashboard sigue existiendo como superficie de consulta
- el backend persiste señales nuevas
- el scheduler procesa esas señales y dispara alertas inmediatas
- Telegram es el canal prioritario
- email queda preparado como extensión, pero puede permanecer desactivado por flag

## Componentes

### Persistencia de señales

Archivo principal:

- `apps/api/services/signal_persistence.py`

Responsabilidades:

- construir `signal_hash` con bucket temporal
- transformar la salida del signal engine en `SignalRecord`
- guardar solo señales nuevas
- devolver la lista de señales recién persistidas

La deduplicación usa:

- `asset_symbol`
- `signal_key`
- `timeframe`
- `direction`
- bucket temporal de `ALERT_DEDUPE_WINDOW_MINUTES`

## Tablas

### signals

La tabla `signals` pasa a usarse de verdad en runtime.

Campos relevantes:

- `asset_symbol`
- `signal_key`
- `signal_type`
- `timeframe`
- `direction`
- `score`
- `confidence`
- `thesis`
- `evidence_json`
- `source`
- `source_snapshot_time`
- `signal_hash`
- `is_active`
- `created_at`

### alert_subscriptions

Define preferencias de alertas por usuario y canal.

Campos relevantes:

- `user_id`
- `channel`
- `is_active`
- `telegram_chat_id`
- `email`
- `min_score`
- `min_confidence`

Regla simplificada implementada:

- una suscripción por usuario y canal

### alert_deliveries

Registra cada intento de envío y evita duplicados.

Campos relevantes:

- `signal_id`
- `user_id`
- `channel`
- `delivery_status`
- `provider_message_id`
- `error_message`
- `sent_at`

Constraint principal:

- unique por `signal_id`, `user_id`, `channel`

## Flujo end-to-end

1. `APScheduler` ejecuta la ingesta de market data.
2. Se generan snapshots normalizados.
3. El backend calcula señales sobre esos snapshots.
4. Las señales nuevas se persisten en `signals`.
5. Si `ALERTS_PROCESS_ON_SCHEDULER=true`, se ejecuta el pipeline de alertas.
6. El motor carga usuarios `pro` o `pro_plus` con suscripciones activas.
7. Filtra señales por:
   - `score >= ALERT_MIN_SCORE`
   - `confidence >= ALERT_MIN_CONFIDENCE`
8. Crea `alert_deliveries` en estado `pending`.
9. Intenta enviar por canal.
10. Marca la entrega como `sent` o `failed`.

## Flags de entorno

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

## Telegram

Configuración requerida:

1. crear un bot y obtener `TELEGRAM_BOT_TOKEN`
2. identificar el `telegram_chat_id` del destino
3. guardar ese chat id desde el dashboard o vía API

Endpoints:

- `GET /alerts/me`
- `GET /alerts/telegram/connect-instructions`
- `POST /alerts/telegram/connect`
- `POST /alerts/telegram/test`
- `POST /alerts/preferences`

Flujo implementado en dashboard:

1. el usuario `pro` abre la card `Alertas PRO`
2. despliega `Conectar Telegram`
3. sigue las instrucciones del bot
4. pega `telegram_chat_id` y vincula la cuenta
5. puede enviar `Enviar prueba` aunque el canal todavía no esté activado
6. después guarda `Activar alertas por Telegram`

## Umbrales

El sistema de alertas usa `min_confidence` en formato 0-1 por defecto.

Ejemplo:

- `0.6` se interpreta como `60%`

Esto permite mantener:

- dashboard mostrando confidence en porcentaje
- preferencias de alertas en formato compacto

## Tolerancia a fallos

- si `TELEGRAM_BOT_TOKEN` falta, el envío falla sin romper scheduler ni API
- si un usuario no tiene chat id configurado, no se intenta el envío
- si una entrega falla, se registra en `alert_deliveries`
- si la misma señal ya fue enviada al mismo usuario por el mismo canal, se omite
- si el usuario no inició el bot, la API devuelve un mensaje claro para pulsar `Start`
- si el `chat_id` es inválido, la API devuelve error controlado para UI

## Limitaciones actuales

- el dashboard sigue consumiendo señales on-demand; la persistencia se usa para alertas e histórico técnico
- email no tiene proveedor real configurado todavía
- no hay sistema de reintentos
- las liquidaciones pueden seguir viniendo de fallback mock
- no existe Alembic; el schema sigue apoyándose en `create_all()` más parches de compatibilidad para la tabla `signals`

## Prueba manual recomendada

1. definir `TELEGRAM_BOT_TOKEN` y opcionalmente `TELEGRAM_BOT_USERNAME`
2. arrancar Postgres y API
3. registrar un usuario
4. activar el usuario en plan `pro`
5. abrir Telegram, buscar el bot y pulsar `Start`
6. ir a dashboard y vincular `telegram_chat_id`
7. pulsar `Enviar prueba`
8. verificar recepción del mensaje o error controlado
9. activar Telegram en preferencias y guardar

Troubleshooting:

- `Telegram no disponible temporalmente`: falta token o el canal está desactivado por flags
- `Abre Telegram, busca el bot y pulsa Start`: el usuario no inició el bot o el chat no es accesible
- `El chat ID de Telegram no es válido`: el valor pegado no es numérico o el backend lo rechaza
- `El plan free no puede...`: el usuario necesita `pro` o `pro_plus`
