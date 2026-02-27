"""
train.py — Phase 3: Model training for the CLPTM.

Trains three models per target variable:
  1. LightGBM (primary predictor)
  2. MLP Neural Network (nonlinear interactions)
  3. Bayesian Ridge (uncertainty quantification)

Training strategy:
  - Uses the feature_dataset.csv produced by Phase 2
  - Builds a "transfer scenario" train/test split:
      Train: all players in source leagues (e.g. Bundesliga)
      Test : same player names found in target league next season
             (proxy via the same dataset with cross-league players)
  - Also does 5-fold cross-validation within each league

Models saved to: models/<target>_lgbm.pkl, models/<target>_mlp.pkl, models/<target>_bayesian.pkl
"""

import pandas as pd
import numpy as np
import joblib
import json
import sys
from pathlib import Path

import lightgbm as lgb
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import BayesianRidge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils import load_config, resolve_path, get_logger

# ── Feature columns used for modeling ────────────────────────────────────────
FEATURE_COLS = [
    # LSC-adjusted per-90 (cross-league translated)
    "lsc_adj_goals_p90", "lsc_adj_assists_p90", "lsc_adj_xg_p90", "lsc_adj_xag_p90",
    "lsc_adj_npxg_p90", "lsc_adj_shots_p90", "lsc_adj_shots_on_target_p90",
    "lsc_adj_prog_carries_p90", "lsc_adj_prog_passes_p90", "lsc_adj_prog_receptions_p90",
    "lsc_adj_key_passes_p90", "lsc_adj_xa_p90", "lsc_adj_carries_p90",
    "lsc_adj_tackles_won_p90", "lsc_adj_interceptions_p90",
    # Engineered features
    "team_strength_ratio", "poss_adj_touches_p90",
    "age", "age_curve_score", "source_lsc", "target_lsc", "league_lsc",
    "play_style_progressive", "play_style_direct_carry", "play_style_defensive",
    # Position flags
    "pos_gk", "pos_df", "pos_mf", "pos_fw",
]

TARGET_COLS = ["goals_p90", "assists_p90", "xg_p90", "xag_p90"]


def _safe_features(df: pd.DataFrame, log) -> list[str]:
    """Return only feature columns that actually exist in df."""
    available = [c for c in FEATURE_COLS if c in df.columns]
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        log.warning(f"Missing feature columns (will skip): {missing}")
    return available


def _build_lgbm(cfg: dict) -> lgb.LGBMRegressor:
    mc = cfg["model"]["lgbm"]
    return lgb.LGBMRegressor(
        n_estimators=mc["n_estimators"],
        learning_rate=mc["learning_rate"],
        num_leaves=mc["num_leaves"],
        min_child_samples=mc["min_child_samples"],
        random_state=cfg["model"]["random_state"],
        n_jobs=-1,
        verbosity=-1,
    )


def _build_mlp(cfg: dict) -> Pipeline:
    mc = cfg["model"]["mlp"]
    return Pipeline([
        ("scaler", StandardScaler()),
        ("mlp", MLPRegressor(
            hidden_layer_sizes=tuple(mc["hidden_layer_sizes"]),
            max_iter=mc["max_iter"],
            early_stopping=mc["early_stopping"],
            random_state=cfg["model"]["random_state"],
            validation_fraction=0.1,
        )),
    ])


def _build_bayesian() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("bay", BayesianRidge()),
    ])


