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
from db.models import Player
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
