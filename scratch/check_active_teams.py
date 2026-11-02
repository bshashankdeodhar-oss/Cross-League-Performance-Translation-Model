import pandas as pd
import sqlite3

master = pd.read_csv("data/raw/big5_player_master_2018_2024.csv", low_memory=False)
print("Seasons in master:", master["season"].value_counts())

recent_teams = master[master["season"].isin(["2024-2025", "2025-2026"])].groupby(["league", "team"]).size().reset_index()
print("\nRecent teams count by league:")
print(recent_teams["league"].value_counts())

conn = sqlite3.connect("transferpred.db")
db_teams = pd.read_sql("SELECT t.team_name, l.league_name FROM Team t JOIN League l ON t.league_id = l.league_id", conn)
print(f"\nTotal teams currently in DB: {len(db_teams)}")

for lg in ["Premier League", "Bundesliga", "La Liga", "Serie A", "Ligue 1"]:
    rec_lg = set(recent_teams[recent_teams["league"] == lg]["team"])
    db_lg = set(db_teams[db_teams["league_name"] == lg]["team_name"])
    missing_in_db = rec_lg - db_lg
    print(f"\n--- {lg} ---")
    print(f"Active in 2024-2026: {len(rec_lg)} teams")
    print(f"Missing from DB: {missing_in_db}")
