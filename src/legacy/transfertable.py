import pandas as pd

# Load datasets
df_2324 = pd.read_csv("combined_with_percentiles.csv")
df_2425 = pd.read_csv("clean_2425_with_percentiles.csv")

# Filter leagues
bund_2324 = df_2324[df_2324["league"] == "Bundesliga"].copy()
pl_2425 = df_2425[df_2425["Comp"].str.contains("Premier League")].copy()

# Clean names
bund_2324["Player"] = bund_2324["Player"].str.strip()
pl_2425["Player"] = pl_2425["Player"].str.strip()

# Find transfers
transfers = set(bund_2324["Player"]).intersection(set(pl_2425["Player"]))

transfer_rows = []

for player in transfers:
    bl_row = bund_2324[bund_2324["Player"] == player]
    pl_row = pl_2425[pl_2425["Player"] == player]

    if len(bl_row) == 1 and len(pl_row) == 1:
        bl_row = bl_row.iloc[0]
        pl_row = pl_row.iloc[0]

        row = {
            "Player": player
        }

        # Loop through percentile features
        for col in bund_2324.columns:
            if col.endswith("_percentile"):
        
            bl_value = bl_row[col]

            base_col = col.replace("_percentile", "")
            pl_col = base_col + "_pct"

            if pl_col in pl_row.index:
                pl_value = pl_row[pl_col]
                row[base_col + "_delta"] = pl_value - bl_value


        transfer_rows.append(row)

transfer_df = pd.DataFrame(transfer_rows)

transfer_df.to_csv("transfer_delta_table.csv", index=False)

print(transfer_df)
