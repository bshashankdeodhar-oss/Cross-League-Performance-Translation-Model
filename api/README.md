# CLPTM API Layer (FastAPI)

Wraps the existing Cross-League Performance Translation Model in a REST API.
The ML code in `src/` is untouched — this is a plumbing layer on top.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn api.main:app --reload --port 8000
```

Docs: http://localhost:8000/docs

## Auth

Two demo users (in-memory — swap for a real user table before deploying):

| username | password   | role   |
|----------|-----------|--------|
| viewer   | viewer123 | viewer |
| admin    | admin123  | admin  |

```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=viewer&password=viewer123" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

Use the returned `access_token` as `Authorization: Bearer <token>` on other routes.

## Endpoints

- `GET /health` — liveness check, no auth
- `POST /auth/login` — get JWT
- `GET /leagues` — league strength coefficients (auth required)
- `GET /players?league=&search=&limit=` — browse/search players (auth required)
- `POST /predict` — run a transfer prediction (auth required)
- `POST /admin/retrain` — trigger `pipeline.py --phase train` (admin role only)

## Example predict call

```bash
curl -X POST http://localhost:8000/predict \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"player": "Florian Wirtz", "source_league": "Bundesliga", "target_league": "Premier League"}'
```

## Next steps (roadmap)

1. Migrate `data/processed/feature_dataset.csv` into Postgres; point `/players`
   and `/predict` at the DB instead of reading CSV on every request.
2. Build a React dashboard: player search → prediction card → SHAP chart →
   what-if scenario slider (wraps `src/explainability/scenario_sim.py`).
3. Add pytest coverage for `api/` routes + a GitHub Actions CI workflow.
4. Move `/admin/retrain` off the request thread into a background job queue
   (Celery/RQ) since training can run long.
