# Crypto Intelligence SaaS

Base monorepo para un SaaS de inteligencia crypto con frontend en Next.js, backend en FastAPI, market data normalizado, signal engine MVP y alertas inmediatas para usuarios `pro`.

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
- feed con gating por plan: `http://localhost:8000/signals/feed`
- auth: `http://localhost:8000/auth/login`, `http://localhost:8000/auth/register`, `http://localhost:8000/auth/me`
- billing: `http://localhost:8000/billing/checkout`, `http://localhost:8000/billing/confirm`
- alertas: `http://localhost:8000/alerts/me`, `http://localhost:8000/alerts/telegram/connect`, `http://localhost:8000/alerts/preferences`

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
4. si las alertas estan habilitadas, el backend procesa alertas inmediatas
5. usuarios `pro` y `pro_plus` con Telegram configurado reciben push
6. usuarios `free` siguen viendo un feed limitado en el dashboard
7. el dashboard sigue pudiendo consultar feed on-demand aunque las alertas esten desactivadas

## Alertas inmediatas

Canal actual:

- Telegram como canal prioritario

Canal preparado:

- email, detras de flag y aun sin proveedor real

Reglas base:

- solo `pro` y `pro_plus` reciben alertas push
- thresholds globales por defecto:
  - `ALERT_MIN_SCORE=7.0`
  - `ALERT_MIN_CONFIDENCE=0.6`
- deduplicacion por hash con ventana temporal de `5` minutos
- si falta `TELEGRAM_BOT_TOKEN`, el sistema registra fallo y sigue funcionando

UI actual:

- el dashboard incluye una card de `Alertas PRO`
- `free` ve upgrade prompt
- `pro` puede guardar `telegram_chat_id`, activar/desactivar canales y definir thresholds

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
- `ALERT_MIN_SCORE`
- `ALERT_MIN_CONFIDENCE`
- `ALERT_DEDUPE_WINDOW_MINUTES`
- `ALERT_MAX_PER_RUN`
- `ALERTS_PROCESS_ON_SCHEDULER`

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
- `subscriptions`
- `alert_subscriptions`
- `alert_deliveries`

Capacidades ya implementadas:

- ingesta desde Binance y Bybit con fallback mock
- feed de senales con gating por plan
- persistencia real de senales para historico tecnico y alertas
- auth basica con cookie `ci_session`
- checkout Stripe con modo mock para desarrollo
- dashboard con upgrade flow y configuracion de alertas
- tests minimos del sistema de alertas

## Billing local

- si usas credenciales y `price_id` reales de Stripe, desactiva `ENABLE_STRIPE_MOCK_CHECKOUT`
- en desarrollo, `ENABLE_STRIPE_MOCK_CHECKOUT=true` permite probar registro, upgrade y acceso sin cobro real

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
- sustituir liquidaciones mock por proveedor real
