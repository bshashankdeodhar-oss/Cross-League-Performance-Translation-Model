"""
predict.py — Phase 6: Unified inference endpoint for the CLPTM.

Given a player name, source league, and target league, this module:
  1. Looks up the player in the feature dataset
  2. Applies LSC adjustment for the target league
  3. Predicts goals_p90, assists_p90, xg_p90, xag_p90
  4. Computes adaptation_score and risk_score
  5. Estimates confidence intervals using Bayesian Ridge model
  6. Returns top-5 SHAP factors driving the prediction

Usage:
  python src/predict.py --player "Florian Wirtz" --source "Bundesliga" --target "Premier League"
"""

import pandas as pd
import numpy as np
import joblib
import json
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils import load_config, resolve_path, get_logger
from src.models.train import FEATURE_COLS, TARGET_COLS
from src.explainability.shap_analysis import explain_prediction


def _load_model(models_dir: Path, target: str, model_name: str):
    p = models_dir / f"{target}_{model_name}.pkl"
    return joblib.load(p) if p.exists() else None


def _apply_target_lsc(features: np.ndarray, feat_cols: list, source_lsc: float, target_lsc: float) -> np.ndarray:
    """Re-scale LSC-adjusted features for a different target league."""
    features = features.copy()
    # lsc_adj_* cols were computed as: raw * (source_lsc / ref_lsc)
    # To "move" to target league: multiply by (target_lsc / source_lsc) but
    # the model already sees LSC-adjusted values; we just update league_lsc
    lsc_idx = feat_cols.index("league_lsc") if "league_lsc" in feat_cols else -1
    if lsc_idx >= 0:
        features[lsc_idx] = target_lsc
    # Scale lsc_adj_* columns (offensive): original * (target_lsc/source_lsc)
    for i, col in enumerate(feat_cols):
        if col.startswith("lsc_adj_") and "tackles" not in col and "interceptions" not in col:
            features[i] = features[i] * (target_lsc / source_lsc)
        elif col.startswith("lsc_adj_") and ("tackles" in col or "interceptions" in col):
            features[i] = features[i] * (source_lsc / target_lsc)  # inverted
    return features


