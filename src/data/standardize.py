"""
standardize.py — Phase 1, Step 2: Unified column schema & league filtering.

Takes the validated raw DataFrame from ingest.py and:
  - Renames columns to a consistent internal snake_case schema
  - Filters to configured leagues and min-minutes threshold
  - Tags each row with 'season' and 'league'
  - Saves interim/standardized.csv
"""

import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils import load_config, resolve_path, get_logger

# ── Mapping: FBRef column → internal schema ───────────────────────────────────
COLUMN_MAP = {
    "Player":   "player",
    "Squad":    "team",
    "Comp":     "league",
    "Pos":      "position",
    "Age":      "age",
    "Min":      "minutes",
    "Gls":      "goals",
    "Ast":      "assists",
    "xG":       "xg",
    "xAG":      "xag",
    "npxG":     "npxg",
    "Sh/90":    "shots_p90",
    "SoT/90":   "shots_on_target_p90",
    "PrgC":     "prog_carries",
    "PrgP":     "prog_passes",
    "PrgR":     "prog_receptions",
    "KP":       "key_passes",
    "xA":       "xa",
    "Cmp%":     "pass_completion_pct",
    "TklW":     "tackles_won",
    "Int":      "interceptions",
    "Clr":      "clearances",
    "Carries":  "carries",
    "Touches":  "touches",
}


def standardize(df: pd.DataFrame, cfg: dict | None = None) -> pd.DataFrame:
    """
    Standardize column names, filter leagues and minutes, tag rows.

    Parameters
    ----------
    df : pd.DataFrame
        Output of ingest().
    cfg : dict, optional
        Loaded config. Loaded from file if not provided.

    Returns
    -------
    pd.DataFrame
        Standardized DataFrame saved to data/interim/standardized.csv
    """
    if cfg is None:
        cfg = load_config()

    log = get_logger("standardize", cfg)
    log.info("=== Phase 1 — Standardize: START ===")

    # ── Rename columns ────────────────────────────────────────────────────────
    df = df.rename(columns=COLUMN_MAP)
    kept_cols = list(COLUMN_MAP.values())
    df = df[kept_cols].copy()
    log.info(f"Columns after renaming: {list(df.columns)}")

    # ── Filter to configured leagues ──────────────────────────────────────────
    leagues = cfg["leagues"]
    before = len(df)
    # FBRef Comp column looks like "eng Premier League" — match by substring
    df = df[df["league"].str.contains("|".join(leagues), case=False, na=False)].copy()
    log.info(f"League filter ({leagues}): {before} → {len(df)} rows")

    # ── Normalise league name to clean label ──────────────────────────────────
    for league in leagues:
        mask = df["league"].str.contains(league, case=False, na=False)
        df.loc[mask, "league"] = league
    log.info(f"League value counts:\n{df['league'].value_counts().to_string()}")

    # ── Filter by minimum minutes ─────────────────────────────────────────────
    min_min = cfg["min_minutes"]
    before = len(df)
    df = df[df["minutes"] >= min_min].copy()
    log.info(f"Minutes filter (>={min_min}): {before} → {len(df)} rows")

    # ── Parse age to numeric (FBRef sometimes shows "24-123" days format) ─────
    df["age"] = df["age"].astype(str).str.split("-").str[0]
    df["age"] = pd.to_numeric(df["age"], errors="coerce")

    # ── Reset index ───────────────────────────────────────────────────────────
    df = df.reset_index(drop=True)

    # ── Save ──────────────────────────────────────────────────────────────────
    out_path = resolve_path(cfg, "interim_data", "standardized.csv")
    df.to_csv(out_path, index=False)
    log.info(f"Saved standardized dataset: {out_path} — shape {df.shape}")
    log.info("=== Phase 1 — Standardize: DONE ===")

    return df


if __name__ == "__main__":
    from src.data.ingest import ingest
    cfg = load_config()
    raw = ingest(cfg)
    std = standardize(raw, cfg)
    print(std.head())
    print(std.dtypes)
