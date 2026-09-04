"""
Unit and integration tests for the CLPTM FastAPI endpoints.
Tests database-backed /players and /leagues endpoints.
"""

import os
# Ensure SQLite is used for unit tests
os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from db.session import engine, SessionLocal, Base, get_db
from db.models import Player, League, Team, User, PlayerStats, PlayerStyleProfile, TransferPrediction
from scripts.load_to_postgres import load_dataset_to_db
from api.main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    load_dataset_to_db()
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test_api.db"):
        try:
            os.remove("test_api.db")
        except OSError:
            pass


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_success():
    response = client.post(
        "/auth/login",
        data={"username": "viewer", "password": "viewer123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_admin_success():
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_invalid():
    response = client.post(
        "/auth/login",
        data={"username": "viewer", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_unauthorized_access():
    response = client.get("/leagues")
    assert response.status_code == 401


def test_get_leagues():
    login_resp = client.post(
        "/auth/login",
        data={"username": "viewer", "password": "viewer123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/leagues", headers=headers)
    assert response.status_code == 200
    leagues = response.json()
    assert "Bundesliga" in leagues
    assert "Premier League" in leagues


def test_list_players():
    login_resp = client.post(
        "/auth/login",
        data={"username": "viewer", "password": "viewer123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/players?limit=10", headers=headers)
    assert response.status_code == 200
    players = response.json()
    assert isinstance(players, list)
    assert len(players) > 0
    assert "player" in players[0]
    assert "team" in players[0]
    assert "league" in players[0]
    assert "position" in players[0]
    assert "age" in players[0]


def test_list_players_filter_league():
    login_resp = client.post(
        "/auth/login",
        data={"username": "viewer", "password": "viewer123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/players?league=Bundesliga&limit=5", headers=headers)
    assert response.status_code == 200
    players = response.json()
    assert len(players) > 0
    for p in players:
        assert p["league"] == "Bundesliga"


def test_list_players_search_name():
    login_resp = client.post(
        "/auth/login",
        data={"username": "viewer", "password": "viewer123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/players?search=Wirtz", headers=headers)
    assert response.status_code == 200
    players = response.json()
    assert len(players) > 0
    assert "Wirtz" in players[0]["player"]


def test_get_teams():
    login_resp = client.post(
        "/auth/login",
        data={"username": "viewer", "password": "viewer123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/teams?league=Bundesliga", headers=headers)
    assert response.status_code == 200
    teams = response.json()
    assert isinstance(teams, list)
    if len(teams) > 0:
        assert "team" in teams[0]
        assert "league" in teams[0]
        assert "team_strength_ratio" in teams[0]


def test_predict():
    login_resp = client.post(
        "/auth/login",
        data={"username": "viewer", "password": "viewer123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "player": "Florian Wirtz",
        "source_league": "Bundesliga",
        "target_league": "Premier League",
    }
    response = client.post("/predict", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["player"] == "Florian Wirtz"
    assert "adaptation_score_pct" in data
    assert "top_5_factors" in data


def test_predict_with_target_team():
    login_resp = client.post(
        "/auth/login",
        data={"username": "viewer", "password": "viewer123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "player": "Florian Wirtz",
        "source_league": "Bundesliga",
        "target_league": "Premier League",
        "target_team": "Manchester City",
    }
    response = client.post("/predict", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["player"] == "Florian Wirtz"
    assert data["target_team"] == "Manchester City"
    assert "target_team_strength_ratio" in data
    assert data["target_team_strength_ratio"] is not None


def test_admin_retrain_forbidden_for_viewer():
    login_resp = client.post(
        "/auth/login",
        data={"username": "viewer", "password": "viewer123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/admin/retrain", headers=headers)
    assert response.status_code == 403


@patch("subprocess.run")
def test_admin_retrain_success(mock_run):
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "Retrain complete output"
    mock_proc.stderr = ""
    mock_run.return_value = mock_proc

    login_resp = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin123"},
    )
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/admin/retrain", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "retrain complete"


def test_relational_schema_and_prediction_audit():
    session = SessionLocal()
    try:
        # 1. Verify League table
        leagues = session.query(League).all()
        assert len(leagues) >= 5
        lg_names = [lg.league_name for lg in leagues]
        assert "Premier League" in lg_names
        assert "Bundesliga" in lg_names

        # 2. Verify Team table
        teams = session.query(Team).all()
        assert len(teams) > 0
        assert teams[0].team_strength_ratio > 0

        # 3. Verify User table
        users = session.query(User).all()
        unames = [u.username for u in users]
        assert "admin" in unames
        assert "viewer" in unames

        # 4. Verify Player, PlayerStats, and PlayerStyleProfile
        player = session.query(Player).filter(Player.player_name == "Florian Wirtz").first()
        assert player is not None
        assert player.league_rel is not None
        assert player.stats is not None
        assert player.style_profile is not None

        # 5. Verify TransferPrediction audit record logged
        preds = session.query(TransferPrediction).all()
        assert len(preds) > 0
        assert preds[0].projected_goals_p90 is not None
        assert preds[0].source_league is not None
        assert preds[0].target_league is not None
    finally:
        session.close()
