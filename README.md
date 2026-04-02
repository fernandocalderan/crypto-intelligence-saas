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
- activos mock: `http://localhost:8000/assets`
- señales mock: `http://localhost:8000/signals`

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

- modelo Postgres para `users`, `assets` y `signals`
- endpoints mock de `assets` y `signals`
- dashboard que consume datos reales del backend
- documentación para producto, arquitectura, señales, modelo de datos y despliegue

## Siguiente paso recomendado

Definir con precisión las 5 señales comerciales del MVP y fijar para cada una:

- inputs de mercado
- fórmula de scoring
- umbrales de activación
- frecuencia de cálculo
- explicación visible para el cliente

