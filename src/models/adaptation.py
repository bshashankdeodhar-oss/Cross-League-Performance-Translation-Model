"""
adaptation.py — Phase 4: Adaptation & risk modeling.

Predicts two things for a transferring player:
  1. `adaptation_score` (0-100%): Probability the player will perform at
     or above their source-league percentile within the first season.
  2. `risk_score` (0-100%): Probability of significant performance drop
     (defined as falling below 40th percentile in target league).

Both are logistic regression models trained on league-crossing signals
within the current dataset (players appearing in both leagues).

Note: With a single-season dataset, the adaptation model is limited.
It uses structural player features (age, minutes, LSC delta, team strength)
as proxies for adaptation likelihood.

Saved to:
  models/adaptation_model.pkl
  models/risk_model.pkl
"""

import pandas as pd
import numpy as np
import joblib
import json
import sys
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score, StratifiedKFold

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils import load_config, resolve_path, get_logger

ADAPTATION_FEATURES = [
    "age_curve_score",
    "league_lsc",
    "lsc_adj_goals_p90",
    "lsc_adj_assists_p90",
    "lsc_adj_xg_p90",
    "team_strength_ratio",
    "play_style_progressive",
    "play_style_direct_carry",
    "play_style_defensive",
    "pos_gk", "pos_df", "pos_mf", "pos_fw",
    "minutes",
]


def _create_adaptation_labels(df: pd.DataFrame, cfg: dict, log) -> pd.DataFrame:
    """
    Create binary adaptation labels for cross-league players.

    Uses empirical historical transfers from data_T5/cross_league_transfers_2018_2024.csv
    when available (955 longitudinal transfer pairs), otherwise falls back to
    same-season cross-league appearances.
    """
    xfer_file = Path("data_T5/cross_league_transfers_2018_2024.csv")
    if xfer_file.exists():
        log.info(f"Loading empirical cross-league transfers from: {xfer_file}")
        xfers = pd.read_csv(xfer_file)
        
        # Merge transfers with the engineered feature dataset on player + source league
        merged = pd.merge(xfers, df, left_on=["player", "league_src"], right_on=["player", "league"])
        log.info(f"Matched {len(merged)} transfer records ({merged['player'].nunique()} unique players) with feature set.")
        
        if not merged.empty:
            xg_ratio = merged["xg_p90_tgt"] / (merged["xg_p90_src"] + 0.05)
            min_ratio = merged["minutes_tgt"] / (merged["minutes_src"] + 100.0)
            
            # Successful adaptation: maintained >=70% xG/goals and played significant minutes
            merged["adaptation_label"] = (
                ((xg_ratio >= 0.70) | (merged["goals_p90_tgt"] >= 0.70 * merged["goals_p90_src"]))
                & (min_ratio >= 0.50)
            ).astype(int)
            
            # High transfer risk: severe production drop and lost playing time
            merged["risk_label"] = ((xg_ratio < 0.45) & (min_ratio < 0.65)).astype(int)
            
            log.info(f"Adaptation positive rate: {merged['adaptation_label'].mean():.1%}")
            log.info(f"Risk positive rate: {merged['risk_label'].mean():.1%}")
            return merged

    # Fallback to intra-dataset search
    leagues = cfg["leagues"]
    if len(leagues) < 2:
        log.warning("Need at least 2 leagues for adaptation labels.")
        return pd.DataFrame()

    league_a, league_b = leagues[0], leagues[1]

    df_a = df[df["league"] == league_a].copy()
    df_b = df[df["league"] == league_b].copy()

    if "goals_p90" in df_a.columns:
        df_a.loc[:, "goals_pct"] = df_a["goals_p90"].rank(pct=True)
        df_b.loc[:, "goals_pct"] = df_b["goals_p90"].rank(pct=True)

    cross = set(df_a["player"]) & set(df_b["player"])
    log.info(f"Cross-league players for adaptation labels: {len(cross)}")

    rows = []
    for player in cross:
        row_a = df_a[df_a["player"] == player]
        row_b = df_b[df_b["player"] == player]
        if len(row_a) != 1 or len(row_b) != 1:
            continue
        pct_a = row_a["goals_pct"].values[0] if "goals_pct" in row_a.columns else 0.5
        pct_b = row_b["goals_pct"].values[0] if "goals_pct" in row_b.columns else 0.5

        feat_row = row_a.iloc[0].to_dict()
        feat_row["adaptation_label"] = int(pct_b >= pct_a * 0.8)
        feat_row["risk_label"] = int(pct_b < 0.4)
        rows.append(feat_row)

    if not rows:
        log.warning("No cross-league players found for adaptation labels.")
        return pd.DataFrame()

    return pd.DataFrame(rows)


def train_adaptation(cfg: dict | None = None) -> dict:
    """
    Train adaptation and risk models.

    Returns
    -------
    dict: training metrics
    """
    if cfg is None:
        cfg = load_config()

    log = get_logger("adaptation", cfg)
    log.info("=== Phase 4 — Adaptation Modeling: START ===")

    feat_path = resolve_path(cfg, "processed_data", "feature_dataset.csv")
    df = pd.read_csv(feat_path)

    labeled = _create_adaptation_labels(df, cfg, log)

    if labeled.empty or len(labeled) < 5:
        log.warning(
            "Insufficient cross-league players for supervised adaptation training.\n"
            "Saving a rule-based fallback model instead."
        )
        stub = {"type": "rule_based", "note": "Insufficient training data for supervised adaptation model."}
        models_dir = resolve_path(cfg, "models")
        with open(models_dir / "adaptation_meta.json", "w") as f:
            json.dump(stub, f, indent=2)
        log.info("Saved rule-based stub metadata.")
        return stub

    feat_cols_av = [c for c in ADAPTATION_FEATURES if c in labeled.columns]
    log.info(f"Adaptation feature columns: {feat_cols_av}")

    models_dir = resolve_path(cfg, "models")
    metrics = {}
    skf = StratifiedKFold(n_splits=min(5, len(labeled)), shuffle=True, random_state=cfg["model"]["random_state"])

    for label_col, model_name in [("adaptation_label", "adaptation"), ("risk_label", "risk")]:
        if label_col not in labeled.columns:
            continue
        X = labeled[feat_cols_av].fillna(0).values
        y = labeled[label_col].values

        if len(np.unique(y)) < 2:
            log.warning(f"Only one class in '{label_col}' — skipping supervised training.")
            continue

        model = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=cfg["model"]["random_state"])),
        ])

        scores = cross_val_score(model, X, y, cv=skf, scoring="roc_auc")
        model.fit(X, y)
        log.info(f"  {model_name}: ROC-AUC = {scores.mean():.3f} ± {scores.std():.3f}")
        metrics[model_name] = {"roc_auc": round(float(scores.mean()), 3), "std": round(float(scores.std()), 3)}

        joblib.dump(model, models_dir / f"{model_name}_model.pkl")
        log.info(f"  Saved: {model_name}_model.pkl")

    # Save feature list used
    meta = {"features": feat_cols_av, "n_training_samples": len(labeled)}
    with open(models_dir / "adaptation_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    eval_dir = resolve_path(cfg, "evaluation")
    with open(eval_dir / "adaptation_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    log.info("=== Phase 4 — Adaptation Modeling: DONE ===")
    return metrics


if __name__ == "__main__":
    cfg = load_config()
    result = train_adaptation(cfg)
    import json
    print(json.dumps(result, indent=2))
