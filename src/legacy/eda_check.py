import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("combined_with_percentiles.csv")

# Compare average percentile values per league
percentile_cols = [col for col in df.columns if "percentile" in col]

league_means = df.groupby("league")[percentile_cols].mean()

print(league_means)
