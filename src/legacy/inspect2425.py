import pandas as pd

bund_2425 = pd.read_csv("Bundesliga_Stats_24-25.csv")
pl_2425 = pd.read_csv("PL_Stats_24-25.csv")

print("Bundesliga 24/25 columns:")
print(bund_2425.columns)

print("\nPL 24/25 columns:")
print(pl_2425.columns)

print("\nBundesliga sample:")
print(bund_2425.head())
