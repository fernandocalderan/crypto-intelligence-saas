# Crypto Intelligence SaaS

Base monorepo para un SaaS de inteligencia crypto con frontend en Next.js, backend en FastAPI, documentación de producto/arquitectura y despliegue inicial con Docker.

## Stack

- `apps/web`: Next.js + Tailwind + App Router
- `apps/api`: FastAPI + SQLAlchemy + Postgres
- `packages/core`: tipos compartidos y contratos del dominio
- `packages/signal-engine`: catálogo y reglas base para señales del MVP
- `infra/docker`: Dockerfiles de frontend y backend
- `infra/nginx`: reverse proxy base para futuro despliegue en VPS
- `infra/scripts`: scripts de bootstrap y desarrollo local
- `docs`: documentación funcional y técnica

## Arranque rápido local

Primer comando recomendado:

```bash
npm run dev
```

Qué hace:

- crea `.env` a partir de `.env.example` si no existe
- instala dependencias Node en la raíz si faltan
- crea `apps/api/.venv` e instala dependencias Python si faltan
- arranca FastAPI en `http://localhost:8000`
- arranca Next.js en `http://localhost:3000`

Rutas útiles:

- landing: `http://localhost:3000/`
- login: `http://localhost:3000/login`
- dashboard: `http://localhost:3000/dashboard`
- pricing: `http://localhost:3000/pricing`
- health API: `http://localhost:8000/health`
- activos: `http://localhost:8000/assets`
- snapshots de mercado: `http://localhost:8000/market/latest`
- señales live: `http://localhost:8000/signals/live`
- feed con restricción por plan: `http://localhost:8000/signals/feed`
- auth: `http://localhost:8000/auth/login`, `http://localhost:8000/auth/register`, `http://localhost:8000/auth/me`
- billing: `http://localhost:8000/billing/checkout`, `http://localhost:8000/billing/confirm`

## Arranque con Docker

```bash
docker compose up --build
```

Servicios:

- `web`: Next.js en `3000`
- `api`: FastAPI en `8000`
- `postgres`: Postgres en `5432`

## Comandos útiles

```bash
npm run build:web
npm run lint:web
npm run install:api
```

## Modelo inicial

La base incluye:

- modelo Postgres para `users`, `assets`, `signals`, `market_snapshots` y `subscriptions`
- ingestión inicial de market data desde Binance y Bybit con fallback mock
- auth básica con registro/login y sesión persistida por cookie en el frontend
- endpoint `market/latest`, checkout Stripe y señales filtradas por plan
- dashboard con banner de upgrade, limitación Free y desbloqueo Pro/Pro+
- documentación para producto, arquitectura, señales, modelo de datos y despliegue

## Billing local

- si usas credenciales y `price_id` reales de Stripe, desactiva `ENABLE_STRIPE_MOCK_CHECKOUT`
- en desarrollo, `ENABLE_STRIPE_MOCK_CHECKOUT=true` permite probar registro, pago simulado y acceso sin cobro real

## Siguiente paso recomendado

Definir con precisión las 5 señales comerciales del MVP y fijar para cada una:

- inputs de mercado
- fórmula de scoring
- umbrales de activación
- frecuencia de cálculo
- explicación visible para el cliente
