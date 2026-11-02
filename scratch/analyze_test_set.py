import pandas as pd
import sqlite3

test_df = pd.read_csv("data_T5/transfers_2026_2027_test_set.csv")
feat_df = pd.read_csv("data/processed/feature_dataset.csv")
raw_master = pd.read_csv("data/raw/big5_player_master_2018_2024.csv", low_memory=False)

conn = sqlite3.connect("transferpred.db")
db_players = pd.read_sql("SELECT player_name, league, team FROM Player", conn)
db_teams = pd.read_sql("SELECT team_name, league_id FROM Team", conn)
leagues = pd.read_sql("SELECT * FROM League", conn)

print(f"Test set shape: {test_df.shape}")
print(f"Test set unique players: {test_df['player'].nunique()}")
print(f"Test set moving_from teams: {test_df['moving_from'].nunique()}")
print(f"Test set moving_to teams: {test_df['moving_to'].nunique()}")

# Compare test set players against feature_dataset
test_players_clean = test_df['player'].str.strip()
feat_players = set(feat_df['player'].str.strip().str.lower())
db_players_set = set(db_players['player_name'].str.strip().str.lower())
raw_players_set = set(raw_master['player'].dropna().str.strip().str.lower())

missing_in_feat = [p for p in test_players_clean.unique() if p.lower() not in feat_players]
missing_in_db = [p for p in test_players_clean.unique() if p.lower() not in db_players_set]
in_raw_missing_feat = [p for p in missing_in_feat if p.lower() in raw_players_set]
not_in_raw = [p for p in missing_in_feat if p.lower() not in raw_players_set]

print(f"Missing in feature_dataset: {len(missing_in_feat)} / {test_df['player'].nunique()}")
print(f"Missing in DB: {len(missing_in_db)} / {test_df['player'].nunique()}")
print(f"  - Exists in raw master but dropped by min_minutes: {len(in_raw_missing_feat)}")
print(f"  - Not in raw master: {len(not_in_raw)}")
print(f"Sample in raw but dropped: {in_raw_missing_feat[:10]}")
if not_in_raw:
    print(f"Sample not in raw: {not_in_raw[:10]}")

# Check teams in test set vs DB
test_all_teams = set(test_df['moving_from'].dropna().unique()) | set(test_df['moving_to'].dropna().unique())
db_team_names = set(db_teams['team_name'].str.strip().str.lower())
missing_teams = [t for t in test_all_teams if t.strip().lower() not in db_team_names]
print(f"\nMissing teams in DB from test set: {len(missing_teams)} / {len(test_all_teams)}")
print("Missing teams:", missing_teams)
