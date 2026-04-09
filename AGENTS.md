# AGENTS.md

## Repo Shape
- `src/main/java` + `src/main/resources/application.yml`: Spring Boot 2.7 / Java 8 API. `BiliInsightApplication` enables scheduling.
- `python_service/app`: FastAPI analysis service. `python_service/scripts` are one-off migration/eval utilities, not request entrypoints.
- `bili-insight-frontend/src`: Vue 3 + Vite app.
- `bilibili-api/`: checked-in upstream/fork library package plus its own tests/docs. The live Python service imports the installed `bilibili-api-python` dependency from `python_service/requirements.txt`, not this sibling tree by default.
- `sql/bili_insight_db.sql`: schema and seed dump; use this as the DB source of truth before trusting prose docs.
- Searches will surface checked-in generated artifacts (`target/`, `__pycache__`, `.pyc`, `.DS_Store`). Do not treat them as source.

## Commands
- Backend: `mvn spring-boot:run`
- Backend build: `mvn clean package -DskipTests`
- Frontend setup: in `bili-insight-frontend`, run `npm install`
- Frontend dev: in `bili-insight-frontend`, run `npm run dev`
- Frontend verification: in `bili-insight-frontend`, run `npm run type-check` and `npm run build`
- Frontend lint: `npm run lint` runs `eslint . --fix` and will mutate files.
- Python service setup: in `python_service`, run `pip install -r requirements.txt`
- Python service run: in `python_service`, run `venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --log-level info`

## Runtime Wiring
- Real request flow is `frontend /insight/* -> Spring controllers -> PythonApiClient -> FastAPI -> MySQL`, then Java reads the written rows back for result endpoints. Do not move crawling/NLP into Java or JWT/auth into Python.
- Frontend API calls assume Vite proxying: axios base URL is `'/'`, and `vite.config.ts` proxies `/insight` to `http://localhost:8080`. Avoid hardcoding absolute backend URLs in frontend code.
- Frontend auth is client-side JWT storage: `src/utils/request.ts` injects `Authorization: Bearer ...`, and `src/router/index.ts` locally decodes token expiry. Client public routes are only `/login` and `/register`.
- The live analysis detail/review page is `bili-insight-frontend/src/views/AnalysisDetailView.vue`. `VideoReviewView.vue` exists but is not routed.

## Service Gotchas
- Starting the Spring app is not side-effect free. `StartupDataInitializer` will try to launch `python_service` with `python.service.start-command` if health checks fail, then immediately trigger popular-video initialization.
- Scheduling is always on. `ProjectMonitorScheduler` scans projects hourly, and `ProjectMonitorService` also has a 6-hour schedule. Be careful when changing task submission, project logic, or startup behavior.
- Python API auth is separate from JWT. FastAPI middleware checks `X-API-Key` for most routes; only `/`, `/health`, `/docs`, and `/openapi.json` are public. Java sends the same key from `python.service.api-key`.
- The checked-in workspace currently has `python_service/venv`, but `application.yml` still defaults `python.service.start-command` to `.venv/bin/uvicorn ...`. If Spring auto-start matters, align those before relying on it.
- Python settings load from `python_service/.env` specifically via `app/config.py`, not from the repo root `.env`.
- There is no checked-in `python_service/.env.example`. If you change DB or service connection settings, keep Java env overrides in `application.yml` and Python `python_service/.env` aligned.
- `src/main/resources/application.yml` currently contains development defaults for DB password, JWT secret, and Python API key. Treat them as local defaults only; do not add more hardcoded secrets.
- Comment crawling is not a single path. `python_service/app/services/bilibili_service.py` can use bilibili-api first, then Playwright / `curl_cffi` fallbacks when Bilibili risk control or network issues hit.

## Verification
- There is no app test suite checked in for the Spring app, frontend, or `python_service`; the only substantial tests in this repo are under `bilibili-api/tests` for the bundled library.
- For normal app changes, the practical focused checks are:
  - frontend: `npm run type-check` and/or `npm run build`
  - backend: `mvn clean package -DskipTests`
  - python service: start `uvicorn` and hit `/health` or exercise the touched endpoint

## Language Requirement
- The agent must always respond in Chinese (Simplified Chinese).
- Do not use English unless explicitly required by the user.
