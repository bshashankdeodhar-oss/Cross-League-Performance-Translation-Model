"""
scenario_sim.py — Phase 5: Scenario / What-If Simulator.

Allows manual perturbation of player features and shows how predictions change.
Useful for answering:
  "What if this player joined a top-4 team instead of a mid-table team?"
  "What if he were 3 years younger?"

Usage:
  python src/explainability/scenario_sim.py --player "Florian Wirtz" --vary team_strength_ratio 0.8 1.0 1.2
"""

import pandas as pd
import numpy as np
import joblib
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils import load_config, resolve_path, get_logger
from src.models.train import FEATURE_COLS, TARGET_COLS


def simulate(
    player_name: str,
    vary_feature: str,
    values: list[float],
    target: str = "goals_p90",
    cfg: dict | None = None,
) -> pd.DataFrame:
    """
    Vary a single feature for a player and show prediction deltas.

    Parameters
    ----------
    player_name : str
    vary_feature : str  — must be in FEATURE_COLS
    values : list[float] — list of values to test for that feature
    target : str — prediction target
    cfg : dict

    Returns
    -------
    pd.DataFrame with columns [vary_feature, target_predicted]
    """
    if cfg is None:
        cfg = load_config()

    log = get_logger("scenario_sim", cfg)

    # ── Load dataset ──────────────────────────────────────────────────────────
    feat_path = resolve_path(cfg, "processed_data", "feature_dataset.csv")
    df = pd.read_csv(feat_path)
    feat_cols = [c for c in FEATURE_COLS if c in df.columns]

    # ── Find player row ───────────────────────────────────────────────────────
    player_rows = df[df["player"].str.lower() == player_name.lower()]
    if player_rows.empty:
        log.error(f"Player '{player_name}' not found in dataset.")
        return pd.DataFrame()

    player_row = player_rows.iloc[0]
    base_features = player_row[feat_cols].fillna(0).values.copy()

    if vary_feature not in feat_cols:
        log.error(f"Feature '{vary_feature}' not in model feature set.")
        log.info(f"Available features: {feat_cols}")
        return pd.DataFrame()

    feat_idx = feat_cols.index(vary_feature)

    # ── Load model ────────────────────────────────────────────────────────────
    models_dir = resolve_path(cfg, "models")
    model_path = models_dir / f"{target}_lgbm.pkl"
    if not model_path.exists():
        log.error(f"Model not found: {model_path}")
        return pd.DataFrame()
    model = joblib.load(model_path)

    # ── Simulate ──────────────────────────────────────────────────────────────
    rows = []
    for val in values:
        features = base_features.copy()
        features[feat_idx] = val
        pred = model.predict(features.reshape(1, -1))[0]
        rows.append({vary_feature: val, f"{target}_predicted": round(float(pred), 4)})

    result = pd.DataFrame(rows)
    log.info(f"\nScenario simulation for {player_name} | vary: {vary_feature} | target: {target}")
    log.info(f"\n{result.to_string(index=False)}")
    return result


def main():
    parser = argparse.ArgumentParser(description="CLPTM Scenario Simulator")
    parser.add_argument("--player", type=str, required=True, help="Player name")
    parser.add_argument("--feature", type=str, required=True, help="Feature to vary")
    parser.add_argument("--values", type=float, nargs="+", required=True, help="Values to test")
    parser.add_argument("--target", type=str, default="goals_p90", choices=TARGET_COLS)
    args = parser.parse_args()

    cfg = load_config()
    result = simulate(args.player, args.feature, args.values, args.target, cfg)
    if not result.empty:
        print(result.to_string(index=False))


if __name__ == "__main__":
    main()
