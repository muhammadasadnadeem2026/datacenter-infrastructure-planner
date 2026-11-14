# Production deployment

## Topology

```
Browser ──HTTPS──► reverse proxy / load balancer (TLS, rate limiting)
                      │
                      ├── frontend (nginx, static SPA, proxies /api)
                      └── backend (FastAPI / uvicorn, N replicas)
                                │
                                └── PostgreSQL (managed, backups enabled)
```

## Steps

1. **Database.** Provision PostgreSQL 14+ (16 recommended). Create a dedicated database and
   user with least privilege. Enable automated backups.
2. **Secrets.** Store `DATABASE_URL` (e.g.
   `postgresql+psycopg://hallplan:<password>@db-host:5432/hallplan`) in your secret manager and
   inject it as an environment variable. Never bake it into images.
3. **Build images.**
   ```bash
   docker build -t registry.example.com/hallplan-backend:1.0.0 ./backend
   docker build -t registry.example.com/hallplan-frontend:1.0.0 ./frontend
   ```
   If the API is served from a different origin than the SPA, pass
   `--build-arg VITE_API_BASE_URL=https://api.example.com` to the frontend build and set
   `CORS_ORIGINS=https://app.example.com` on the backend. With the bundled nginx proxy the SPA
   and API share one origin and CORS is not needed.
4. **Migrations.** The backend container runs `alembic upgrade head` on start. With several
   replicas, run migrations once as a release job instead
   (`docker run --rm -e DATABASE_URL=… hallplan-backend alembic upgrade head`) and start the
   replicas with `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
5. **TLS and headers.** Terminate TLS at the proxy. nginx already adds `X-Content-Type-Options`,
   `X-Frame-Options` and `Referrer-Policy`. Add HSTS at the edge.
6. **Rate limiting.** The built-in limiter is per process. Behind multiple replicas, also
   enforce limits at the proxy / API gateway.
7. **Health checks.** Use `GET /api/health` for liveness and readiness.
8. **Scaling.** The engine is CPU-bound and stateless; scale backend replicas horizontally.
   Tune `WEB_CONCURRENCY` for workers per container.

## Upgrading the engine

Bump `CALC_ENGINE_VERSION` for any change that alters results. Existing saved projects keep
their stored results and version; users choose when to *Recalculate*.

## Security checklist

- [x] All inputs validated server-side (Pydantic, finite numbers, ranges, no extra fields)
- [x] No `eval` / dynamic code execution; formulas are compiled Python functions
- [x] Secrets only via environment variables
- [x] CORS restricted to configured origins
- [x] Rate limiting (app + gateway)
- [x] Non-root container user (backend)
