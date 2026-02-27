"""
normalize.py — Phase 1, Step 3: Per-90 normalization and league baseline adjustment.

Takes the standardized DataFrame and:
  - Computes per-90 versions of all counting stats
  - Computes each stat's z-score relative to the league average
  - Saves interim/normalized.csv
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils import load_config, resolve_path, get_logger

# Counting stats to normalize to per-90
COUNTING_STATS = [
    "goals", "assists", "xg", "xag", "npxg",
    "prog_carries", "prog_passes", "prog_receptions",
    "key_passes", "xa", "tackles_won", "interceptions",
    "clearances", "carries", "touches",
]

# Stats that are already per-90 or percentages — do NOT divide again
ALREADY_PER90 = ["shots_p90", "shots_on_target_p90", "pass_completion_pct"]


def normalize(df: pd.DataFrame, cfg: dict | None = None) -> pd.DataFrame:
    """
    Normalize counting stats to per-90 and compute league z-scores.

    Parameters
    ----------
    df : pd.DataFrame
        Output of standardize().
    cfg : dict, optional
        Loaded config.

    Returns
    -------
    pd.DataFrame
        DataFrame with *_p90 and *_zscore columns added.
    """
    if cfg is None:
        cfg = load_config()

    log = get_logger("normalize", cfg)
    log.info("=== Phase 1 — Normalize: START ===")

    df = df.copy()

    # ── Guard: minutes must be > 0 ────────────────────────────────────────────
    df = df[df["minutes"] > 0].copy()

    # ── Per-90 normalization ──────────────────────────────────────────────────
    log.info("Computing per-90 metrics...")
    for stat in COUNTING_STATS:
        if stat not in df.columns:
            log.warning(f"Column '{stat}' not found — skipping per-90.")
            continue
        col_name = f"{stat}_p90"
        df.loc[:, col_name] = (df[stat] / df["minutes"]) * 90
        log.info(f"  {stat} → {col_name}")

    # Keep the already-per-90 columns as-is
    for stat in ALREADY_PER90:
        if stat in df.columns:
            df.loc[:, stat] = df[stat]  # already correct

    # ── League-level z-score normalization ────────────────────────────────────
    log.info("Computing league z-scores...")
    p90_cols = [f"{s}_p90" for s in COUNTING_STATS if f"{s}_p90" in df.columns]
    all_norm_cols = p90_cols + ALREADY_PER90

    for col in all_norm_cols:
        if col not in df.columns:
            continue
        z_col = col.replace("_p90", "_zscore").replace("_pct", "_zscore")
        if z_col == col:
            z_col = col + "_zscore"

        # Compute z-score within each league independently
        df.loc[:, z_col] = df.groupby("league")[col].transform(
            lambda x: (x - x.mean()) / (x.std() + 1e-9)
        )
        log.info(f"  {col} → {z_col}")

    log.info(f"Shape after normalization: {df.shape}")

    # ── Save ──────────────────────────────────────────────────────────────────
    out_path = resolve_path(cfg, "interim_data", "normalized.csv")
    df.to_csv(out_path, index=False)
    log.info(f"Saved: {out_path}")
    log.info("=== Phase 1 — Normalize: DONE ===")

    return df


if __name__ == "__main__":
    from src.data.ingest import ingest
    from src.data.standardize import standardize
    cfg = load_config()
    df = normalize(standardize(ingest(cfg), cfg), cfg)
    p90_cols = [c for c in df.columns if c.endswith("_p90")]
    print(df[["player", "league", "minutes"] + p90_cols[:5]].head(10))
