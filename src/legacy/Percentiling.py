import pandas as pd

# Load merged dataset
df = pd.read_csv("combined_leagues.csv")

print("Original shape:", df.shape)

# Identify feature columns
# Skip: Player, Team, Minutes, league
features = df.columns[3:-1]

print("Features being converted to percentiles:")
print(features)

# Compute percentiles within each league
for feature in features:
    df[feature + "_percentile"] = (
        df.groupby("league")[feature]
          .rank(pct=True)
    )

print("New shape:", df.shape)

df.to_csv("combined_with_percentiles.csv", index=False)
