"""
engineer.py — Phase 2: Feature Engineering for the CLPTM.

Produces the final feature-rich dataset from the unified_dataset.csv.

Features created:
  1. LSC-adjusted per-90 metrics (inherited from Phase 1)
  2. Team strength ratio (player's team avg xG / league avg xG)
  3. Possession-adjusted touches
  4. Position one-hot encoding (GK, DF, MF, FW, multi-pos)
  5. Age curve score (peak 24-28, polynomial decay)
  6. Play style vector (dribble %, progressive pass %, aerial ratio proxy)

All transformations are logged to logs/feature_engineering.log.
Output: data/processed/feature_dataset.csv
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils import load_config, resolve_path, get_logger

# Standard positions
POSITIONS = ["GK", "DF", "MF", "FW"]


# ─────────────────────────────────────────────────────────────────────────────
# 1. Team Strength Ratio
# ─────────────────────────────────────────────────────────────────────────────
def _add_team_strength(df: pd.DataFrame, log) -> pd.DataFrame:
    """
    Team strength ratio = team's average xg_p90 / league's average xg_p90.
    Values >1 mean the player is in a stronger-than-average team.
    """
    if "xg_p90" not in df.columns:
        log.warning("xg_p90 not found — skipping team strength ratio.")
        return df

    # League average xg/90
    league_avg_xg = df.groupby("league")["xg_p90"].transform("mean")

    # Team average xg/90 — proxy for team quality
    team_avg_xg = df.groupby(["league", "team"])["xg_p90"].transform("mean")

    df.loc[:, "team_strength_ratio"] = team_avg_xg / (league_avg_xg + 1e-9)
    log.info("  team_strength_ratio computed.")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 2. Possession-Adjusted Touches
# ─────────────────────────────────────────────────────────────────────────────
def _add_possession_adjusted(df: pd.DataFrame, log) -> pd.DataFrame:
    """
    touches_p90 normalized by team's relative possession proxy.
    We use the team's avg passes_completed_pct as a possession surrogate
    since we don't have direct possession% in the dataset.
    """
    if "touches_p90" not in df.columns or "pass_completion_pct" not in df.columns:
        log.warning("touches_p90 or pass_completion_pct missing — skipping possession adjustment.")
        return df

    team_avg_pass_pct = df.groupby(["league", "team"])["pass_completion_pct"].transform("mean")
    league_avg_pass_pct = df.groupby("league")["pass_completion_pct"].transform("mean")

    possession_factor = team_avg_pass_pct / (league_avg_pass_pct + 1e-9)
    df.loc[:, "poss_adj_touches_p90"] = df["touches_p90"] / (possession_factor + 1e-9)
    log.info("  poss_adj_touches_p90 computed.")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 3. Position One-Hot Encoding
# ─────────────────────────────────────────────────────────────────────────────
def _add_position_encoding(df: pd.DataFrame, log) -> pd.DataFrame:
    """
    One-hot encode positions. FBRef uses comma-separated multi-position strings
    like "MF,FW". We set a 1 for every position tag a player has.
    """
    if "position" not in df.columns:
        log.warning("position column not found — skipping position encoding.")
        return df

    for pos in POSITIONS:
        col = f"pos_{pos.lower()}"
        df.loc[:, col] = df["position"].str.contains(pos, na=False).astype(int)
        log.info(f"  Position flag: {col}")

    # Position group: primary position for role-adjusted analysis
    def primary_pos(pos_str):
        if pd.isna(pos_str):
            return "Unknown"
        parts = str(pos_str).split(",")
        return parts[0].strip()

    df.loc[:, "position_primary"] = df["position"].apply(primary_pos)
    log.info("  position_primary computed.")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 4. Age Curve Score
# ─────────────────────────────────────────────────────────────────────────────
def _add_age_curve(df: pd.DataFrame, cfg: dict, log) -> pd.DataFrame:
    """
    Age curve score in [0, 1].
    Peak = 1.0 for ages between peak_start and peak_end.
    Polynomial decay before peak and after peak.
    """
    if "age" not in df.columns:
        log.warning("age column not found — skipping age curve.")
        return df

    peak_start = cfg["age_curve"]["peak_start"]
    peak_end = cfg["age_curve"]["peak_end"]
    min_age = cfg["age_curve"]["min_age"]
    max_age = cfg["age_curve"]["max_age"]

    def age_score(age):
        if pd.isna(age):
            return 0.5  # neutral for missing age
        age = float(age)
        if age < peak_start:
            # Rising curve: quadratic from 0 at min_age to 1 at peak_start
            progress = (age - min_age) / max(peak_start - min_age, 1)
            return float(np.clip(progress ** 1.5, 0, 1))
        elif age <= peak_end:
            return 1.0
        else:
            # Declining curve: quadratic from 1 at peak_end to 0 at max_age
            decline = (age - peak_end) / max(max_age - peak_end, 1)
            return float(np.clip(1 - decline ** 1.5, 0, 1))

    df.loc[:, "age_curve_score"] = df["age"].apply(age_score)
    log.info("  age_curve_score computed.")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 5. Play Style Vector
# ─────────────────────────────────────────────────────────────────────────────
def _add_play_style_vector(df: pd.DataFrame, log) -> pd.DataFrame:
    """
    Three play-style dimensions:
      - progressive_ratio : prog_passes_p90 / (touches_p90 + 1e-9)
      - direct_carry_ratio: prog_carries_p90 / (carries_p90 + 1e-9)
      - defensive_contribution: (tackles_won_p90 + interceptions_p90) / 2
    """
    if "prog_passes_p90" in df.columns and "touches_p90" in df.columns:
        df.loc[:, "play_style_progressive"] = (
            df["prog_passes_p90"] / (df["touches_p90"] + 1e-9)
        )
        log.info("  play_style_progressive computed.")

    if "prog_carries_p90" in df.columns and "carries_p90" in df.columns:
        df.loc[:, "play_style_direct_carry"] = (
            df["prog_carries_p90"] / (df["carries_p90"] + 1e-9)
        )
        log.info("  play_style_direct_carry computed.")

    if "tackles_won_p90" in df.columns and "interceptions_p90" in df.columns:
        df.loc[:, "play_style_defensive"] = (
            (df["tackles_won_p90"] + df["interceptions_p90"]) / 2
        )
        log.info("  play_style_defensive computed.")

    return df


# ─────────────────────────────────────────────────────────────────────────────
# 6. League percentile ranks (within-league)
# ─────────────────────────────────────────────────────────────────────────────
def _add_league_percentiles(df: pd.DataFrame, log) -> pd.DataFrame:
    """
    Compute within-league percentile rank for all _p90 columns.
    This is position-agnostic (overall percentile across all positions in league).
    """
    p90_cols = [c for c in df.columns if c.endswith("_p90") and not c.startswith("lsc_adj")]

    for col in p90_cols:
        pct_col = f"{col}_pct"
        df.loc[:, pct_col] = df.groupby("league")[col].rank(pct=True)
        log.info(f"  Percentile: {pct_col}")

    return df


# ─────────────────────────────────────────────────────────────────────────────
# Main engineer function
# ─────────────────────────────────────────────────────────────────────────────
def engineer(df: pd.DataFrame, cfg: dict | None = None) -> pd.DataFrame:
    """
    Run all feature engineering steps on the unified dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Output of league_strength.apply_lsc().
    cfg : dict
        Loaded config.

    Returns
    -------
    pd.DataFrame
        Feature-rich dataset saved to data/processed/feature_dataset.csv
    """
    if cfg is None:
        cfg = load_config()

    log = get_logger("feature_engineering", cfg)
    log.info("=== Phase 2 — Feature Engineering: START ===")
    log.info(f"Input shape: {df.shape}")

    df = df.copy()

    df = _add_team_strength(df, log)
    df = _add_possession_adjusted(df, log)
    df = _add_position_encoding(df, log)
    df = _add_age_curve(df, cfg, log)
    df = _add_play_style_vector(df, log)
    df = _add_league_percentiles(df, log)

    # ── Fill any remaining NaNs for numeric columns ───────────────────────────
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    null_counts = df[numeric_cols].isna().sum()
    null_cols = null_counts[null_counts > 0]
    if not null_cols.empty:
        log.warning(f"NaN counts before fill:\n{null_cols.to_string()}")
        df.loc[:, numeric_cols] = df[numeric_cols].fillna(0)
        log.info("Filled remaining NaNs with 0.")

    log.info(f"Final feature set — shape: {df.shape}")
    log.info(f"Columns: {list(df.columns)}")

    # ── Save ──────────────────────────────────────────────────────────────────
    out_path = resolve_path(cfg, "processed_data", "feature_dataset.csv")
    df.to_csv(out_path, index=False)
    log.info(f"Saved feature dataset: {out_path}")
    log.info("=== Phase 2 — Feature Engineering: DONE ===")

    return df


if __name__ == "__main__":
    from src.data.ingest import ingest
    from src.data.standardize import standardize
    from src.data.normalize import normalize
    from src.data.league_strength import apply_lsc
    cfg = load_config()
    df = engineer(
        apply_lsc(normalize(standardize(ingest(cfg), cfg), cfg), cfg),
        cfg
    )
    print(df.shape)
    print(df[["player", "league", "age_curve_score", "team_strength_ratio",
              "play_style_progressive", "pos_fw", "goals_p90"]].head(10))
