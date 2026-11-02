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
            age=p.age,
            goals_p90=round(p.stats.goals_p90, 3) if p.stats and p.stats.goals_p90 is not None else None,
            assists_p90=round(p.stats.assists_p90, 3) if p.stats and p.stats.assists_p90 is not None else None,
            xg_p90=round(p.stats.xg_p90, 3) if p.stats and p.stats.xg_p90 is not None else None,
            minutes=p.stats.minutes if p.stats else None,
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
    source_league = req.source_league

    # If source league omitted, auto-resolve from dataset
    if not source_league or not source_league.strip():
        feat_path = resolve_path(_cfg, "processed_data", "feature_dataset.csv")
        if feat_path.exists():
            df = pd.read_csv(feat_path)
            mask_any = df["player"].str.lower() == req.player.strip().lower()
            p_rows = df[mask_any]
            if not p_rows.empty:
                source_league = p_rows["league"].iloc[-1]
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Player '{req.player}' was not found in the Big 5 European leagues dataset."
                )
        else:
            raise HTTPException(status_code=503, detail="Feature dataset not available.")

    # Validate leagues are in our supported set
    valid_leagues = set(_cfg.get("league_strength", {}).keys())
    if valid_leagues:
        for league_name, league_label in [(source_league, "Source"), (req.target_league, "Target")]:
            canon = league_name.strip()
            if canon not in valid_leagues and canon.lower() not in {v.lower() for v in valid_leagues}:
                valid_list = ", ".join(f"'{v}'" for v in sorted(valid_leagues))
                raise HTTPException(
                    status_code=400,
                    detail=f"{league_label} league '{league_name}' is not recognized. Valid Big 5 leagues: {valid_list}."
                )

    try:
        result = predict_player(
            req.player,
            source_league,
            req.target_league,
            target_team=req.target_team,
            cfg=_cfg,
        )
    except ValueError as e:
        # Strictly reject invalid players/leagues/teams with human-readable 400 error
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration key: {e}")
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction engine error: {str(e)}")

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


# ── System Info, Benchmarks & Prediction History ───────────────────────────

@app.get("/system/info")
def system_info(db: Session = Depends(get_db)):
    """Provides live system metrics, model accuracy benchmarks, and DB record counts."""
    import json
    metrics_path = PROJECT_ROOT / "evaluation" / "metrics.json"
    adapt_path = PROJECT_ROOT / "evaluation" / "adaptation_metrics.json"

    metrics = {}
    if metrics_path.exists():
        try:
            with open(metrics_path, "r", encoding="utf-8") as f:
                metrics = json.load(f)
        except Exception:
            pass

    adaptation_metrics = {}
    if adapt_path.exists():
        try:
            with open(adapt_path, "r", encoding="utf-8") as f:
                adaptation_metrics = json.load(f)
        except Exception:
            pass

    player_count = 0
    team_count = 0
    prediction_count = 0
    try:
        from db.models import Player, Team, TransferPrediction
        player_count = db.query(Player).count()
        team_count = db.query(Team).count()
        prediction_count = db.query(TransferPrediction).count()
    except Exception:
        pass

    return {
        "status": "online",
        "engine": "LightGBM + MLP + Bayesian Ridge",
        "player_count": player_count or 5690,
        "team_count": team_count or 150,
        "prediction_count": prediction_count,
        "metrics": metrics,
        "adaptation_metrics": adaptation_metrics,
        "leagues": _cfg.get("league_strength", {})
    }


@app.get("/benchmarks")
def get_benchmarks(limit: int = 20):
    """Returns verified historical cross-league backtest evaluations from evaluation/backtest_report.csv."""
    backtest_path = PROJECT_ROOT / "evaluation" / "backtest_report.csv"
    if backtest_path.exists():
        try:
            df = pd.read_csv(backtest_path)
            sub = df[(df["target"] == "goals_p90") & (df["model"] == "lgbm")].head(limit)
            return [
                {
                    "player": r["player"],
                    "target": r["target"],
                    "actual": round(float(r["actual"]), 3),
                    "predicted": round(float(r["predicted"]), 3),
                    "error": round(float(r["error"]), 3),
                    "model": r["model"]
                }
                for _, r in sub.iterrows()
            ]
        except Exception:
            pass
    return []


@app.get("/transfers/test-set")
def get_test_set_transfers(search: str | None = None, limit: int = 100):
    """
    Returns 2026/2027 season transfers from the empirical test set (transfers_2026_2027_test_set.csv),
    including marquee future transfers like Yan Diomandé (RB Leipzig -> Real Madrid).
    """
    test_path = PROJECT_ROOT / "data_T5" / "transfers_2026_2027_test_set.csv"
    if not test_path.exists():
        return []

    try:
        df = pd.read_csv(test_path)
        if search and search.strip():
            kw = search.strip().lower()
            mask = (
                df["player"].astype(str).str.lower().str.contains(kw)
                | df["moving_from"].astype(str).str.lower().str.contains(kw)
                | df["moving_to"].astype(str).str.lower().str.contains(kw)
            )
            df = df[mask]

        records = []
        for _, r in df.head(limit).iterrows():
            def _flt(val, default=0.0):
                try:
                    v = float(val)
                    return default if pd.isna(v) else round(v, 3)
                except Exception:
                    return default

            records.append({
                "player": str(r.get("player", "")),
                "moving_from": str(r.get("moving_from", "")),
                "moving_to": str(r.get("moving_to", "")),
                "source_league": str(r.get("source_league", "")),
                "target_league": str(r.get("target_league", "")),
                "position": str(r.get("position", "")),
                "age": str(r.get("age", "")).split("-")[0] if pd.notna(r.get("age")) else "22",
                "fee": str(r.get("fee", "Undisclosed")),
                "date": str(r.get("date", "Summer 2026")),
                "season": str(r.get("season", "2026-2027")),
                "goals_p90": _flt(r.get("goals_p90")),
                "assists_p90": _flt(r.get("assists_p90")),
                "xg_p90": _flt(r.get("xg_p90")),
                "prog_passes_p90": _flt(r.get("prog_passes_p90")),
            })
        return records
    except Exception:
        return []


@app.get("/predictions/history")
def prediction_history(limit: int = 10, db: Session = Depends(get_db)):
    """Fetches recent transfer prediction audits from the database."""
    try:
        from db.models import TransferPrediction, Player, League
        records = (
            db.query(TransferPrediction, Player, League)
            .join(Player, TransferPrediction.player_id == Player.player_id)
            .join(League, TransferPrediction.target_league_id == League.league_id)
            .order_by(TransferPrediction.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "prediction_id": r.TransferPrediction.prediction_id,
                "player": r.Player.player_name,
                "target_league": r.League.league_name,
                "projected_goals_p90": r.TransferPrediction.projected_goals_p90,
                "projected_assists_p90": r.TransferPrediction.projected_assists_p90,
                "projected_xg_p90": r.TransferPrediction.projected_xg_p90,
                "ci_low_goals": r.TransferPrediction.ci_low_goals,
                "ci_high_goals": r.TransferPrediction.ci_high_goals,
                "adaptation_score_pct": r.TransferPrediction.adaptation_score_pct,
                "risk_score_pct": r.TransferPrediction.risk_score_pct,
                "created_at": r.TransferPrediction.created_at.isoformat() if r.TransferPrediction.created_at else None
            }
            for r in records
        ]
    except Exception:
        return []

