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

from api.schemas import PredictRequest, PredictResponse, Token, PlayerSummary, TeamSummary
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
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    role = authenticate_user(form_data.username, form_data.password, db=db)
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


@app.get("/teams", response_model=list[TeamSummary])
def list_teams(
    league: str | None = None,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        from db.models import Team, League
        q = db.query(Team, League).join(League, Team.league_id == League.league_id)
        if league:
            q = q.filter(League.league_name == league)
        teams = q.all()
        if teams:
            return [
                TeamSummary(
                    team=t.Team.team_name,
                    league=t.League.league_name,
                    team_strength_ratio=t.Team.team_strength_ratio or 1.0,
                )
                for t in teams
            ]
    except Exception:
        pass

    # Fallback to feature_dataset.csv
    try:
        feat_path = resolve_path(_cfg, "processed_data", "feature_dataset.csv")
        if feat_path.exists():
            df = pd.read_csv(feat_path)
            if "team" in df.columns and "league" in df.columns:
                sub = df
                if league:
                    sub = df[df["league"].str.lower() == league.lower()]
                grouped = (
                    sub.groupby(["team", "league"])["team_strength_ratio"]
                    .mean()
                    .reset_index()
                )
                return [
                    TeamSummary(
                        team=r["team"],
                        league=r["league"],
                        team_strength_ratio=round(float(r["team_strength_ratio"]), 3)
                        if "team_strength_ratio" in r and not pd.isna(r["team_strength_ratio"])
                        else 1.0,
                    )
                    for _, r in grouped.iterrows()
                ]
    except Exception:
        pass

    return []


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
def predict(
    req: PredictRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = predict_player(
            req.player,
            req.source_league,
            req.target_league,
            target_team=req.target_team,
            cfg=_cfg,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Audit log prediction to TransferPrediction table
    try:
        from db.models import League, User, TransferPrediction
        player_obj = db.query(Player).filter(Player.player_name == req.player).first()
        src_lg = db.query(League).filter(League.league_name == req.source_league).first()
        tgt_lg = db.query(League).filter(League.league_name == req.target_league).first()
        user_obj = db.query(User).filter(User.username == user.get("username")).first()

        if player_obj and src_lg and tgt_lg:
            pred_record = TransferPrediction(
                player_id=player_obj.player_id,
                user_id=user_obj.user_id if user_obj else None,
                source_league_id=src_lg.league_id,
                target_league_id=tgt_lg.league_id,
                projected_goals_p90=result.get("projected_goals_p90"),
                projected_assists_p90=result.get("projected_assists_p90"),
                projected_xg_p90=result.get("projected_xg_p90"),
                ci_low_goals=result.get("ci_low_goals"),
                ci_high_goals=result.get("ci_high_goals"),
                adaptation_score_pct=result.get("adaptation_score_pct"),
                risk_score_pct=result.get("risk_score_pct"),
            )
            db.add(pred_record)
            db.commit()
    except Exception:
        db.rollback()

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
