import pandas as pd

# Load 23/24 Bundesliga percentiles
df_2324 = pd.read_csv("combined_with_percentiles.csv")
bund_2324 = df_2324[df_2324["league"] == "Bundesliga"]

# Load 24/25 cleaned data
df_2425 = pd.read_csv("clean_2425_top2.csv")

# Keep only PL 24/25
pl_2425 = df_2425[df_2425["Comp"].str.contains("Premier League")]

# Clean player names
bund_2324["Player"] = bund_2324["Player"].str.strip()
pl_2425["Player"] = pl_2425["Player"].str.strip()

# Find intersection
transfers = set(bund_2324["Player"]).intersection(set(pl_2425["Player"]))

print("Transferred Players:")
print(transfers)
print("Count:", len(transfers))
