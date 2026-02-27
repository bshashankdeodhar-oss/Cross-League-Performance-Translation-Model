import pandas as pd

df = pd.read_csv("combined_leagues.csv")

print("Total players:", df.shape[0])
print("\nPlayers per league:")
print(df["league"].value_counts())
