import pandas as pd

# Load datasets
df_2324 = pd.read_csv("combined_with_percentiles.csv")
df_2425 = pd.read_csv("clean_2425_top2.csv")

# Filter Bundesliga 23/24
bund_2324 = df_2324[df_2324["league"] == "Bundesliga"]

# Filter PL 24/25
pl_2425 = df_2425[df_2425["Comp"].str.contains("Premier League")]

# Clean names
bund_2324["Player"] = bund_2324["Player"].str.strip()
pl_2425["Player"] = pl_2425["Player"].str.strip()

# Find intersection
transfers = set(bund_2324["Player"]).intersection(set(pl_2425["Player"]))

print("Transfer Count:", len(transfers))
print("=" * 50)

# Verify league transition
for player in transfers:
    print("Player:", player)

    print("23/24 League:")
    print(bund_2324[bund_2324["Player"] == player]["league"].unique())

    print("24/25 League:")
    print(pl_2425[pl_2425["Player"] == player]["Comp"].unique())

    print("-" * 50)
