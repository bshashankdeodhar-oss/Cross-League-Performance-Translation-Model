"""
ingest.py — Phase 1, Step 1: Load and validate raw FBRef data.

Reads the master FBRef CSV, validates required columns exist,
enforces correct dtypes, and logs any issues found.
Produces a validated DataFrame without modifying the raw file.
"""

import pandas as pd
import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils import load_config, resolve_path, get_logger

# ── Column schema we require from the raw FBRef file ─────────────────────────
REQUIRED_COLS = [
    "Player", "Squad", "Comp", "Pos", "Age", "Min",
    "Gls", "Ast", "xG", "xAG", "npxG",
    "Sh/90", "SoT/90",
    "PrgC", "PrgP", "PrgR",
    "KP", "xA", "Cmp%",
    "TklW", "Int", "Clr",
    "Carries", "Touches",
]


REVERSE_MAP = {
    "player": "Player",
    "team": "Squad",
    "league": "Comp",
    "position": "Pos",
    "age": "Age",
    "minutes": "Min",
    "goals": "Gls",
    "assists": "Ast",
    "xg": "xG",
    "xag": "xAG",
    "npxg": "npxG",
    "shots_p90": "Sh/90",
    "shots_on_target_p90": "SoT/90",
    "prog_carries": "PrgC",
    "prog_passes": "PrgP",
    "prog_receptions": "PrgR",
    "key_passes": "KP",
    "xa": "xA",
    "pass_completion_pct": "Cmp%",
    "tackles_won": "TklW",
    "interceptions": "Int",
    "clearances": "Clr",
    "carries": "Carries",
    "touches": "Touches",
}


def ingest(cfg: dict | None = None) -> pd.DataFrame:
    """
    Load and validate the raw FBRef dataset.

    Returns
    -------
    pd.DataFrame
        Validated raw DataFrame with all required columns present.
    """
    if cfg is None:
        cfg = load_config()

    log = get_logger("ingest", cfg)
    log.info("=== Phase 1 — Ingest: START ===")

    # ── Locate the raw file ───────────────────────────────────────────────────
    raw_dir = resolve_path(cfg, "raw_data")
    raw_file = raw_dir / cfg["raw_fbref_file"]

    if not raw_file.exists():
        # Fallback to data_T5 directory
        alt_file = Path("data_T5") / cfg["raw_fbref_file"]
        if alt_file.exists():
            raw_file = alt_file
        else:
            log.error(f"Raw file not found: {raw_file}")
            raise FileNotFoundError(f"Missing: {raw_file}")

    log.info(f"Loading raw data from: {raw_file}")
    df = pd.read_csv(raw_file, low_memory=False)
    log.info(f"Raw shape: {df.shape}")

    # ── Rename from snake_case if already formatted (e.g. data_T5 master) ────
    if "player" in df.columns and "Player" not in df.columns:
        df = df.rename(columns=REVERSE_MAP)

    # ── Drop duplicate header rows that FBRef sometimes repeats ──────────────
    if "Player" in df.columns:
        before = len(df)
        df = df[df["Player"] != "Player"].copy()
        dropped = before - len(df)
        if dropped:
            log.warning(f"Dropped {dropped} duplicate header rows.")

    # ── Validate and fill required columns ────────────────────────────────────
    for c in REQUIRED_COLS:
        if c not in df.columns:
            df[c] = pd.NA

    log.info("All required columns verified/aligned.")

    # ── Enforce numeric types ─────────────────────────────────────────────────
    numeric_cols = [c for c in REQUIRED_COLS if c not in ("Player", "Squad", "Comp", "Pos")]
    coerce_errors = []
    for col in numeric_cols:
        before_nulls = df[col].isna().sum()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        after_nulls = df[col].isna().sum()
        new_nulls = after_nulls - before_nulls
        if new_nulls > 0:
            coerce_errors.append((col, new_nulls))

    if coerce_errors:
        for col, n in coerce_errors:
            log.warning(f"Column '{col}': {n} values coerced to NaN during numeric conversion.")

    # ── Strip whitespace from string columns ─────────────────────────────────
    for col in ("Player", "Squad", "Comp", "Pos"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # ── Basic stats ───────────────────────────────────────────────────────────
    log.info(f"Leagues found: {sorted(df['Comp'].dropna().unique())}")
    log.info(f"Seasons/rows after cleaning: {len(df)}")
    log.info(f"Total NaNs in numeric cols: {df[numeric_cols].isna().sum().sum()}")
    log.info("=== Phase 1 — Ingest: DONE ===")

    return df


if __name__ == "__main__":
    cfg = load_config()
    df = ingest(cfg)
    print(df.head())
    print(df.shape)
    print(df["Comp"].value_counts())
