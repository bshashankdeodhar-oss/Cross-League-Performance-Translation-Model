import sys
from pathlib import Path
sys.path.insert(0, ".")
import pandas as pd
import numpy as np
from src.utils import load_config
from src.data.ingest import ingest
from src.data.standardize import standardize, COLUMN_MAP
from src.data.normalize import normalize
from src.data.league_strength import apply_lsc
from src.features.engineer import engineer

cfg = load_config()
test_df = pd.read_csv("data_T5/transfers_2026_2027_test_set.csv")
test_players = set(test_df["player"].dropna().str.strip().str.lower())

df_raw = ingest(cfg)

# Custom standardization that preserves test set players
df = df_raw.rename(columns=COLUMN_MAP)
kept_cols = list(COLUMN_MAP.values())
df = df[kept_cols].copy()

leagues = cfg["leagues"]
df = df[df["league"].str.contains("|".join(leagues), case=False, na=False)].copy()
for league in leagues:
    mask = df["league"].str.contains(league, case=False, na=False)
    df.loc[mask, "league"] = league

min_min = cfg["min_minutes"]
is_test_player = df["player"].astype(str).str.strip().str.lower().isin(test_players)
df = df[(df["minutes"] >= min_min) | (is_test_player & (df["minutes"] > 0))].copy()

df["age"] = df["age"].astype(str).str.split("-").str[0]
df["age"] = pd.to_numeric(df["age"], errors="coerce")
df = df.reset_index(drop=True)

print(f"Standardized shape with test set included: {df.shape}")
yd_std = df[df["player"].str.contains("Yan Diomand", case=False, na=False)]
print("Yan Diomande in standardized:\n", yd_std[["player", "team", "league", "minutes", "goals", "xg"]])

# Now normalize
df_norm = normalize(df, cfg)
print("Normalized shape:", df_norm.shape)

# Now apply LSC
df_lsc = apply_lsc(df_norm, cfg)
print("LSC shape:", df_lsc.shape)

# Now engineer
df_eng = engineer(df_lsc, cfg)
print("Engineered shape:", df_eng.shape)
yd_eng = df_eng[df_eng["player"].str.contains("Yan Diomand", case=False, na=False)]
print("Yan Diomande in engineered:\n", yd_eng[["player", "team", "league", "minutes", "goals_p90", "xg_p90", "age_curve_score", "team_strength_ratio"]])

# Check how many test set players are now in engineered:
eng_players = set(df_eng["player"].dropna().str.strip().str.lower())
missing = [p for p in test_players if p not in eng_players]
print(f"Missing test players after pipeline: {len(missing)} / {len(test_players)}")
if missing:
    print("Sample missing:", missing[:5])
