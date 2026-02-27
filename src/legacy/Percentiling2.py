import pandas as pd

df_2425 = pd.read_csv("clean_2425_top2.csv")

# Print count for debug
print(df_2425["Comp"].value_counts())

# Percentile computation
percentile_cols = [
    "Gls", "xG", "npxG", "Ast", "xAG",
    "Sh/90", "SoT/90",
    "PrgC", "PrgP", "PrgR",
    "Cmp%", "KP", "xA",
    "TklW", "Int", "Tkl+Int", "Clr",
    "Succ%", "Carries", "Touches"
]

for col in percentile_cols:
    df_2425[col + "_pct"] = df_2425.groupby("Comp")[col].rank(pct=True)

df_2425.to_csv("clean_2425_with_percentiles.csv", index=False)
