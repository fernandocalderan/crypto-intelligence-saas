# Architecture

## Monorepo

```text
apps/
  web/            Next.js UI
  api/            FastAPI backend
packages/
  core/           domain contracts
  signal-engine/  scoring catalog
infra/
  docker/         Dockerfiles
  nginx/          VPS reverse proxy base
  scripts/        local/dev automation
docs/             product and technical docs
```

## Flujo

1. `apps/web` renderiza landing, login, pricing y dashboard.
2. `apps/web/app/dashboard` consume `/assets` y `/signals` del backend.
3. `apps/api` expone rutas y centraliza acceso a servicios de mercado y motor de señales.
4. `apps/api/db` prepara modelos SQLAlchemy para Postgres.
5. `packages/signal-engine` deja lista la futura extracción del scoring.

## Principios

- frontend y backend desacoplados por contrato HTTP sencillo
- motor de señales aislable del API para evitar acoplamiento temprano
- Postgres preparado, pero endpoints iniciales desacoplados de la base para iterar rápido
- infraestructura mínima para local y VPS sin sobredimensionar el MVP

