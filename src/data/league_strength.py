"""
league_strength.py — Phase 1, Step 4: League Strength Coefficient (LSC) adjustment.

Applies the LSC from config to translate performance metrics from a source league
to a target league scale. Also produces the unified processed dataset.

Translation formula:
  projected_stat = source_stat * (source_LSC / target_LSC)

Interpretation: A player scoring 0.5 goals/90 in Bundesliga (LSC=0.92) is
projected to score 0.5 * (0.92/1.00) = 0.46 goals/90 in the Premier League.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils import load_config, resolve_path, get_logger

# Stats to apply LSC adjustment to
LSC_APPLY_COLS = [
    "goals_p90", "assists_p90", "xg_p90", "xag_p90", "npxg_p90",
    "shots_p90", "shots_on_target_p90",
    "prog_carries_p90", "prog_passes_p90", "prog_receptions_p90",
    "key_passes_p90", "xa_p90", "carries_p90", "touches_p90",
]

# Defensive stats — LSC adjustment is inverted (harder league = more impressive)
LSC_INVERTED_COLS = [
    "tackles_won_p90", "interceptions_p90", "clearances_p90",
]


def apply_lsc(df: pd.DataFrame, cfg: dict | None = None) -> pd.DataFrame:
    """
    Add LSC-adjusted stat columns to the DataFrame.
    These represent what a player's stats would look like if translated
    to the Premier League (reference league, LSC=1.0).

    Parameters
    ----------
    df : pd.DataFrame
        Output of normalize().
    cfg : dict
        Loaded config.

    Returns
    -------
    pd.DataFrame
        DataFrame with lsc_adj_* columns added and saved to data/processed/unified_dataset.csv
    """
    if cfg is None:
        cfg = load_config()

    log = get_logger("league_strength", cfg)
    log.info("=== Phase 1 — League Strength Coefficient: START ===")

    lsc_map: dict = cfg["league_strength"]
    log.info(f"LSC map: {lsc_map}")

    df = df.copy()

    # ── Add source LSC column ─────────────────────────────────────────────────
    df.loc[:, "league_lsc"] = df["league"].map(lsc_map)
    unmapped = df["league_lsc"].isna().sum()
    if unmapped > 0:
        log.warning(f"{unmapped} rows have leagues not in LSC map — they will be dropped.")
        df = df[df["league_lsc"].notna()].copy()

    ref_lsc = lsc_map.get("Premier League", 1.0)
    log.info(f"Reference LSC (Premier League): {ref_lsc}")

    # ── Apply LSC adjustment for offensive stats ──────────────────────────────
    for col in LSC_APPLY_COLS:
        if col not in df.columns:
            continue
        adj_col = f"lsc_adj_{col}"
        # Translate to reference league
        df.loc[:, adj_col] = df[col] * (df["league_lsc"] / ref_lsc)
        log.info(f"  {col} → {adj_col}")

    # ── Apply inverted LSC for defensive stats ────────────────────────────────
    for col in LSC_INVERTED_COLS:
        if col not in df.columns:
            continue
        adj_col = f"lsc_adj_{col}"
        # In a harder league, fewer defensive actions is still impressive
        df.loc[:, adj_col] = df[col] * (ref_lsc / df["league_lsc"])
        log.info(f"  {col} → {adj_col} (inverted LSC)")

    log.info(f"DataFrame shape after LSC adjustment: {df.shape}")

    # ── Save as the unified processed dataset ─────────────────────────────────
    out_path = resolve_path(cfg, "processed_data", "unified_dataset.csv")
    df.to_csv(out_path, index=False)
    log.info(f"Saved unified dataset: {out_path}")
    log.info("=== Phase 1 — League Strength Coefficient: DONE ===")

    return df


if __name__ == "__main__":
    from src.data.ingest import ingest
    from src.data.standardize import standardize
    from src.data.normalize import normalize
    cfg = load_config()
    df = apply_lsc(normalize(standardize(ingest(cfg), cfg), cfg), cfg)
    lsc_cols = [c for c in df.columns if c.startswith("lsc_adj_")]
    print(df[["player", "league", "league_lsc"] + lsc_cols[:4]].head(10))
    print(f"Shape: {df.shape}")
