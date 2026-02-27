"""
evaluate.py — Phase 3: Model evaluation and transfer backtest.

Evaluates all trained models against known transfer cases:
  - Players appearing in Bundesliga who later appear in Premier League
    (or vice versa) within the same dataset across available seasons.

Outputs:
  - evaluation/metrics.json (MAE, RMSE per model per target)
  - evaluation/backtest_report.csv (player-level predictions vs actuals)
  - evaluation/calibration_<target>.png (calibration plots)
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
from sklearn.metrics import mean_absolute_error, mean_squared_error

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils import load_config, resolve_path, get_logger
from src.models.train import FEATURE_COLS, TARGET_COLS


def _load_model(models_dir: Path, target: str, model_name: str):
    model_path = models_dir / f"{target}_{model_name}.pkl"
    if model_path.exists():
        return joblib.load(model_path)
    return None


def _plot_calibration(y_true, y_pred, target, model_name, eval_dir: Path):
    """Scatter plot of predicted vs actual values."""
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(y_pred, y_true, alpha=0.5, s=20, color="#3a7ebf")
    lim_min = min(y_pred.min(), y_true.min()) - 0.05
    lim_max = max(y_pred.max(), y_true.max()) + 0.05
    ax.plot([lim_min, lim_max], [lim_min, lim_max], "r--", linewidth=1.5, label="Perfect prediction")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"Calibration — {target} ({model_name})")
    ax.legend()
    plt.tight_layout()
    out = eval_dir / f"calibration_{target}_{model_name}.png"
    fig.savefig(out, dpi=100)
    plt.close(fig)
    return out


def evaluate(cfg: dict | None = None) -> dict:
    """
    Run evaluation on all trained models using the feature dataset.

    Returns
    -------
    dict: full metrics dictionary
    """
    if cfg is None:
        cfg = load_config()

    log = get_logger("evaluate", cfg)
    log.info("=== Phase 3 — Evaluation: START ===")

    feat_path = resolve_path(cfg, "processed_data", "feature_dataset.csv")
    df = pd.read_csv(feat_path)
    models_dir = resolve_path(cfg, "models")
    eval_dir = resolve_path(cfg, "evaluation")

    feat_cols_available = [c for c in FEATURE_COLS if c in df.columns]
    log.info(f"Feature columns available: {len(feat_cols_available)}")

    # ── Build a transfer "backtest" set ───────────────────────────────────────
    # Players in Bundesliga → also in PL (cross-league in same dataset)
    leagues = cfg["leagues"]
    if len(leagues) >= 2:
        league_a, league_b = leagues[0], leagues[1]
        players_a = set(df[df["league"] == league_a]["player"].str.strip())
        players_b = set(df[df["league"] == league_b]["player"].str.strip())
        transfer_players = players_a & players_b
        log.info(f"Cross-league players (backtest set): {len(transfer_players)}")
    else:
        transfer_players = set()

    all_metrics = {}
    backtest_rows = []
    model_names = ["lgbm", "mlp", "bayesian"]

    for target in TARGET_COLS:
        if target not in df.columns:
            log.warning(f"Target '{target}' not in dataset — skipping.")
            continue

        log.info(f"\n--- Evaluating: {target} ---")
        
        unsafe_keywords = []
        if "goals" in target:
            unsafe_keywords = ["goals", "xg"]
        elif "assists" in target:
            unsafe_keywords = ["assists", "xag"]
        elif "xg" in target or "xag" in target:
            unsafe_keywords = ["goals", "assists", "xg", "xag"]
            
        target_feat_cols = []
        for c in feat_cols_available:
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
                
        valid = df[target_feat_cols + [target, "player", "league"]].dropna(subset=[target])
        X = valid[target_feat_cols].values
        y = valid[target].values

        target_metrics = {}

        for model_name in model_names:
            model = _load_model(models_dir, target, model_name)
            if model is None:
                log.warning(f"  Model not found: {target}_{model_name}.pkl")
                continue

            y_pred = model.predict(X)
            mae = mean_absolute_error(y, y_pred)
            rmse = float(np.sqrt(mean_squared_error(y, y_pred)))
            log.info(f"  {model_name}: MAE={mae:.4f}, RMSE={rmse:.4f}")
            target_metrics[model_name] = {"mae": round(mae, 4), "rmse": round(rmse, 4)}

            # Calibration plot
            plot_path = _plot_calibration(y, y_pred, target, model_name, eval_dir)
            log.info(f"  Saved calibration plot: {plot_path}")

        # ── Transfer backtest ─────────────────────────────────────────────────
        if transfer_players:
            backtest_df = valid[valid["player"].isin(transfer_players)].copy()
            if len(backtest_df) > 0:
                X_bt = backtest_df[target_feat_cols].values
                y_bt = backtest_df[target].values

                best_model_name = min(
                    target_metrics,
                    key=lambda k: target_metrics[k]["mae"],
                    default=None
                )
                if best_model_name:
                    best_model = _load_model(models_dir, target, best_model_name)
                    y_bt_pred = best_model.predict(X_bt)
                    bt_mae = mean_absolute_error(y_bt, y_bt_pred)
                    log.info(f"  Backtest MAE ({best_model_name}): {bt_mae:.4f} on {len(y_bt)} transfer players")
                    target_metrics["backtest_mae"] = round(bt_mae, 4)
                    target_metrics["backtest_n"] = len(y_bt)

                    for i, player in enumerate(backtest_df["player"].values):
                        backtest_rows.append({
                            "player": player,
                            "target": target,
                            "actual": round(float(y_bt[i]), 4),
                            "predicted": round(float(y_bt_pred[i]), 4),
                            "error": round(float(abs(y_bt[i] - y_bt_pred[i])), 4),
                            "model": best_model_name,
                        })

        all_metrics[target] = target_metrics

    # ── Save metrics ──────────────────────────────────────────────────────────
    with open(eval_dir / "metrics.json", "w") as f:
        json.dump(all_metrics, f, indent=2)
    log.info(f"\nMetrics saved: {eval_dir / 'metrics.json'}")

    if backtest_rows:
        bt_df = pd.DataFrame(backtest_rows)
        bt_path = eval_dir / "backtest_report.csv"
        bt_df.to_csv(bt_path, index=False)
        log.info(f"Backtest report saved: {bt_path} ({len(bt_df)} rows)")

    log.info("=== Phase 3 — Evaluation: DONE ===")
    return all_metrics


if __name__ == "__main__":
    cfg = load_config()
    results = evaluate(cfg)
    import json
    print(json.dumps(results, indent=2))
