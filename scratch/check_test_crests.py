import pandas as pd
import json
import re

test_df = pd.read_csv("data_T5/transfers_2026_2027_test_set.csv")

# Read teamCrestMap.js
with open("frontend/src/data/teamCrestMap.js", "r", encoding="utf-8") as f:
    crest_content = f.read()

# Extract keys from TEAM_CREST_MAP
keys = re.findall(r"'([^']+)':\s*\{\s*id:", crest_content)
crest_keys = set(k.lower() for k in keys)

all_moving_from = set(test_df['moving_from'].dropna().unique())
all_moving_to = set(test_df['moving_to'].dropna().unique())
all_teams = all_moving_from | all_moving_to

print(f"Total unique clubs in 2026/2027 test set: {len(all_teams)}")
missing_in_crests = [t for t in sorted(all_teams) if t.lower() not in crest_keys]
print(f"Missing from teamCrestMap.js: {len(missing_in_crests)}")
print(missing_in_crests)