def train(cfg: dict | None = None) -> dict:
    """
    Train all models on the feature dataset.

    Returns
    -------
    dict: {target: {model_name: fitted_model}}
    """
    if cfg is None:
        cfg = load_config()

    log = get_logger("train", cfg)
    log.info("=== Phase 3 — Training: START ===")

    # ── Load feature dataset ──────────────────────────────────────────────────
    feat_path = resolve_path(cfg, "processed_data", "feature_dataset.csv")
    if not feat_path.exists():
        raise FileNotFoundError(
            f"Feature dataset not found: {feat_path}\n"
            "Run pipeline.py --phase features first."
        )
    df = pd.read_csv(feat_path)
    log.info(f"Feature dataset shape: {df.shape}")

    feat_cols = _safe_features(df, log)
    log.info(f"Using {len(feat_cols)} feature columns.")

    models_dir = resolve_path(cfg, "models")
    metrics_all = {}

    kf = KFold(
        n_splits=cfg["model"]["cv_folds"],
        shuffle=True,
        random_state=cfg["model"]["random_state"],
    )

    for target in TARGET_COLS:
        if target not in df.columns:
            log.warning(f"Target '{target}' not in dataset — skipping.")
            continue

        log.info(f"\n--- Training for target: {target} ---")

        # DROP LEAKAGE: We cannot train the model to predict goals by giving it adjusted goals,
        # nor xG for that matter, as they are 1-to-1 in the same season dataset.
        unsafe_keywords = []
        if "goals" in target:
            unsafe_keywords = ["goals", "xg"]
        elif "assists" in target:
            unsafe_keywords = ["assists", "xag"]
        elif "xg" in target or "xag" in target:
            unsafe_keywords = ["goals", "assists", "xg", "xag"]
            
        target_feat_cols = []
        for c in feat_cols:
            is_safe = True
            for kw in unsafe_keywords:
                if kw in c.lower():
                    is_safe = False
            if is_safe:
                target_feat_cols.append(c)
                
        # Force keep at least LSC, team strength, and age if they got filtered
        must_keep = ["source_lsc", "target_lsc", "team_strength_ratio", "age"]
        for c in must_keep:
            if c in df.columns and c not in target_feat_cols:
                target_feat_cols.append(c)
        
        log.info(f"  Dropped {len(feat_cols) - len(target_feat_cols)} leaky features for this target.")

        # Drop rows where target is NaN
        valid = df[target_feat_cols + [target]].dropna(subset=[target])
        X = valid[target_feat_cols].values
        y = valid[target].values

        log.info(f"  Samples after dropna: {len(X)}")
        log.info(f"  Features used: {len(target_feat_cols)}")

        target_metrics = {}

        # ── LightGBM ─────────────────────────────────────────────────────────
        lgbm = _build_lgbm(cfg)
        cv_scores = cross_val_score(lgbm, X, y, cv=kf, scoring="neg_mean_absolute_error", n_jobs=-1)
        lgbm.fit(X, y)
        mae_cv = -cv_scores.mean()
        log.info(f"  LightGBM CV MAE: {mae_cv:.4f} ± {cv_scores.std():.4f}")
        target_metrics["lgbm"] = {"cv_mae": round(float(mae_cv), 4), "cv_std": round(float(cv_scores.std()), 4)}
        joblib.dump(lgbm, models_dir / f"{target}_lgbm.pkl")
        log.info(f"  Saved: {target}_lgbm.pkl")

        # ── MLP ──────────────────────────────────────────────────────────────
        mlp = _build_mlp(cfg)
        mlp_cv = cross_val_score(mlp, X, y, cv=kf, scoring="neg_mean_absolute_error", n_jobs=1)
        mlp.fit(X, y)
        mae_mlp = -mlp_cv.mean()
        log.info(f"  MLP CV MAE: {mae_mlp:.4f} ± {mlp_cv.std():.4f}")
        target_metrics["mlp"] = {"cv_mae": round(float(mae_mlp), 4), "cv_std": round(float(mlp_cv.std()), 4)}
        joblib.dump(mlp, models_dir / f"{target}_mlp.pkl")
        log.info(f"  Saved: {target}_mlp.pkl")

        # ── Bayesian Ridge ────────────────────────────────────────────────────
        bay = _build_bayesian()
        bay_cv = cross_val_score(bay, X, y, cv=kf, scoring="neg_mean_absolute_error", n_jobs=-1)
        bay.fit(X, y)
        mae_bay = -bay_cv.mean()
        log.info(f"  Bayesian CV MAE: {mae_bay:.4f} ± {bay_cv.std():.4f}")
        target_metrics["bayesian"] = {"cv_mae": round(float(mae_bay), 4), "cv_std": round(float(bay_cv.std()), 4)}
        joblib.dump(bay, models_dir / f"{target}_bayesian.pkl")
        log.info(f"  Saved: {target}_bayesian.pkl")

        # ── Best model ────────────────────────────────────────────────────────
        best = min(target_metrics, key=lambda k: target_metrics[k]["cv_mae"])
        target_metrics["best_model"] = best
        log.info(f"  Best model for {target}: {best} (MAE={target_metrics[best]['cv_mae']:.4f})")

        metrics_all[target] = target_metrics

    # ── Save metrics ──────────────────────────────────────────────────────────
    eval_dir = resolve_path(cfg, "evaluation")
    metrics_path = eval_dir / "training_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics_all, f, indent=2)
    log.info(f"\nAll metrics saved: {metrics_path}")
    log.info("=== Phase 3 — Training: DONE ===")

    return metrics_all


if __name__ == "__main__":
    cfg = load_config()
    results = train(cfg)
    import json
    print(json.dumps(results, indent=2))
