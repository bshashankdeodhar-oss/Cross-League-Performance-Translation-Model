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
import difflib
import sys
from pathlib import Path
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
warnings.filterwarnings("ignore", category=FutureWarning)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.utils import load_config, resolve_path, get_logger
from src.models.train import FEATURE_COLS, TARGET_COLS
from src.explainability.shap_analysis import explain_prediction
from src.tactics.tactical_fit import analyze_tactical_fit


def _load_model(models_dir: Path, target: str, model_name: str):
    p = models_dir / f"{target}_{model_name}.pkl"
    return joblib.load(p) if p.exists() else None


def _apply_target_lsc(features: np.ndarray, feat_cols: list, source_lsc: float, target_lsc: float) -> np.ndarray:
    """Re-scale LSC-adjusted features for a different target league."""
    features = features.copy()
    lsc_idx = feat_cols.index("league_lsc") if "league_lsc" in feat_cols else -1
    if lsc_idx >= 0:
        features[lsc_idx] = target_lsc
    # Scale lsc_adj_* columns:
    # Defensive disruption actions invert scaling (harder league = more defending required)
    for i, col in enumerate(feat_cols):
        if col.startswith("lsc_adj_") and any(d in col for d in ["tackles", "interceptions", "clearances"]):
            features[i] = features[i] * (source_lsc / target_lsc)
        elif col.startswith("lsc_adj_"):
            features[i] = features[i] * (target_lsc / source_lsc)
    return features


def _select_shap_target(player_row: pd.Series) -> tuple[str, str, list[str]]:
    """
    Dynamically select the most relevant primary target metric, human-readable label,
    and anti-leakage filter keywords based on the player's position and profile.
    """
    pos = str(player_row.get("position", "")).upper()
    prim = str(player_row.get("position_primary", "")).upper()
    combined = f"{pos} {prim}"

    if "GK" in combined:
        return "clearances_p90", "Clearances per 90 (Sweeper-Keeper Actions)", ["clearances"]
    elif "DF" in combined and "FW" not in combined:
        prog_p = float(player_row.get("prog_passes_p90", 0))
        tackles = float(player_row.get("tackles_won_p90", 0))
        if prog_p > 3.0 and prog_p > tackles * 1.8:
            return "prog_passes_p90", "Progressive Passes per 90 (Build-Up)", ["prog_passes"]
        else:
            return "tackles_won_p90", "Tackles Won per 90 (Defensive Disruption)", ["tackles_won"]
    elif "MF" in combined:
        goals = float(player_row.get("goals_p90", 0))
        key_p = float(player_row.get("key_passes_p90", 0))
        tackles = float(player_row.get("tackles_won_p90", 0))
        if goals >= 0.30:
            return "goals_p90", "Goals per 90 (Attacking Impact)", ["goals", "xg", "npxg"]
        elif tackles > key_p and tackles >= 1.5:
            return "tackles_won_p90", "Tackles Won per 90 (Defensive Workrate)", ["tackles_won"]
        else:
            return "key_passes_p90", "Key Passes per 90 (Chance Creation)", ["key_passes"]
    else:
        return "goals_p90", "Goals per 90 (Finishing)", ["goals", "xg", "npxg"]


