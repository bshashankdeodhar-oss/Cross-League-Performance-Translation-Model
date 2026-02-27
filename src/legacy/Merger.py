import pandas as pd
import os

def merge_league(folder_path, league_name):
    
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
    
    # Base file
    df = pd.read_csv(os.path.join(folder_path, files[0]))
    df = df[["Player", "Team", "Minutes", "Goals per 90"]]
    df = df.rename(columns={"Goals per 90": "goals_per_90"})
    
    # Merge rest
    for file in files[1:]:
        temp = pd.read_csv(os.path.join(folder_path, file))
        
        stat_column = temp.columns[3]
        temp = temp[["Player", "Team", stat_column]]
        
        new_name = file.replace(".csv", "")
        temp = temp.rename(columns={stat_column: new_name})
        
        df = df.merge(temp, on=["Player", "Team"], how="left")
    
    # Filter
    df = df[df["Minutes"] > 600]
    
    # Fill missing
    df = df.fillna(0)
    
    # Add league label
    df["league"] = league_name
    
    return df


bundesliga_df = merge_league("Bundesliga_PlayerStats", "Bundesliga")
prem_df = merge_league("Prem_PlayerStats", "Premier League")

final_df = pd.concat([bundesliga_df, prem_df])

print(final_df.head())
print(final_df.shape)

final_df.to_csv("combined_leagues.csv", index=False)
