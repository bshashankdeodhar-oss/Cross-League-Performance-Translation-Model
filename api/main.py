"""
FastAPI layer around the Cross-League Performance Translation Model.

Design principle: this file NEVER re-implements ML logic. It only
imports and calls src/predict.py, src/pipeline.py etc. The model
code stays exactly as-is; this is pure plumbing (validation, auth,
routing, error translation).

Run:
  uvicorn api.main:app --reload --port 8000
Docs:
  http://localhost:8000/docs
"""

import sys
import subprocess
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import load_config, resolve_path
from src.predict import predict_player

from api.schemas import PredictRequest, PredictResponse, Token, PlayerSummary
from api.auth import authenticate_user, create_access_token, get_current_user, require_admin
from db.session import get_db
from db.models import Player

app = FastAPI(
    title="Cross-League Performance Translation API",
    description="Predicts how a football player's stats translate across leagues.",
    version="1.0.0",
)

# Loosen for local dev; tighten allow_origins before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_cfg = load_config()


@app.get("/health")
def health():
    return {"status": "ok"}


# ── Auth ──────────────────────────────────────────────────────────────────

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    role = authenticate_user(form_data.username, form_data.password)
    if not role:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token(form_data.username, role)
    return Token(access_token=token)


# ── Reference data (backed by Postgres) ──────────────────────────────────

@app.get("/leagues")
def list_leagues(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        db_leagues = db.query(Player.league).distinct().all()
        leagues = [r[0] for r in db_leagues]
        if leagues:
            return {lg: _cfg["league_strength"].get(lg, 1.0) for lg in leagues}
    except Exception:
        pass
    return _cfg["league_strength"]


@app.get("/players", response_model=list[PlayerSummary])
def list_players(
    league: str | None = None,
    search: str | None = None,
    limit: int = 50,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Player)
    if league:
        query = query.filter(Player.league == league)
    if search:
        query = query.filter(Player.player.ilike(f"%{search}%"))

    players = query.limit(limit).all()
    return [
        PlayerSummary(
            player=p.player,
            team=p.team,
            league=p.league,
            position=p.position,
            age=p.age
        )
        for p in players
    ]


# ── Prediction ────────────────────────────────────────────────────────────

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest, user: dict = Depends(get_current_user)):
    try:
        result = predict_player(req.player, req.source_league, req.target_league, _cfg)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return result


# ── Admin: trigger retrain ────────────────────────────────────────────────

@app.post("/admin/retrain")
def retrain(user: dict = Depends(require_admin)):
    """Kicks off the training phase of the pipeline. Runs synchronously —
    for a real deployment, push this to a background task queue (Celery/RQ)
    instead of blocking the request."""
    result = subprocess.run(
        [sys.executable, "-m", "src.pipeline", "--phase", "train"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=1800,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Retrain failed: {result.stderr[-2000:]}")
    return {"status": "retrain complete", "log_tail": result.stdout[-1000:]}
