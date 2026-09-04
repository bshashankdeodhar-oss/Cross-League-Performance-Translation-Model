"""
scrape_t5_data.py — Downloads, extracts, and merges comprehensive multi-season
FBRef Big 5 European Leagues data (Premier League, La Liga, Serie A, Bundesliga, Ligue 1)
into data_T5/.

Generates:
  1. Individual domain tables (standard, shooting, passing, possession, defense, playing_time)
  2. big5_player_master_2018_2024.csv: unified master dataset matching the CLPTM schema
  3. cross_league_transfers_2018_2024.csv: ground-truth cross-league transfer pairs
"""

import os
import sys
import urllib.request
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import pyreadr
except ImportError:
    raise ImportError("pyreadr is required. Install via `pip install pyreadr`")

DATA_T5_DIR = PROJECT_ROOT / "data_T5"
INDIVIDUAL_DIR = DATA_T5_DIR / "individual_tables"
RAW_RDS_DIR = DATA_T5_DIR / "raw_rds"

DATA_T5_DIR.mkdir(exist_ok=True)
INDIVIDUAL_DIR.mkdir(exist_ok=True)
RAW_RDS_DIR.mkdir(exist_ok=True)

BASE_RELEASE_URL = "https://github.com/JaseZiv/worldfootballR_data/releases/download/fb_big5_advanced_season_stats"

TABLES = [
    "big5_player_standard",
    "big5_player_shooting",
    "big5_player_passing",
    "big5_player_possession",
    "big5_player_defense",
    "big5_player_playing_time",
    "big5_team_standard",
]


def download_and_load_table(table_name: str) -> pd.DataFrame:
    """Download RDS file if not present and return as pandas DataFrame."""
    rds_file = RAW_RDS_DIR / f"{table_name}.rds"
    if not rds_file.exists():
        url = f"{BASE_RELEASE_URL}/{table_name}.rds"
        print(f"  Downloading {table_name}.rds from GitHub releases...")
        urllib.request.urlretrieve(url, rds_file)
        print(f"  ✓ Downloaded {table_name}.rds ({os.path.getsize(rds_file):,} bytes)")
    else:
        print(f"  Found cached {table_name}.rds ({os.path.getsize(rds_file):,} bytes)")

    print(f"  Reading {table_name}.rds via pyreadr...")
    df = pyreadr.read_r(str(rds_file))[None]
    return df


def save_individual_csvs(dataframes: dict[str, pd.DataFrame]):
    """Export individual tables as CSVs in data_T5/individual_tables/."""
    print("\n--- Exporting Individual CSV Tables ---")
    for name, df in dataframes.items():
        csv_path = INDIVIDUAL_DIR / f"{name}.csv"
        df.to_csv(csv_path, index=False)
        print(f"  ✓ Saved {csv_path.name}: {df.shape[0]:,} rows × {df.shape[1]} cols")


