# Deployment

## Local

- comando único recomendado: `npm run dev`
- alternativa contenedorizada: `docker compose up --build`

## VPS

Stack previsto:

- `web` Next.js
- `api` FastAPI
- `postgres` gestionado en el mismo VPS o servicio externo
- `nginx` delante con reverse proxy y TLS

## Ruta sugerida de despliegue

1. desplegar contenedores `web` y `api`
2. montar `postgres` persistente
3. apuntar Nginx a `web:3000` y `api:8000`
4. exponer `/api/` a FastAPI y `/` a Next.js
5. añadir HTTPS, backups y monitorización básica

## Notas

- el compose actual prioriza simplicidad de MVP
- la configuración Nginx en `infra/nginx/default.conf` sirve como base para el VPS
- conviene introducir migraciones antes de pasar a producción real
