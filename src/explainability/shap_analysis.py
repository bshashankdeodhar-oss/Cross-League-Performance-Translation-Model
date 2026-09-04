"""
shap_analysis.py — Phase 5: SHAP explainability for CLPTM predictions.

Uses SHAP TreeExplainer on the LightGBM models to:
  - Identify top-5 features driving each prediction
  - Generate SHAP summary plots saved to evaluation/
  - Return human-readable factor descriptions
"""

import pandas as pd
import numpy as np
import joblib
import json
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils import load_config, resolve_path, get_logger
from src.models.train import FEATURE_COLS

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

# Human-readable feature name map
FEATURE_LABELS = {
    "lsc_adj_goals_p90":             "Goals per 90 (league-adjusted)",
    "lsc_adj_assists_p90":           "Assists per 90 (league-adjusted)",
    "lsc_adj_xg_p90":                "xG per 90 (league-adjusted)",
    "lsc_adj_xag_p90":               "xAG per 90 (league-adjusted)",
    "lsc_adj_npxg_p90":              "Non-penalty xG per 90",
    "lsc_adj_shots_p90":             "Shots per 90 (league-adjusted)",
    "lsc_adj_shots_on_target_p90":   "Shots on target per 90",
    "lsc_adj_prog_carries_p90":      "Progressive carries per 90",
    "lsc_adj_prog_passes_p90":       "Progressive passes per 90",
    "lsc_adj_prog_receptions_p90":   "Progressive receptions per 90",
    "lsc_adj_key_passes_p90":        "Key passes per 90",
    "lsc_adj_xa_p90":                "xA per 90 (league-adjusted)",
    "lsc_adj_carries_p90":           "Carries per 90",
    "lsc_adj_tackles_won_p90":       "Tackles won per 90",
    "lsc_adj_interceptions_p90":     "Interceptions per 90",
    "team_strength_ratio":           "Team strength (relative to league avg)",
    "poss_adj_touches_p90":          "Possession-adjusted touches per 90",
    "age_curve_score":               "Age curve score (peak = 24–28)",
    "league_lsc":                    "Source league strength coefficient",
    "play_style_progressive":        "Progressive play style",
    "play_style_direct_carry":       "Direct carry play style",
    "play_style_defensive":          "Defensive contribution",
    "pos_gk": "Position: Goalkeeper",
    "pos_df": "Position: Defender",
    "pos_mf": "Position: Midfielder",
    "pos_fw": "Position: Forward",
}


def get_top_factors(shap_values: np.ndarray, feature_names: list, top_n: int = 5) -> list[dict]:
    """Extract top-N contributing features with direction and value."""
    abs_vals = np.abs(shap_values)
    top_indices = np.argsort(abs_vals)[::-1][:top_n]

    factors = []
    for idx in top_indices:
        factors.append({
            "feature": feature_names[idx],
            "label": FEATURE_LABELS.get(feature_names[idx], feature_names[idx]),
            "shap_value": round(float(shap_values[idx]), 4),
            "direction": "positive" if shap_values[idx] > 0 else "negative",
        })
    return factors


def explain_prediction(
    player_features: np.ndarray,
    target: str,
    feat_cols: list[str],
    models_dir: Path,
    log,
) -> list[dict]:
    """
    Compute SHAP values for a single player prediction using the LightGBM model.

    Returns list of top-5 factor dicts, or fallback feature importance if SHAP unavailable.
    """
    model_path = models_dir / f"{target}_lgbm.pkl"
    if not model_path.exists():
        log.warning(f"LightGBM model not found for {target}")
        return []

    model = joblib.load(model_path)

    if SHAP_AVAILABLE:
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(player_features.reshape(1, -1))[0]
        return get_top_factors(shap_vals, feat_cols, top_n=5)
    else:
        # Fallback: use feature importances directly
        log.warning("SHAP not available — using feature importances as fallback.")
        importances = model.feature_importances_
        top_indices = np.argsort(importances)[::-1][:5]
        return [
            {
                "feature": feat_cols[i],
                "label": FEATURE_LABELS.get(feat_cols[i], feat_cols[i]),
                "shap_value": round(float(importances[i]), 4),
                "direction": "positive",
            }
            for i in top_indices
        ]


def generate_shap_summary(cfg: dict | None = None):
    """
    Generate SHAP summary plots for all LightGBM models on the full dataset.
    Saves plots to evaluation/.
    """
    if cfg is None:
        cfg = load_config()

    log = get_logger("shap_analysis", cfg)
    log.info("=== Phase 5 — SHAP Analysis: START ===")

    if not SHAP_AVAILABLE:
        log.warning("SHAP library not installed. Skipping summary plots.")
        log.warning("Install with: pip install shap")
        return

    feat_path = resolve_path(cfg, "processed_data", "feature_dataset.csv")
    df = pd.read_csv(feat_path)
    feat_cols = [c for c in FEATURE_COLS if c in df.columns]

    models_dir = resolve_path(cfg, "models")
    eval_dir = resolve_path(cfg, "evaluation")

    from src.models.train import TARGET_COLS
    for target in TARGET_COLS:
        model_path = models_dir / f"{target}_lgbm.pkl"
        if not model_path.exists():
            log.warning(f"No LightGBM model for {target} — skipping.")
            continue

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

        must_keep = ["source_lsc", "target_lsc", "team_strength_ratio", "age"]
        for c in must_keep:
            if c in df.columns and c not in target_feat_cols:
                target_feat_cols.append(c)

        valid = df[target_feat_cols + [target]].dropna(subset=[target])
        # Sample for fast SHAP summary calculation
        sample_size = min(500, len(valid))
        sample_df = valid.sample(n=sample_size, random_state=42)
        X = sample_df[target_feat_cols].fillna(0).values
        model = joblib.load(model_path)

        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X)

            # Summary plot
            fig, ax = plt.subplots(figsize=(10, 6))
            shap.summary_plot(
                shap_values, X,
                feature_names=[FEATURE_LABELS.get(f, f) for f in target_feat_cols],
                show=False,
                plot_size=None,
            )
            out_path = eval_dir / f"shap_{target}.png"
            plt.tight_layout()
            plt.savefig(out_path, dpi=120, bbox_inches="tight")
            plt.close()
            log.info(f"  Saved SHAP summary: {out_path}")

        except Exception as e:
            log.error(f"  SHAP error for {target}: {e}")

    log.info("=== Phase 5 — SHAP Analysis: DONE ===")


if __name__ == "__main__":
    cfg = load_config()
    generate_shap_summary(cfg)