def predict_player(
    player_name: str,
    source_league: str,
    target_league: str,
    target_team: str | None = None,
    cfg: dict | None = None,
) -> dict:
    """
    Full prediction for a single player transfer scenario.

    Returns
    -------
    dict with keys:
      player, source_league, target_league, target_team, target_team_strength_ratio,
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

    # ── Canonicalize Leagues ──────────────────────────────────────────────────
    def _canonicalize_league(name: str, lmap: dict) -> str:
        if name in lmap:
            return name
        for k in lmap:
            if k.lower() == name.strip().lower():
                return k
        aliases = {
            "epl": "Premier League",
            "pl": "Premier League",
            "prem": "Premier League",
            "laliga": "La Liga",
            "liga": "La Liga",
            "seriea": "Serie A",
            "ligue1": "Ligue 1",
        }
        cleaned = name.strip().lower().replace(" ", "").replace("_", "").replace("-", "")
        if cleaned in aliases and aliases[cleaned] in lmap:
            return aliases[cleaned]
        valid = ", ".join(repr(k) for k in lmap.keys())
        raise ValueError(f"Unrecognized league '{name}'. Valid Big 5 leagues are: {valid}.")

    source_league = _canonicalize_league(source_league, lsc_map)
    target_league = _canonicalize_league(target_league, lsc_map)

    source_lsc = lsc_map[source_league]
    target_lsc = lsc_map[target_league]

    # ── Load data ─────────────────────────────────────────────────────────────
    feat_path = resolve_path(cfg, "processed_data", "feature_dataset.csv")
    if not feat_path.exists():
        raise FileNotFoundError(f"Feature dataset not found: {feat_path}. Run pipeline first.")

    df = pd.read_csv(feat_path)
    feat_cols = [c for c in FEATURE_COLS if c in df.columns]

    # ── Strict Player & League Lookup ─────────────────────────────────────────
    player_name_clean = player_name.strip()
    mask = (df["player"].str.lower() == player_name_clean.lower()) & (
        df["league"].str.lower() == source_league.lower()
    )
    player_rows = df[mask]

    if player_rows.empty:
        # Check if the player exists in another league
        mask_any = df["player"].str.lower() == player_name_clean.lower()
        player_rows_any = df[mask_any]
        if player_rows_any.empty:
            # Fuzzy match suggestions for typo in player name
            all_players = sorted(df["player"].dropna().unique())
            close_matches = difflib.get_close_matches(player_name_clean, all_players, n=3, cutoff=0.6)
            suggestion = (
                f" Did you mean: {', '.join(repr(p) for p in close_matches)}?"
                if close_matches
                else ""
            )
            raise ValueError(f"Player '{player_name}' was not found in the Big 5 leagues dataset.{suggestion}")
        else:
            actual_leagues = player_rows_any["league"].unique().tolist()
            actual_str = ", ".join(actual_leagues)
            raise ValueError(
                f"Player '{player_name}' plays in {actual_str}, not in '{source_league}'. "
                f"Cannot generate transfer projection with incorrect source league. "
                f"Please specify --source \"{actual_leagues[-1]}\"."
            )

    # Use the most recent season available for the player
    player_row = player_rows.iloc[-1]
    base_features = player_row[feat_cols].fillna(0).values.astype(float)

    # ── Apply target-league LSC rescaling ─────────────────────────────────────
    adjusted_features = _apply_target_lsc(base_features, feat_cols, source_lsc, target_lsc)

    # ── Resolve Target Team Strength Context ──────────────────────────────────
    target_team_canonical = None
    target_team_strength = 1.0
    if target_team:
        target_team_clean = target_team.strip()
        valid_teams = sorted(df[df["league"].str.lower() == target_league.lower()]["team"].unique())

        # 1. Exact match in target league (case-insensitive)
        matched_team = None
        for t in valid_teams:
            if t.lower() == target_team_clean.lower():
                matched_team = t
                break

        # 2. Substring & word matches (e.g. "Man City" -> "Manchester City", "Wolves" -> "Wolves")
        if not matched_team:
            words = target_team_clean.lower().split()
            for t in valid_teams:
                if all(w in t.lower() for w in words):
                    matched_team = t
                    break
            if not matched_team:
                for w in reversed(words):
                    if len(w) > 3:
                        for t in valid_teams:
                            if w in t.lower():
                                matched_team = t
                                break
                        if matched_team:
                            break

        # 3. Fuzzy match within target league
        if not matched_team:
            close = difflib.get_close_matches(target_team_clean, valid_teams, n=1, cutoff=0.7)
            if close:
                matched_team = close[0]

        # 4. Strict Validation: Reject non-existent or cross-league teams
        if not matched_team:
            mask_any = df["team"].str.lower() == target_team_clean.lower()
            if mask_any.any():
                actual_lg = df[mask_any]["league"].iloc[0]
                actual_name = df[mask_any]["team"].iloc[0]
                raise ValueError(
                    f"Target team '{target_team}' does not play in {target_league}. "
                    f"{actual_name} plays in {actual_lg}. Please specify a valid {target_league} club."
                )

            all_teams = sorted(df["team"].unique())
            close_any = difflib.get_close_matches(target_team_clean, all_teams, n=1, cutoff=0.7)
            if close_any:
                other_lg = df[df["team"] == close_any[0]]["league"].iloc[0]
                raise ValueError(
                    f"Target team '{target_team}' was not found in {target_league}. "
                    f"Did you mean '{close_any[0]}' from {other_lg}?"
                )

            sample_teams = ", ".join(valid_teams[:8])
            raise ValueError(
                f"Target team '{target_team}' does not exist in {target_league} (Big 5 top-flight dataset). "
                f"Valid {target_league} clubs include: {sample_teams}, etc."
            )

        target_team_canonical = matched_team
        sub_team = df[(df["league"].str.lower() == target_league.lower()) & (df["team"] == matched_team)]
        target_team_strength = float(sub_team["team_strength_ratio"].mean())

        # Update team_strength_ratio in the feature vector for inference
        if "team_strength_ratio" in feat_cols:
            ts_idx = feat_cols.index("team_strength_ratio")
            adjusted_features[ts_idx] = target_team_strength

    models_dir = resolve_path(cfg, "models")
    projections = {}
    ci_results = {}

    for target in TARGET_COLS:
        # Build target-specific feature vector matching train.py
        unsafe_keywords = []
        if "goals" in target:
            unsafe_keywords = ["goals", "xg", "npxg"]
        elif "assists" in target:
            unsafe_keywords = ["assists", "xag", "xa"]
        elif "xg" in target or "xag" in target:
            unsafe_keywords = ["goals", "assists", "xg", "xag", "npxg", "xa"]
        elif "prog_passes" in target:
            unsafe_keywords = ["prog_passes"]
        elif "key_passes" in target:
            unsafe_keywords = ["key_passes"]
        elif "prog_carries" in target:
            unsafe_keywords = ["prog_carries"]
        elif "tackles_won" in target:
            unsafe_keywords = ["tackles_won"]
        elif "interceptions" in target:
            unsafe_keywords = ["interceptions"]
        elif "clearances" in target:
            unsafe_keywords = ["clearances"]
            
        target_feat_cols = []
        target_features = []
        for i, c in enumerate(feat_cols):
            is_safe = True
            for kw in unsafe_keywords:
                if kw in c.lower():
                    is_safe = False
            if is_safe:
                target_feat_cols.append(c)
                target_features.append(adjusted_features[i])
                
        must_keep = ["source_lsc", "target_lsc", "team_strength_ratio", "age"]
        for c in must_keep:
            if c in feat_cols and c not in target_feat_cols:
                target_feat_cols.append(c)
                idx = feat_cols.index(c)
                target_features.append(adjusted_features[idx])
                
        target_features = np.array(target_features)

        # Primary: LightGBM
        lgbm = _load_model(models_dir, target, "lgbm")
        if lgbm:
            raw_pred = float(lgbm.predict(target_features.reshape(1, -1))[0])
            
            # --- TRANSFER REALITY CHECK (TRC) ---
            if target in ["goals_p90", "assists_p90", "xg_p90", "xag_p90"]:
                if target_lsc > source_lsc:
                    difficulty_delta = target_lsc - source_lsc
                    damping_factor = 1.0 - (difficulty_delta * 0.75)
                    if target_team:
                        if target_team_strength > 1.15:
                            damping_factor += min(0.10, (target_team_strength - 1.0) * 0.15)
                        elif target_team_strength < 0.90:
                            damping_factor -= min(0.12, (1.0 - target_team_strength) * 0.15)
                    else:
                        team_jump = float(player_row.get("team_strength_ratio", 1.0))
                        if team_jump > 1.2:
                            damping_factor += 0.05
                    damping_factor = max(0.5, min(1.3, damping_factor))
                    final_pred = raw_pred * damping_factor
                elif target_lsc < source_lsc:
                    ease_delta = source_lsc - target_lsc
                    boost_factor = 1.0 + (ease_delta * 0.15)
                    if target_team and target_team_strength > 1.15:
                        boost_factor += min(0.08, (target_team_strength - 1.0) * 0.10)
                    final_pred = raw_pred * boost_factor
                else:
                    if target_team and "team_strength_ratio" in player_row:
                        src_team_str = float(player_row["team_strength_ratio"])
                        if src_team_str > 0:
                            rel_change = (target_team_strength / src_team_str) - 1.0
                            final_pred = raw_pred * (1.0 + max(-0.25, min(0.25, rel_change * 0.12)))
                        else:
                            final_pred = raw_pred
                    else:
                        final_pred = raw_pred
            elif target in ["prog_passes_p90", "key_passes_p90", "prog_carries_p90"]:
                # High possession / high quality teams yield more progression opportunities
                if target_team and target_team_strength > 1.15:
                    final_pred = raw_pred * (1.0 + min(0.10, (target_team_strength - 1.0) * 0.12))
                else:
                    final_pred = raw_pred
            else:
                # Defensive metrics (tackles, interceptions, clearances)
                final_pred = raw_pred
                
            projections[target] = round(max(0.0, final_pred), 4)

        # CI: Bayesian Ridge
        bay_pipeline = _load_model(models_dir, target, "bayesian")
        if bay_pipeline:
            bay_model = bay_pipeline.named_steps["bay"]
            scaler = bay_pipeline.named_steps["scaler"]
            X_scaled = scaler.transform(target_features.reshape(1, -1))
            mean_pred, std_pred = bay_model.predict(X_scaled, return_std=True)
            
            # Apply same TRC damping to CI
            if target_lsc > source_lsc:
                ci_damping = 1.0 - ((target_lsc - source_lsc) * 0.75)
                if target_team and target_team_strength > 1.15:
                    ci_damping += min(0.10, (target_team_strength - 1.0) * 0.15)
                mean_pred[0] *= ci_damping
            
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

    # ── Role-Aware SHAP top-5 factors ─────────────────────────────────────────
    target_for_shap, shap_label, unsafe_kw_shap = _select_shap_target(player_row)
    
    target_feat_cols_shap = []
    target_features_shap = []
    for i, c in enumerate(feat_cols):
        is_safe = True
        for kw in unsafe_kw_shap:
            if kw in c.lower():
                is_safe = False
        if is_safe:
            target_feat_cols_shap.append(c)
            target_features_shap.append(adjusted_features[i])
            
    must_keep = ["source_lsc", "target_lsc", "team_strength_ratio", "age"]
    for c in must_keep:
        if c in feat_cols and c not in target_feat_cols_shap:
            target_feat_cols_shap.append(c)
            idx = feat_cols.index(c)
            target_features_shap.append(adjusted_features[idx])
    
    target_features_shap = np.array([target_features_shap])
    
    top_factors = explain_prediction(
        target_features_shap, target_for_shap, target_feat_cols_shap, models_dir, log
    )

    # ── Tactical Fit & Squad Upgrade Analysis ─────────────────────────────────
    tactical_fit = analyze_tactical_fit(
        player_row=player_row,
        projections=projections,
        target_team=target_team_canonical,
        target_league=target_league,
        df=df,
        target_team_strength=target_team_strength,
        adaptation_score=adaptation_score,
    )

    # ── Build result ──────────────────────────────────────────────────────────
    goals_ci = ci_results.get("goals_p90", {"low": None, "high": None})
    result = {
        "player":                   player_name,
        "position":                 player_row.get("position", player_row.get("position_primary", "MF")),
        "position_primary":         player_row.get("position_primary", "MF"),
        "source_league":            source_league,
        "target_league":            target_league,
        "target_team":              target_team_canonical,
        "target_team_strength_ratio": round(target_team_strength, 3) if target_team_canonical else None,
        "source_lsc":               source_lsc,
        "target_lsc":               target_lsc,
        # Attacking Projections
        "projected_goals_p90":      projections.get("goals_p90"),
        "projected_assists_p90":    projections.get("assists_p90"),
        "projected_xg_p90":         projections.get("xg_p90"),
        "projected_xag_p90":        projections.get("xag_p90"),
        # Progression Projections
        "projected_prog_passes_p90": projections.get("prog_passes_p90"),
        "projected_key_passes_p90":  projections.get("key_passes_p90"),
        "projected_prog_carries_p90":projections.get("prog_carries_p90"),
        # Defensive Projections
        "projected_tackles_won_p90": projections.get("tackles_won_p90"),
        "projected_interceptions_p90": projections.get("interceptions_p90"),
        "projected_clearances_p90":  projections.get("clearances_p90"),
        # Uncertainty
        "ci_low_goals":             goals_ci["low"],
        "ci_high_goals":            goals_ci["high"],
        "minutes_expectation":      minutes_expectation,
        "adaptation_score_pct":     adaptation_score,
        "risk_score_pct":           risk_score,
        # SHAP
        "shap_target":              target_for_shap,
        "shap_target_label":        shap_label,
        "top_5_factors":            top_factors,
        # Tactical Fit & Squad Upgrade
        "tactical_fit":             tactical_fit,
    }

    tgt_str = f" → {target_league}" + (f" ({target_team_canonical})" if target_team_canonical else "")
    log.info(f"Prediction complete for {player_name} ({source_league}{tgt_str})")
    return result


def main():
    parser = argparse.ArgumentParser(description="CLPTM — Player Transfer Prediction")
    parser.add_argument("--player",  type=str, required=True)
    parser.add_argument("--source",  type=str, required=True, help="Source league")
    parser.add_argument("--target",  type=str, required=True, help="Target league")
    parser.add_argument("--target-team", type=str, default=None, help="Target team (optional)")
    args = parser.parse_args()

    cfg = load_config()
    try:
        result = predict_player(args.player, args.source, args.target, target_team=args.target_team, cfg=cfg)
        from src.report import render_report
        print(render_report(result))
    except ValueError as err:
        print(f"\n❌ Transfer Prediction Error:\n   {err}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
