import pandas as pd
import os

folder_path = "Bundesliga_PlayerStats"

# Files we will use for now
files = [
    "player_goals_per_90.csv",
    "player_expected_goals_per_90.csv",
    "player_expected_assists_per_90.csv",
    "player_accurate_passes.csv",
    "player_accurate_long_balls.csv",
    "player_tackles_won.csv",
    "player_interceptions.csv",
    "player_effective_clearances.csv",
    "player_contests_won.csv",
    "player_big_chances_created.csv"
]

# Load first file as base
df = pd.read_csv(os.path.join(folder_path, files[0]))

# Keep only relevant columns
df = df[["Player", "Team", "Minutes", "Goals per 90"]]

# Rename stat column
df = df.rename(columns={"Goals per 90": "goals_per_90"})

print(df.head())



for file in files[1:]:
    temp = pd.read_csv(os.path.join(folder_path, file))
    
    # Identify the stat column (usually 4th column)
    stat_column = temp.columns[3]
    
    # Keep only relevant columns
    temp = temp[["Player", "Team", stat_column]]
    
    # Rename stat column to file name
    new_name = file.replace(".csv", "")
    temp = temp.rename(columns={stat_column: new_name})
    
    # Merge
    df = df.merge(temp, on=["Player", "Team"], how="left")

print(df.head())
print(df.shape)

df = df[df["Minutes"] > 600]
df = df.fillna(0)

df.to_csv("bundesliga_merged.csv", index=False)
