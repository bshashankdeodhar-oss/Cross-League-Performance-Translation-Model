import pandas as pd

df = pd.read_csv("players_data-2024_2025.csv")

# Filter leagues
df = df[df["Comp"].str.contains("Premier League|Bundesliga")]

# Filter minutes
df = df[df["Min"] > 600]

# Select useful columns
features = [
    "Player", "Squad", "Comp", "Pos", "Min",
    "Gls", "xG", "npxG", "Ast", "xAG",
    "Sh/90", "SoT/90",
    "PrgC", "PrgP", "PrgR",
    "Cmp%", "KP", "xA",
    "TklW", "Int", "Tkl+Int", "Clr",
    "Succ%", "Carries", "Touches"
]

df = df[features]

df.to_csv("clean_2425_top2.csv", index=False)

print(df.head())
print(df.shape)