def build_unified_master(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Merge standard, shooting, passing, possession, and defense tables into a unified
    multi-season dataset matching the CLPTM snake_case schema.
    Focus on modern tracking era (Season_End_Year >= 2018).
    """
    print("\n--- Building Unified Multi-Season Player Master Dataset ---")
    std = dfs["big5_player_standard"].copy()
    shoot = dfs["big5_player_shooting"].copy()
    pass_ = dfs["big5_player_passing"].copy()
    poss = dfs["big5_player_possession"].copy()
    def_ = dfs["big5_player_defense"].copy()

    # Filter to seasons with complete tracking (2018 onwards)
    std = std[std["Season_End_Year"] >= 2018].copy()
    shoot = shoot[shoot["Season_End_Year"] >= 2018].copy()
    pass_ = pass_[pass_["Season_End_Year"] >= 2018].copy()
    poss = poss[poss["Season_End_Year"] >= 2018].copy()
    def_ = def_[def_["Season_End_Year"] >= 2018].copy()

    # Define primary merge keys
    keys = ["Season_End_Year", "Squad", "Comp", "Url"]

    # Iteratively merge new columns without duplicate name collisions
    merged = std.copy()
    for extra_name, extra_df in [
        ("shooting", shoot),
        ("passing", pass_),
        ("possession", poss),
        ("defense", def_),
    ]:
        print(f"  Merging + {extra_name}...")
        new_cols = keys + [c for c in extra_df.columns if c not in merged.columns and c not in keys]
        sub_df = extra_df[new_cols].drop_duplicates(subset=keys)
        merged = pd.merge(merged, sub_df, on=keys, how="left")

    # Map FBRef / worldfootballR columns to standard CLPTM snake_case columns
    col_map = {
        "Player": "player",
        "Squad": "team",
        "Comp": "league",
        "Pos": "position",
        "Age": "age",
        "Min_Playing": "minutes",
        "Gls": "goals",
        "Ast": "assists",
        "xG_Expected": "xg",
        "xAG_Expected": "xag",
        "npxG_Expected": "npxg",
        "Sh_per90_Standard": "shots_p90",
        "SoT_per90_Standard": "shots_on_target_p90",
        "PrgC_Carries": "prog_carries",
        "PrgP": "prog_passes",
        "PrgR_Receiving": "prog_receptions",
        "KP": "key_passes",
        "xA": "xa",
        "Cmp_percent_Total": "pass_completion_pct",
        "TklW_Tackles": "tackles_won",
        "Int": "interceptions",
        "Clr": "clearances",
        "Carries_Carries": "carries",
        "Touches_Touches": "touches",
    }

    # Add normalized season tag, e.g., 2024 -> "2023-2024"
    merged["season"] = merged["Season_End_Year"].apply(lambda y: f"{int(y)-1}-{int(y)}")

    # Handle age format
    if "Age" in merged.columns:
        merged["age"] = merged["Age"].astype(str).str.split("-").str[0]
        merged["age"] = pd.to_numeric(merged["age"], errors="coerce")

    # Clean league names: strip prefix if any (e.g. "eng Premier League" -> "Premier League")
    merged["league"] = (
        merged["Comp"]
        .astype(str)
        .str.replace(r"^[a-z]{2,3}\s+", "", regex=True)
        .str.strip()
    )

    # Standardize columns
    standard_df = pd.DataFrame()
    for raw_c, std_c in col_map.items():
        if raw_c in merged.columns:
            standard_df[std_c] = merged[raw_c]
        elif std_c in merged.columns:
            standard_df[std_c] = merged[std_c]
        else:
            standard_df[std_c] = np.nan

    standard_df["season"] = merged["season"]
    standard_df["season_end_year"] = merged["Season_End_Year"]
    standard_df["player_url"] = merged["Url"]
    standard_df["nation"] = merged.get("Nation", "")

    # Compute per-90 metrics where missing
    safe_90s = (pd.to_numeric(standard_df["minutes"], errors="coerce") / 90.0).replace(0, np.nan)
    for stat in ["goals", "assists", "xg", "xag", "npxg", "prog_carries", "prog_passes", "prog_receptions", "key_passes", "tackles_won", "interceptions", "clearances", "carries", "touches"]:
        p90_col = f"{stat}_p90"
        if stat in standard_df.columns:
            standard_df[p90_col] = pd.to_numeric(standard_df[stat], errors="coerce") / safe_90s

    master_path = DATA_T5_DIR / "big5_player_master_2018_2024.csv"
    standard_df.to_csv(master_path, index=False)
    print(f"\n  ✓ Saved master dataset: {master_path.name}")
    print(f"    Shape: {standard_df.shape[0]:,} player-seasons × {standard_df.shape[1]} features")
    print(f"    Seasons: {sorted(standard_df['season'].unique())}")
    print(f"    Leagues: {list(standard_df['league'].value_counts().to_dict().items())}")

    return standard_df


def extract_cross_league_transfers(master_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract longitudinal player transfers across consecutive seasons.
    Identifies player i playing in League A in season T and League B in season T+1.
    """
    print("\n--- Extracting Cross-League Transfer Pairs (T -> T+1) ---")
    
    # Filter players with at least 450 minutes in both seasons
    active = master_df[pd.to_numeric(master_df["minutes"], errors="coerce") >= 450].copy()
    
    # Deduplicate in case of mid-season stints: keep the stint with most minutes
    active = (
        active.sort_values("minutes", ascending=False)
        .drop_duplicates(subset=["player_url", "season_end_year"], keep="first")
        .sort_values(["player_url", "season_end_year"])
    )

    seasons = sorted(active["season_end_year"].unique())
    transfer_records = []

    core_stats = ["goals_p90", "assists_p90", "xg_p90", "xag_p90", "prog_passes_p90", "prog_carries_p90", "touches_p90"]

    for i in range(len(seasons) - 1):
        s_from = seasons[i]
        s_to = seasons[i+1]

        df_from = active[active["season_end_year"] == s_from].copy()
        df_to = active[active["season_end_year"] == s_to].copy()

        # Match on player_url (or player name if url is empty)
        merged = pd.merge(df_from, df_to, on="player_url", suffixes=("_src", "_tgt"))

        # Cross-league transfer condition
        cross = merged[merged["league_src"] != merged["league_tgt"]].copy()

        for _, row in cross.iterrows():
            rec = {
                "player": row["player_src"],
                "player_url": row["player_url"],
                "season_src": row["season_src"],
                "season_tgt": row["season_tgt"],
                "league_src": row["league_src"],
                "league_tgt": row["league_tgt"],
                "team_src": row["team_src"],
                "team_tgt": row["team_tgt"],
                "age_src": row["age_src"],
                "age_tgt": row["age_tgt"],
                "position": row["position_src"],
                "minutes_src": row["minutes_src"],
                "minutes_tgt": row["minutes_tgt"],
            }
            # Record stat changes
            for s in core_stats:
                src_val = row.get(f"{s}_src", np.nan)
                tgt_val = row.get(f"{s}_tgt", np.nan)
                rec[f"{s}_src"] = src_val
                rec[f"{s}_tgt"] = tgt_val
                rec[f"{s}_delta"] = tgt_val - src_val if pd.notna(tgt_val) and pd.notna(src_val) else np.nan

            transfer_records.append(rec)

    transfers_df = pd.DataFrame(transfer_records)
    transfers_path = DATA_T5_DIR / "cross_league_transfers_2018_2024.csv"
    transfers_df.to_csv(transfers_path, index=False)

    print(f"  ✓ Extracted {len(transfers_df):,} cross-league transfer pairs!")
    print(f"  ✓ Saved to: {transfers_path.name}")
    print("\n  Top Cross-League Transfer Pathways:")
    pathway_counts = (
        transfers_df["league_src"] + " -> " + transfers_df["league_tgt"]
    ).value_counts().head(10)
    for pathway, count in pathway_counts.items():
        print(f"    {pathway}: {count} transfers")

    return transfers_df


def main():
    print("=" * 70)
    print("CLPTM DATA INGESTION ENGINE — TOP 5 EUROPEAN LEAGUES (2018–2024)")
    print("=" * 70)

    loaded_dfs = {}
    for table in TABLES:
        print(f"\nProcessing {table}...")
        df = download_and_load_table(table)
        loaded_dfs[table] = df
        print(f"  Loaded shape: {df.shape[0]:,} rows × {df.shape[1]} cols")

    # 1. Export individual CSVs
    save_individual_csvs(loaded_dfs)

    # 2. Build unified multi-season player master dataset
    master_df = build_unified_master(loaded_dfs)

    # 3. Extract real cross-league transfers
    transfers_df = extract_cross_league_transfers(master_df)

    print("\n" + "=" * 70)
    print("ALL DATA DOWNLOADED & PROCESSED SUCCESSFULLY INTO `data_T5/`")
    print(f"1. Individual tables: {INDIVIDUAL_DIR}")
    print(f"2. Master Multi-Season CSV: {DATA_T5_DIR / 'big5_player_master_2018_2024.csv'}")
    print(f"3. Real Cross-League Transfers CSV: {DATA_T5_DIR / 'cross_league_transfers_2018_2024.csv'} ({len(transfers_df)} transfer pairs)")
    print("=" * 70)


if __name__ == "__main__":
    main()
