import pandas as pd
import sqlite3

feat_full = pd.read_csv("data/processed/feature_dataset.csv")
test_df = pd.read_csv("data_T5/transfers_2026_2027_test_set.csv")

print("Full feature dataset unique teams:", feat_full["team"].nunique())
print("Teams per league in feature dataset:")
print(feat_full.groupby("league")["team"].nunique())

# Check moving_from and moving_to in test_df
print("\nTest set moving_from:", test_df.groupby("source_league")["moving_from"].nunique())
print("Test set moving_to:", test_df.groupby("target_league")["moving_to"].nunique())
