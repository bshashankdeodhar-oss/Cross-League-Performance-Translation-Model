"""
Unit tests for the Tactical Fit and Squad Upgrade module.
"""

import pandas as pd
import pytest
from src.tactics.tactical_fit import analyze_tactical_fit
from src.utils import load_config, resolve_path


@pytest.fixture(scope="module")
def feature_df():
    cfg = load_config()
    feat_path = resolve_path(cfg, "processed_data", "feature_dataset.csv")
    return pd.read_csv(feat_path)


def test_tactical_fit_defender_with_team(feature_df):
    schlotter = feature_df[feature_df["player"] == "Nico Schlotterbeck"].iloc[-1]
    proj = {
        "projected_prog_passes_p90": 8.201,
        "projected_tackles_won_p90": 0.306,
        "projected_interceptions_p90": 0.360,
        "projected_clearances_p90": 0.536,
        "projected_prog_carries_p90": 0.553,
    }

    res = analyze_tactical_fit(
        player_row=schlotter,
        projections=proj,
        target_team="Cardiff City",
        target_league="Premier League",
        df=feature_df,
        target_team_strength=0.97,
        adaptation_score=41.3,
    )

    assert res["target_team"] == "Cardiff City"
    assert "Cardiff City DF Baseline" in res["baseline_scope"]
    assert len(res["upgrades"]) >= 4
    assert "Ball-Playing Center-Back" in res["tactical_archetype"]
    assert res["compatibility_score_pct"] > 50.0
    assert len(res["recommended_formations"]) >= 2
    assert len(res["key_instructions"]) >= 2

    # Verify Ball Progression upgrade exists and is positive
    prog_upgrade = next(u for u in res["upgrades"] if "Ball Progression" in u["metric"])
    assert prog_upgrade["pct_change"] > 0
    assert prog_upgrade["badge"] == "▲"


def test_tactical_fit_midfielder_with_team(feature_df):
    wirtz = feature_df[feature_df["player"] == "Florian Wirtz"].iloc[-1]
    proj = {
        "projected_key_passes_p90": 2.845,
        "projected_prog_passes_p90": 6.980,
        "projected_xag_p90": 0.297,
        "projected_tackles_won_p90": 0.215,
        "projected_goals_p90": 0.306,
    }

    res = analyze_tactical_fit(
        player_row=wirtz,
        projections=proj,
        target_team="Manchester City",
        target_league="Premier League",
        df=feature_df,
        target_team_strength=1.45,
        adaptation_score=40.9,
    )

    assert res["target_team"] == "Manchester City"
    assert "Manchester City MF Baseline" in res["baseline_scope"]
    assert res["compatibility_score_pct"] >= 80.0  # High synergy with Man City
    assert len(res["recommended_formations"]) >= 2

    # Check key passes upgrade
    kp_upgrade = next(u for u in res["upgrades"] if "Chances Created" in u["metric"])
    assert kp_upgrade["pct_change"] > 0


def test_tactical_fit_no_target_team_fallback(feature_df):
    wirtz = feature_df[feature_df["player"] == "Florian Wirtz"].iloc[-1]
    proj = {
        "projected_key_passes_p90": 2.683,
        "projected_prog_passes_p90": 6.497,
        "projected_xag_p90": 0.268,
        "projected_tackles_won_p90": 0.216,
        "projected_goals_p90": 0.289,
    }

    res = analyze_tactical_fit(
        player_row=wirtz,
        projections=proj,
        target_team=None,
        target_league="Premier League",
        df=feature_df,
        target_team_strength=1.0,
        adaptation_score=40.9,
    )

    assert res["target_team"] is None
    assert "Premier League MF Average" in res["baseline_scope"]
    assert len(res["upgrades"]) >= 4
    assert res["compatibility_score_pct"] > 50.0


def test_tactical_fit_goalkeeper(feature_df):
    neuer_rows = feature_df[feature_df["player"].str.contains("Neuer", case=False, na=False)]
    if neuer_rows.empty:
        pytest.skip("Manuel Neuer not found in dataset")

    neuer = neuer_rows.iloc[-1]
    proj = {
        "projected_clearances_p90": 0.85,
        "projected_touches_p90": 42.0,
        "projected_tackles_won_p90": 0.12,
    }

    res = analyze_tactical_fit(
        player_row=neuer,
        projections=proj,
        target_team="Arsenal",
        target_league="Premier League",
        df=feature_df,
        target_team_strength=1.19,
        adaptation_score=81.5,
    )

    assert "GK" in res["baseline_scope"]
    assert "Sweeper-Keeper" in res["tactical_archetype"] or "Goalkeeper" in res["tactical_archetype"]
    assert len(res["recommended_formations"]) >= 2
