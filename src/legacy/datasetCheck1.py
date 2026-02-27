import pandas as pd
import os
folder_path = "Bundesliga_PlayerStats"
df = pd.read_csv(os.path.join(folder_path, "player_goals_per_90.csv"))
print(df.head())
