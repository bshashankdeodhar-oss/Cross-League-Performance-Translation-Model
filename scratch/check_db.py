import sqlite3
import pandas as pd

conn = sqlite3.connect("transferpred.db")
c = conn.cursor()
c.execute("SELECT sql FROM sqlite_master WHERE type='table'")
for row in c.fetchall():
    print(row[0])
    print("-" * 50)

print("TEAMS:")
df_teams = pd.read_sql("SELECT * FROM Team", conn)
print(f"Total teams: {len(df_teams)}")
print(df_teams.head(10))

print("\nPLAYERS:")
df_players = pd.read_sql("SELECT * FROM Player", conn)
print(f"Total players: {len(df_players)}")
print(df_players.columns.tolist())
print(df_players.head(5))