def predict_player(
    player_name: str,
    source_league: str,
    target_league: str,
    cfg: dict | None = None,
) -> dict:
    """
    Full prediction for a single player transfer scenario.

    Returns
    -------
    dict with keys:
      player, source_league, target_league,
      projected_goals_p90, projected_assists_p90, projected_xg_p90, projected_xag_p90,
      ci_low_goals, ci_high_goals,
      minutes_expectation,
      adaptation_score, risk_score,
      top_5_factors (list),
      explanation (str)
    """
    if cfg is None:
        cfg = load_config()

    log = get_logger("predict", cfg)
    lsc_map: dict = cfg["league_strength"]

    if source_league not in lsc_map:
        raise ValueError(f"Source league '{source_league}' not in config league_strength map.")
    if target_league not in lsc_map:
        raise ValueError(f"Target league '{target_league}' not in config league_strength map.")

    source_lsc = lsc_map[source_league]
    target_lsc = lsc_map[target_league]

    # ── Load data ─────────────────────────────────────────────────────────────
    feat_path = resolve_path(cfg, "processed_data", "feature_dataset.csv")
    if not feat_path.exists():
        raise FileNotFoundError(f"Feature dataset not found: {feat_path}. Run pipeline first.")

    df = pd.read_csv(feat_path)
    feat_cols = [c for c in FEATURE_COLS if c in df.columns]

    # ── Find player in source league ──────────────────────────────────────────
    mask = (df["player"].str.lower() == player_name.lower()) & (df["league"] == source_league)
    player_rows = df[mask]

    if player_rows.empty:
        # Fallback: search any league
        mask2 = df["player"].str.lower() == player_name.lower()
        player_rows = df[mask2]
        if player_rows.empty:
            raise ValueError(f"Player '{player_name}' not found in dataset.")
        log.warning(f"Player found in {player_rows['league'].values[0]} but not {source_league} — using found row.")

    player_row = player_rows.iloc[0]
    base_features = player_row[feat_cols].fillna(0).values.astype(float)

    # ── Apply target-league LSC rescaling ─────────────────────────────────────
    adjusted_features = _apply_target_lsc(base_features, feat_cols, source_lsc, target_lsc)

    models_dir = resolve_path(cfg, "models")
    projections = {}
    ci_results = {}

    for target in TARGET_COLS:
        # Primary: LightGBM
        lgbm = _load_model(models_dir, target, "lgbm")
        if lgbm:
            projections[target] = round(float(lgbm.predict(adjusted_features.reshape(1, -1))[0]), 4)

        # CI: Bayesian Ridge
        bay_pipeline = _load_model(models_dir, target, "bayesian")
        if bay_pipeline:
            bay_model = bay_pipeline.named_steps["bay"]
            scaler = bay_pipeline.named_steps["scaler"]
            X_scaled = scaler.transform(adjusted_features.reshape(1, -1))
            mean_pred, std_pred = bay_model.predict(X_scaled, return_std=True)
            ci_results[target] = {
                "low": round(float(max(0, mean_pred[0] - 1.96 * std_pred[0])), 4),
                "high": round(float(mean_pred[0] + 1.96 * std_pred[0]), 4),
            }

    # ── Minutes expectation (simple rule: 60% of source minutes) ─────────────
    source_minutes = float(player_row.get("minutes", 1800))
    minutes_expectation = round(source_minutes * (target_lsc / source_lsc) * 0.85, 0)

    # ── Adaptation & Risk scores ──────────────────────────────────────────────
    adapt_path = models_dir / "adaptation_model.pkl"
    risk_path = models_dir / "risk_model.pkl"
    meta_path = models_dir / "adaptation_meta.json"

    adaptation_score = 65.0  # default heuristic
    risk_score = 30.0

    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)

        if "features" in meta and adapt_path.exists():
            adapt_model = joblib.load(adapt_path)
            adapt_feat_cols = meta["features"]
            adapt_X = player_row[[c for c in adapt_feat_cols if c in player_row.index]].fillna(0).values.reshape(1, -1)
            try:
                adapt_proba = adapt_model.predict_proba(adapt_X)[0][1]
                adaptation_score = round(float(adapt_proba) * 100, 1)
            except Exception:
                pass

        if "features" in meta and risk_path.exists():
            risk_model = joblib.load(risk_path)
            risk_feat_cols = meta["features"]
            risk_X = player_row[[c for c in risk_feat_cols if c in player_row.index]].fillna(0).values.reshape(1, -1)
            try:
                risk_proba = risk_model.predict_proba(risk_X)[0][1]
                risk_score = round(float(risk_proba) * 100, 1)
            except Exception:
                pass

    # ── SHAP top-5 factors ────────────────────────────────────────────────────
    top_factors = explain_prediction(
        adjusted_features, "goals_p90", feat_cols, models_dir, log
    )

    # ── Build result ──────────────────────────────────────────────────────────
    goals_ci = ci_results.get("goals_p90", {"low": None, "high": None})
    result = {
        "player":                   player_name,
        "source_league":            source_league,
        "target_league":            target_league,
        "source_lsc":               source_lsc,
        "target_lsc":               target_lsc,
        "projected_goals_p90":      projections.get("goals_p90"),
        "projected_assists_p90":    projections.get("assists_p90"),
        "projected_xg_p90":         projections.get("xg_p90"),
        "projected_xag_p90":        projections.get("xag_p90"),
        "ci_low_goals":             goals_ci["low"],
        "ci_high_goals":            goals_ci["high"],
        "minutes_expectation":      minutes_expectation,
        "adaptation_score_pct":     adaptation_score,
        "risk_score_pct":           risk_score,
        "top_5_factors":            top_factors,
    }

    log.info(f"Prediction complete for {player_name} ({source_league} → {target_league})")
    return result


def main():
    parser = argparse.ArgumentParser(description="CLPTM — Player Transfer Prediction")
    parser.add_argument("--player",  type=str, required=True)
    parser.add_argument("--source",  type=str, required=True, help="Source league")
    parser.add_argument("--target",  type=str, required=True, help="Target league")
    args = parser.parse_args()

    cfg = load_config()
    result = predict_player(args.player, args.source, args.target, cfg)

    from src.report import render_report
    print(render_report(result))


if __name__ == "__main__":
    main()
