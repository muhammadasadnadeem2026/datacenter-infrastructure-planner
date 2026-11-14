# HallPlan — Data Center Infrastructure Planner

Full-stack power, cooling, electrical-distribution and capacity-planning calculator for data
centers, from a single server closet to multi-MW AI/GPU halls.

- **One authoritative calculation engine** (Python, `backend/app/calculations/`). The React UI,
  PDF reports, XLSX/CSV exports and tests all consume the same engine result — no formula is
  implemented twice.
- **Every number is traceable**: value, formula, substituted calculation, units, assumption and
  reference, with a *Show calculation* toggle on every result.
- **Versioned engine** (`CALC_ENGINE_VERSION`), stored with every saved study.

> Results are planning and preliminary engineering estimates. Final electrical, mechanical,
> protection, structural, code-compliance, and equipment-selection decisions must be verified
> against the applicable project requirements, manufacturer data, and local codes by qualified
> engineering professionals.

## Features

| Area | What it does |
|---|---|
| Main calculator (`/calculator`) | 15 collapsible input sections, Quick / Standard / Engineering modes, 7 deployment presets, live debounced results |
| IT load | Rack-average or device-list mode (add / duplicate / delete rows, CSV import & export) |
| Electrical | Receptacle library, 1-φ / 3-φ capacity, continuous-load derating, circuits per rack, loading gauge |
| PDU, UPS, battery | Growth margin, A/B feeds, N / N+1 / 2N, module sizing, idealized battery runtime (needs battery data) |
| Cooling & density | BTU/hr, tons, per-rack heat, configurable density classes, area density |
| Transformer, generator, BESS | Loading with redundancy, FLA, approximate terminal fault current, generator load basis, BESS power vs energy sizing with separate AC/DC |
| Capacity balance | IT / UPS / transformer / utility / generator / BESS / cooling — PF-aware, identifies the bottleneck |
| Visuals | Single-line power flow, energy Sankey (honest "Facility Overhead" when no split entered), capacity chart |
| Projects | Create, rename, save, clone, delete, recalculate, JSON import/export (PostgreSQL) |
| Reports | PDF report, XLSX (7 worksheets), CSV per sheet |
| Tools | kW↔kVA, circuits, unit converter, rack count, cooling, UPS, PDU, rack density, transformer, generator, BESS, AI rack |
| Docs | `/methodology` (every formula), `/references` (structured, verification status shown) |

## Design

- Light and dark themes with a header toggle; every Tailwind colour is a CSS variable in `frontend/src/index.css`.
- Left sidebar navigation that becomes a drawer below 1024 px.

## Optional equipment references

Extra equipment reference data can be placed in `backend/app/constants/equipment_references.local.json` (git-ignored). The engine never needs it: it uses only the entered rack power, liquid-capture ratio and coolant flow.

## Repository layout

```
backend/
  app/
    api/            FastAPI routers (no formulas)
    calculations/   pure calculation modules + warning engine + orchestrator
    constants/      thresholds, cooling classes, receptacles, voltages, presets, references.json
    models/         SQLAlchemy models
    schemas/        Pydantic input / output models
    services/       persistence, PDF report, XLSX/CSV export
    database/       engine & session
    validation/     cross-field validators
  alembic/          migrations
  tests/            pytest unit + integration tests
frontend/
  src/
    components/     calculators, forms, results, charts, layouts
    pages/  hooks/  stores/  services/  types/  constants/  utils/  test/
docs/               calculation, API and deployment documentation
examples/           example project files (importable JSON)
```

## Local installation (without Docker)

Prerequisites: Python 3.12+, Node 20+ (22 recommended).

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows;  macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head            # creates the SQLite database (backend/hallplan.db) by default
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs (Swagger) and http://localhost:8000/redoc.

To use PostgreSQL locally, set `DATABASE_URL`, e.g.
`postgresql+psycopg://hallplan:secret@localhost:5432/hallplan`, then run `alembic upgrade head`.

### Frontend

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173 (proxies /api to :8000)
```

## Docker installation

```bash
cp .env.example .env            # set POSTGRES_PASSWORD
docker compose up --build
```

- App: http://localhost:8080 (nginx serves the SPA and proxies `/api` to the backend)
- API: http://localhost:8000/docs
- Migrations run automatically when the backend container starts.

## Commands

| Task | Backend (`backend/`) | Frontend (`frontend/`) |
|---|---|---|
| Dev server | `uvicorn app.main:app --reload` | `npm run dev` |
| Tests | `pytest` | `npm test` |
| Coverage | `pytest --cov=app` | — |
| Lint | `ruff check .` | `npm run lint` |
| Format | `ruff format .` | `npm run format` |
| Type check | — | `npm run typecheck` |
| Build | `docker build ./backend` | `npm run build` |

### Database migrations

```bash
cd backend
alembic upgrade head                           # apply
alembic downgrade -1                           # roll back one
alembic revision --autogenerate -m "message"   # create after changing models
```

## Environment variables

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | backend | SQLite file `backend/hallplan.db` | SQLAlchemy URL (`postgresql+psycopg://…` in production) |
| `CORS_ORIGINS` | backend | `http://localhost:5173,…` | Comma-separated allowed browser origins |
| `RATE_LIMIT_PER_MINUTE` | backend | `240` | Per-client API request limit (0 disables) |
| `ENVIRONMENT` | backend | `development` | Informational |
| `WEB_CONCURRENCY` | backend container | `2` | Uvicorn worker count |
| `VITE_API_BASE_URL` | frontend build | empty (same origin) | Absolute API URL if the API is on another host |
| `POSTGRES_DB/USER/PASSWORD` | compose | — | Database credentials (password required) |

## Production deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). In short: build both images, run PostgreSQL as a
managed service, set `DATABASE_URL` and `CORS_ORIGINS` from your secret store, terminate TLS at
a reverse proxy, and enforce rate limits at the gateway as well when running several replicas.

## Documentation

- [docs/CALCULATIONS.md](docs/CALCULATIONS.md): engine architecture, every formula, validation, warnings, versioning
- [docs/API.md](docs/API.md): endpoint reference with examples
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md): production deployment
- `/methodology` and `/references` pages in the app

## Acceptance example

`examples/acceptance_example.json` (importable in *Saved Projects → Import JSON*):
10 racks × 6 kW, PF 0.95, PUE 1.5, $0.13/kWh →
60 kW IT · 63.16 kVA · 204,729 BTU/hr · 17.06 tons · 90 kW facility · 788,400 kWh/yr · $102,492/yr.
